"""Main-only OIDC GET verification of compiled fixed contracts; never deploys."""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ama.cloud import ARC_API, MONITOR_API, contract
from infrastructure.preview import SCHEMA, compare, model
from scripts.azure_guard import az_json, canonical_uuid, context
from scripts.prepare_portfolio import NoRedirect
from scripts.validate_detection import require

API = "2025-09-01"
UNQUERIED = frozenset({"sentinel", "diagnostic-export"})
COMPILER_EVIDENCE = {
    "evidence": "actual-local-bicep-compile-contract-check", "template_count": 4,
    "writable_ama_resources": 3, "disabled_rule_definitions": 12, "foundation_writes": 0,
    "azure_requests": 0, "deployment_executed": False, "compiler": "Azure/bicep",
    "compiler_version": "0.48.1", "compiler_sha256_verified": True, "parameter_files": 1,
}


def subscription_from(workspace):
    require(isinstance(workspace, str), "Existing fixed workspace required")
    match = re.fullmatch(r"/subscriptions/([a-f0-9-]{36})/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw", workspace)
    require(match is not None, "Unexpected infrastructure workspace; no scope fallback")
    return canonical_uuid(match[1])


def paths(workspace):
    subscription_from(workspace)
    spec = contract(workspace)
    return {
        "workspace": workspace + "?api-version=2025-02-01",
        "rules": workspace + "/providers/Microsoft.SecurityInsights/alertRules?api-version=" + API,
        "machine": spec["machine_id"] + "?api-version=" + ARC_API,
        "dcr": spec["dcr_id"] + "?api-version=" + MONITOR_API,
        "extension": spec["extension_id"] + "?api-version=" + ARC_API,
        "association": spec["association_id"] + "?api-version=" + MONITOR_API,
    }


class ReadOnlyClient:
    """Exact six GET routes, bounded body, no redirect, raw error suppression."""
    def __init__(self, workspace):
        self.allowed = frozenset(paths(workspace).values())
        self.token = az_json("account", "get-access-token", "--resource", "https://management.azure.com/")["accessToken"]

    def request(self, method, path, body=None):
        require(method == "GET" and body is None, "Infrastructure verifier permits GET only")
        require(path in self.allowed, "Unapproved infrastructure GET route")
        request = urllib.request.Request("https://management.azure.com" + path, method="GET",
                    headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=45) as response:
                raw = response.read(2_097_153)
                require(len(raw) <= 2_097_152, "Infrastructure response exceeds finite allowance")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            code = "AzureHTTPError"
            try:
                value = json.loads(exc.read(65536)).get("error", {}).get("code", "")
                if isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,80}", value):
                    code = value
            except (ValueError, AttributeError, TypeError):
                pass
            finally:
                exc.close()
            raise ValueError(f"Infrastructure GET rejected (HTTP {exc.code}, {code}); no permission fallback") from None


def compiler_evidence(value):
    require(isinstance(value, dict) and json.dumps(value, sort_keys=True) == json.dumps(COMPILER_EVIDENCE, sort_keys=True),
            "Actual locked compiler/contract validation must complete before Azure authentication")
    return dict(value)


