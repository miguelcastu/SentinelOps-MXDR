"""Offline fixed-resource comparison and Bicep compilation; never authenticates.

This is a review artifact generator, not ARM what-if and not a deployer. It
does not suggest creating missing resources or deleting unrecognized resources.
Only field paths/counts appear in its public report, never current values/IDs.
"""
import argparse
import copy
import hashlib
import json
import os
import platform
import re
import subprocess
from pathlib import Path

from ama.cloud import contract as ama_contract, matches as ama_matches
from portfolio.catalog import SPECS, resource_uuid, validate as validate_portfolio
from scripts.validate_detection import DETECTIONS, validate_rule

ROOT = Path(__file__).resolve().parents[1]
SUBSCRIPTION = "11111111-1111-4111-8111-111111111111"  # Fictional offline target.
LEGACY_RULE = "22222222-2222-4222-8222-222222222222"  # Never a cloud target.
SCHEMA = "sentinelops-infrastructure-snapshot-1"
BICEP = ROOT / "infrastructure/bicep"
WRITE_TARGETS = frozenset({"dcr", "extension", "association", *DETECTIONS, *SPECS})


def require(condition, message="Invalid fixed infrastructure contract"):
    if not condition:
        raise ValueError(message)


def uuid_string(value):
    require(isinstance(value, str) and re.fullmatch(
        r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", value),
        "Canonical target UUID required")
    return value


def model(subscription_id=SUBSCRIPTION, legacy_rule_uuid=LEGACY_RULE):
    """Render only fixed names/bodies; arguments pin pre-existing private IDs."""
    validate_portfolio()
    for key in DETECTIONS:
        validate_rule(detection=key)
    subscription_id = uuid_string(subscription_id)
    legacy_rule_uuid = uuid_string(legacy_rule_uuid)
    group = f"/subscriptions/{subscription_id}/resourceGroups/rg-sentinelops-mxdr"
    workspace = group + "/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
    values = ama_contract(workspace)
    resources = {}

    def add(target, rid, kind, body, read_only=False):
        resources[target] = {"id": rid, "type": kind, "body": body, "read_only": read_only}

    add("workspace", workspace, "Microsoft.OperationalInsights/workspaces", {
        "location": "westeurope", "properties": {
            "sku": {"name": "pergb2018"}, "retentionInDays": 30,
            "workspaceCapping": {"dailyQuotaGb": 0.1}}}, True)
    add("sentinel", workspace + "/providers/Microsoft.SecurityInsights/onboardingStates/default",
        "Microsoft.SecurityInsights/onboardingStates", {}, True)
    add("diagnostic-export", f"/subscriptions/{subscription_id}/providers/Microsoft.Insights/diagnosticSettings/subscriptionToLa",
        "Microsoft.Insights/diagnosticSettings", {"properties": {"workspaceId": workspace}}, True)
    add("machine", values["machine_id"], "Microsoft.HybridCompute/machines", {}, True)
    for key, kind in (("dcr", "Microsoft.Insights/dataCollectionRules"),
                      ("extension", "Microsoft.HybridCompute/machines/extensions"),
                      ("association", "Microsoft.Insights/dataCollectionRuleAssociations")):
        add(key, values[key + "_id"], kind, values[key])
    for key in (*DETECTIONS, *SPECS):
        body = json.loads((ROOT / f"detections/azure/{key}.json").read_text(encoding="utf-8"))
        require(body.get("kind") == "Scheduled" and body["properties"]["enabled"] is False,
                "Enabled rules cannot enter infrastructure model")
        rid = (legacy_rule_uuid if key == "AZ-DET-001" else
               DETECTIONS[key]["resource_uuid"] if key == "AZ-DET-002" else resource_uuid(key))
        add(key, workspace + "/providers/Microsoft.SecurityInsights/alertRules/" + rid,
            "Microsoft.SecurityInsights/alertRules", body)
    return resources


def _delta(expected, actual, prefix=""):
    """Managed subset comparison: report paths only, not identities/values."""
    changes = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [prefix or "body"]
        for key in expected:
            path = prefix + "." + key if prefix else key
            if key not in actual:
                changes.append(path)
            else:
                changes.extend(_delta(expected[key], actual[key], path))
        return changes
    if isinstance(expected, str) and isinstance(actual, str) and (
            expected.startswith('/subscriptions/') or prefix.endswith('sku.name')):
        return [] if expected.lower() == actual.lower() else [prefix or 'body']
    if expected != actual or type(expected) is not type(actual):
        return [prefix or "body"]
    return []


def snapshot(resources=None):
    """A labeled synthetic fixture; never describe it as current Azure state."""
    resources = model() if resources is None else resources
    return {"schema": SCHEMA, "evidence": "synthetic", "resources": [
        {"target": target, **{k: copy.deepcopy(v[k]) for k in ("id", "type", "body")}}
        for target, v in resources.items()]}


def compare(observed=None, subscription_id=SUBSCRIPTION, legacy_rule_uuid=LEGACY_RULE):
    expected = model(subscription_id, legacy_rule_uuid)
    evidence = "not-supplied"
    observed_by_target = {}
    if observed is not None:
        require(isinstance(observed, dict) and set(observed) == {"schema", "evidence", "resources"})
        require(observed["schema"] == SCHEMA and observed["evidence"] in {
            "synthetic", "external-snapshot-unverified", "actual-azure-rest-control-plane"})
        evidence = observed["evidence"]
        require(isinstance(observed["resources"], list) and len(observed["resources"]) <= 64)
        for entry in observed["resources"]:
            require(isinstance(entry, dict) and set(entry) == {"target", "id", "type", "body"})
            target = entry["target"]
            require(isinstance(target, str) and target in expected,
                    "Unrecognized resource; no deletion or adoption is allowed")
            require(target not in observed_by_target, "Duplicate/conflicting resource observation")
            require(isinstance(entry["id"], str) and isinstance(entry["type"], str) and isinstance(entry["body"], dict))
            require(entry["id"].lower() == expected[target]["id"].lower() and
                    entry["type"].lower() == expected[target]["type"].lower(),
                    "Resource target/type mismatch; refusing scope expansion")
            observed_by_target[target] = entry
    rows = []
    customer_id = observed_by_target.get("workspace", {}).get("body", {}).get("properties", {}).get("customerId")
    for target, desired in expected.items():
        entry = observed_by_target.get(target)
        changes = []
        state = "Unknown" if observed is None else "Missing"
        if entry is not None:
            if target in {"dcr", "extension", "association"}:
                body = entry["body"] | {"id": entry["id"]}
                same = ama_matches(body, desired["body"], desired["id"], target, customer_id)
                changes = [] if same else _delta(desired["body"], entry["body"]) or ["unreviewed-properties"]
            else:
                changes = _delta(desired["body"], entry["body"])
            state = "Drift" if changes else "Matching"
        rows.append({"target": target, "resource_type": desired["type"],
                     "state": state, "changed_paths": changes,
                     "write_scope": "read-only" if desired["read_only"] else "approved fixed REST workflow only",
                     "proposed_operation": "none"})
    return {"evidence": "offline-contract-comparison", "input_evidence": evidence,
            "input_provenance_verified": False, "azure_requests": 0,
            "arm_what_if_executed": False, "deployment_executed": False,
            "resource_count": len(rows), "resources": rows,
            "counts": {s: sum(r["state"] == s for r in rows) for s in ("Matching", "Drift", "Missing", "Unknown")},
            "safe_to_deploy": False,
            "limitations": ["Local comparison does not authenticate or refresh Azure state.",
                            "Missing resources are not approval to create them.",
                            "Foundation controls are represented read-only; no deployment permission is inferred."]}


def guard_changes(changes, subscription_id=SUBSCRIPTION, legacy_rule_uuid=LEGACY_RULE):
    """Review a bounded external ARM-style change set; never execute it.

    Only NoChange and exact-contract fixed-target Modify are reviewable.
    Complete mode, deletions, creates and readonly-foundation modifications fail.
    This helper does not establish that Azure produced the input.
    """
    expected = model(subscription_id, legacy_rule_uuid)
    require(isinstance(changes, list) and len(changes) <= len(expected))
    seen = set()
    for change in changes:
        require(isinstance(change, dict) and set(change) == {"target", "change_type", "after"})
        target = change["target"]
        require(target in expected and target not in seen, "Unknown/duplicate change target")
        seen.add(target)
        require(change["change_type"] in {"NoChange", "Modify"}, "Create/delete/replace/unsupported changes are prohibited")
        if change["change_type"] == "Modify":
            require(target in WRITE_TARGETS and not expected[target]["read_only"],
                    "Pricing/retention/cap/export/foundation changes are prohibited")
            require(change["after"] == expected[target]["body"], "Change body differs from the fixed reviewed contract")
        else:
            require(change["after"] is None, "NoChange must not contain a body")
    return {"evidence": "offline-change-set-review", "reviewable_changes": len(changes),
            "deployment_executed": False, "safe_to_deploy": False}


def _resolve(value, variables, expressions):
    if isinstance(value, dict):
        return {k: _resolve(v, variables, expressions) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, variables, expressions) for v in value]
    if isinstance(value, str) and value.startswith("["):
        if value in expressions:
            return expressions[value]
        match = re.fullmatch(r"\[variables\('([^']+)'\)\]", value)
        require(match is not None and match[1] in variables, "Unknown compiled expression")
        return _resolve(variables[match[1]], variables, expressions)
    return value