def verify(client, workspace, legacy_rule_uuid, compiled):
    """Only sanitized field paths/counts leave this function; nothing is written."""
    compiler_evidence(compiled)
    subscription = subscription_from(workspace)
    legacy_rule_uuid = canonical_uuid(legacy_rule_uuid)
    expected = model(subscription, legacy_rule_uuid)
    routes = paths(workspace)
    results = {name: client.request("GET", path) for name, path in routes.items()}
    metadata = results["workspace"]
    require(isinstance(metadata, dict), "Workspace GET did not return metadata")
    canonical_uuid(metadata.get("properties", {}).get("customerId", "").lower())
    inventory = results["rules"]
    require(isinstance(inventory, dict) and isinstance(inventory.get("value"), list) and
            not inventory.get("nextLink") and len(inventory["value"]) <= 1000,
            "Complete bounded analytics inventory required")
    require(all(isinstance(r, dict) for r in inventory["value"]), "Invalid analytics inventory")
    rows = []

    def add(target, current):
        require(isinstance(current, dict), "Exact infrastructure GET returned no resource")
        rows.append({"target": target, "id": current.get("id", ""),
                     "type": current.get("type", ""), "body": current})

    add("workspace", metadata)
    machine = results["machine"]
    require(isinstance(machine, dict), "Owned machine metadata required")
    status = machine.get("properties", {}).get("status")
    require(status in {"Connected", "Disconnected"} and machine.get("location") == "westeurope" and
            machine.get("properties", {}).get("osType", "").lower() == "linux" and
            machine.get("identity", {}).get("type") == "SystemAssigned", "Unexpected owned-machine configuration")
    add("machine", machine)
    for target in ("dcr", "extension", "association"):
        add(target, results[target])
    for target, resource in expected.items():
        if not target.startswith("AZ-DET-"):
            continue
        display = resource["body"]["properties"]["displayName"]
        identifier = resource["id"].rsplit("/", 1)[1]
        matches = [r for r in inventory["value"] if
                   r.get("id", "").lower() == resource["id"].lower() or
                   r.get("name", "").lower() == identifier or
                   r.get("properties", {}).get("displayName", "").strip().casefold() == display.casefold()]
        require(len(matches) <= 1, "Duplicate/ambiguous managed analytics definition")
        if matches:
            props = matches[0].get("properties", {})
            require(not props.get("alertRuleTemplateName") and not props.get("templateVersion"),
                    "Managed analytics ownership conflicts with fixed source")
            add(target, matches[0])
    comparison = compare({"schema": SCHEMA, "evidence": "actual-azure-rest-control-plane", "resources": rows},
                         subscription, legacy_rule_uuid)
    # Omission from a deliberately partial collection means unobserved, not
    # demonstrated absence. Never fetch these two without an existing grant.
    for row in comparison["resources"]:
        if row["target"] in UNQUERIED:
            row["state"] = "Unknown"
            row["reason"] = "not queried; existing verifier permissions exclude this resource"
    counts = {state: sum(r["state"] == state for r in comparison["resources"])
              for state in ("Matching", "Drift", "Missing", "Unknown")}
    return {
        "evidence": "actual-azure-rest-compiled-contract-comparison", "auth_mode": "github-oidc",
        "verified_utc": datetime.now(timezone.utc).isoformat(), "compiler": compiler_evidence(compiled),
        "model_target_count": len(expected), "queried_target_count": len(expected) - len(UNQUERIED),
        "counts": counts, "resources": comparison["resources"], "azure_requests": len(routes),
        "methods": ["GET"], "analytics_inventory_count": len(inventory["value"]),
        "owned_machine_connectivity": status, "managed_rules_disabled": sum(
            r["target"].startswith("AZ-DET-") and r["body"]["properties"].get("enabled") is False for r in rows),
        "compiled_writable_contracts": 15, "reference_metadata_contracts": 2,
        "compiled_to_live_contracts_match": counts == {"Matching": 17, "Drift": 0, "Missing": 0, "Unknown": 2},
        "deployment_executed": False, "arm_what_if_executed": False, "resource_writes": 0,
        "role_changes": 0, "log_queries": 0, "messages_sent": 0, "telemetry_ingestion_verified": False,
        "limitations": ["Actual GET agreement is separate from full ARM deployment/what-if.",
                        "Sentinel onboarding and subscription diagnostic export were not queried.",
                        "Disconnected Arc metadata is allowed; no guest start or freshness assertion.",
                        "Unmanaged inventory entries are counted but not modified or claimed as compiled targets."],
    }


def _unique(items):
    result = {}
    for key, value in items:
        require(key not in result, "Duplicate compiler evidence key")
        result[key] = value
    return result


def load_compiler_evidence():
    path = Path(os.environ.get("SENTINELOPS_COMPILE_REPORT", ""))
    require(path.is_file() and path.stat().st_size <= 16_384, "Bounded compiler evidence file required")
    return compiler_evidence(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique))


def main():
    compiled = load_compiler_evidence()  # Failure must precede Azure authentication.
    workspace = context("verify-infrastructure.yml")
    identifier = canonical_uuid(os.environ.get("SENTINEL_RULE_ID", ""))
    report = verify(ReadOnlyClient(workspace), workspace, identifier, compiled)
    print("INFRASTRUCTURE_EVIDENCE=" + json.dumps(report, separators=(",", ":")))
    require(report["compiled_to_live_contracts_match"], "Observed compiled/live configuration drift or missing target")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, AttributeError, RecursionError):
        raise SystemExit("Infrastructure verification stopped; inspect sanitized state/field paths. No raw response, resource mutation, permission fallback or subscription switch.") from None