def validate_compiled(templates):
    """Validate exact compiled resources using a deliberately finite resolver."""
    require(set(templates) == {"main", "ama", "disabled-rules", "diagnostic-export"})
    for name in ("main", "diagnostic-export"):
        require(templates[name].get("resources", []) == [], "Read-only architecture gained writable resources")
    fixed = model()
    expressions = {"[parameters('diagnosticRuleId')]": LEGACY_RULE,
                   "[format('{0}/{1}', 'lab-sentinelops-linux-01', 'AzureMonitorLinuxAgent')]": "lab-sentinelops-linux-01/AzureMonitorLinuxAgent"}
    for target in ("workspace", "machine", "dcr"):
        value = fixed[target]
        name = value["id"].rsplit("/", 1)[1]
        expressions[f"[resourceId('{value['type']}', '{name}')]"] = value["id"]
    template = templates["ama"]
    resources = _resolve(template["resources"], template.get("variables", {}), expressions)
    require(len(resources) == 3)
    for target, resource in zip(("dcr", "extension", "association"), resources):
        resource = copy.deepcopy(resource)
        require(resource.pop("type") == fixed[target]["type"])
        require(resource.pop("apiVersion") == ("2025-01-13" if target == "extension" else "2024-03-11"))
        expected_name = fixed[target]["id"].rsplit("/", 1)[1]
        require(resource.pop("name") == ("lab-sentinelops-linux-01/" + expected_name if target == "extension" else expected_name))
        if target == "association":
            require(resource.pop("scope") == fixed["machine"]["id"])
            require(resource.pop("dependsOn") == [fixed["dcr"]["id"]])
        require(resource == fixed[target]["body"], "Compiled AMA resource differs from the reviewed contract")
    template = templates["disabled-rules"]
    require(len(template["resources"]) == 1)
    loop = template["resources"][0]
    require(loop == {"copy": {"name": "analytics", "count": "[length(variables('rules'))]"},
            "type": "Microsoft.SecurityInsights/alertRules", "apiVersion": "2025-09-01",
            "scope": "[resourceId('Microsoft.OperationalInsights/workspaces', 'law-sentinelops-mxdr-euw')]",
            "name": "[variables('rules')[copyIndex()].name]", "kind": "Scheduled",
            "properties": "[variables('rules')[copyIndex()].body.properties]"}, "Unreviewed analytics template structure")
    rules = _resolve(template["variables"]["rules"], template["variables"], expressions)
    require(len(rules) == 12 and len({r["name"] for r in rules}) == 12)
    for key, rendered in zip((*DETECTIONS, *SPECS), rules):
        require(rendered == {"name": fixed[key]["id"].rsplit("/", 1)[1], "body": fixed[key]["body"]},
                "Compiled analytics target/body differs from the reviewed disabled catalog")
    return {"evidence": "actual-local-bicep-compile-contract-check", "template_count": 4,
            "writable_ama_resources": 3, "disabled_rule_definitions": 12,
            "foundation_writes": 0, "azure_requests": 0, "deployment_executed": False}


def compile_templates(executable, output):
    lock = json.loads((BICEP / "tools.lock.json").read_text(encoding="utf-8"))
    executable = Path(executable).resolve()
    require(executable.is_file(), "Pinned Bicep compiler is missing")
    require(platform.machine().lower() in {"amd64", "x86_64"}, "Only locked x64 compilers are supported")
    platform_key = "windows-x64" if platform.system() == "Windows" else "linux-x64"
    require(hashlib.sha256(executable.read_bytes()).hexdigest() == lock[platform_key]["sha256"],
            "Bicep compiler SHA-256 differs from reviewed official release")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    templates = {}
    for name in ("main", "ama", "disabled-rules", "diagnostic-export"):
        destination = output / (name + ".json")
        result = subprocess.run([str(executable), "build", str(BICEP / (name + ".bicep")),
                                 "--no-restore", "--outfile", str(destination.resolve())],
                                capture_output=True, timeout=60)
        require(result.returncode == 0 and not result.stderr.strip(), "Bicep compiler/linter failed; inspect private local diagnostics")
        templates[name] = json.loads(destination.read_text(encoding="utf-8"))
    parameter_file = output / 'disabled-rules.parameters.json'
    result = subprocess.run([str(executable), 'build-params', str(BICEP / 'disabled-rules.bicepparam'),
                             '--no-restore', '--outfile', str(parameter_file.resolve())],
                            capture_output=True, timeout=60,
                            env=dict(os.environ, SENTINELOPS_EXISTING_RULE_UUID=LEGACY_RULE))
    require(result.returncode == 0 and not result.stderr.strip(), 'Bicep parameter compilation failed')
    parameters = json.loads(parameter_file.read_text(encoding='utf-8'))
    require(parameters.get('parameters') == {'diagnosticRuleId': {'value': LEGACY_RULE}},
            'Compiled parameter file differs from the fictional offline pin')
    return validate_compiled(templates) | {"compiler": "Azure/bicep", "compiler_version": lock["version"],
                                          "compiler_sha256_verified": True, "parameter_files": 1}


def _unique_object(items):
    result = {}
    for key, value in items:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed", type=Path, help="Bounded external/synthetic snapshot, never queried automatically")
    parser.add_argument("--private-pin", type=Path, help="Existing subscription_id/legacy_rule_uuid JSON pin; never printed")
    parser.add_argument("--bicep", type=Path, help="Already-downloaded hash-pinned compiler; no automatic download")
    parser.add_argument("--output", type=Path, default=Path(".local/infrastructure"))
    args = parser.parse_args()
    pin = {}
    if args.private_pin:
        require(args.private_pin.stat().st_size <= 4096)
        pin = json.loads(args.private_pin.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        require(set(pin) == {"subscription_id", "legacy_rule_uuid"})
    data = None
    if args.observed:
        require(args.observed.stat().st_size <= 4_194_304, "Snapshot exceeds finite byte allowance")
        data = json.loads(args.observed.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    report = compare(data, **pin)
    if args.bicep:
        report["bicep"] = compile_templates(args.bicep, args.output)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "preview.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 1 if report["counts"]["Drift"] or report["counts"]["Missing"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, TypeError, KeyError, RecursionError, subprocess.SubprocessError):
        raise SystemExit("Infrastructure preview stopped: invalid bounded contract/compiler/snapshot; no Azure operation was attempted") from None
