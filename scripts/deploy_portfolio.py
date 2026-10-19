"""Only the ten reviewed, disabled portfolio rules, through main GitHub OIDC."""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from portfolio.catalog import SPECS, definition, resource_uuid, validate
from scripts.azure_guard import az_json, context, rule_url
from scripts.validate_detection import require


def complete_inventory(workspace_id):
    result = az_json("rest", "--method", "get", "--url",
                     f"https://management.azure.com{workspace_id}/providers/Microsoft.SecurityInsights/alertRules?api-version=2025-09-01")
    require(isinstance(result, dict) and isinstance(result.get("value"), list) and not result.get("nextLink"), "Complete inventory required")
    require(len(result["value"]) <= 1000 and all(isinstance(x, dict) for x in result["value"]), "Invalid inventory")
    return result["value"]


def target_current(inventory, workspace_id, key):
    desired = definition(key)
    name, target = desired["properties"]["displayName"], resource_uuid(key)
    matches = [r for r in inventory if r.get("name", "").lower() == target or
               r.get("properties", {}).get("displayName", "").strip().casefold() == name.casefold()]
    require(len(matches) <= 1, f"{key}: ambiguous target")
    if not matches:
        return None
    current = matches[0]
    verify(current, workspace_id, key)
    require(isinstance(current.get("etag"), str) and current["etag"], f"{key}: etag required")
    return current


def verify(current, workspace_id, key):
    expected_id = workspace_id + "/providers/Microsoft.SecurityInsights/alertRules/" + resource_uuid(key)
    require(current.get("id", "").lower() == expected_id.lower() and current.get("name", "").lower() == resource_uuid(key), f"{key}: resource identity mismatch")
    require(current.get("type", "").lower() == "microsoft.securityinsights/alertrules" and current.get("kind") == "Scheduled", f"{key}: resource type/kind mismatch")
    props = current.get("properties", {})
    require(props.get("enabled") is False, f"{key}: enabled rule must not be overwritten")
    require(not props.get("alertRuleTemplateName") and not props.get("templateVersion"), f"{key}: template-managed target")
    require(all(props.get(k) == v for k, v in definition(key)["properties"].items()), f"{key}: unexpected cloud properties; review ownership/drift")


def unaffected(inventory):
    targets = {resource_uuid(k) for k in SPECS}
    return {r["id"].lower(): {"kind": r.get("kind"), "properties": r.get("properties")} for r in inventory
            if r.get("name", "").lower() not in targets}


def deploy():
    digest = validate()
    require(os.environ.get("SENTINEL_PORTFOLIO_APPROVED_SHA256") == digest, "Portfolio fingerprint approval required")
    require(os.environ.get("SENTINEL_EXCLUSIVE_RULE_OWNER") == "true", "Exclusive ownership approval required")
    workspace_id = context("deploy-portfolio.yml")
    workspace = az_json("rest", "--method", "get", "--url", f"https://management.azure.com{workspace_id}?api-version=2025-02-01")
    require(workspace.get("id", "").lower() == workspace_id.lower() and workspace.get("location") == "westeurope", "Workspace mismatch")
    before = complete_inventory(workspace_id)
    # Validate the entire batch before the first write. Existing drift/enabled targets stop it.
    plan = [(key, target_current(before, workspace_id, key)) for key in SPECS]
    preserved = unaffected(before)
    results = []
    for key, current in plan:
        if current:
            # Idempotent matching definitions need no PUT.
            verify(az_json("rest", "--method", "get", "--url", rule_url(workspace_id, resource_uuid(key))), workspace_id, key)
            action = "already-matching"
        else:
            with tempfile.TemporaryDirectory(prefix="sentinelops-portfolio-") as directory:
                path = Path(directory) / "disabled-rule.json"
                path.write_text(json.dumps(definition(key)), encoding="utf-8")
                response = az_json("rest", "--method", "put", "--url", rule_url(workspace_id, resource_uuid(key)),
                                   "--headers", "If-None-Match=*", "--body", "@" + str(path))
            verify(response, workspace_id, key)
            verify(az_json("rest", "--method", "get", "--url", rule_url(workspace_id, resource_uuid(key))), workspace_id, key)
            action = "created-disabled"
        results.append({"detection": key, "uuid": resource_uuid(key), "enabled": False, "action": action, "persisted_properties_match": True})
        print(f"VERIFIED: {key}: {action}; Azure REST persisted properties match")
    after = complete_inventory(workspace_id)
    require(unaffected(after) == preserved, "Non-portfolio rules changed during deployment; investigate")
    require(all(target_current(after, workspace_id, key) is not None for key in SPECS), "Final inventory incomplete")
    report = {"evidence": "azure-rest-control-plane", "observed_at": datetime.now(timezone.utc).isoformat(),
              "portfolio_sha256": digest, "rules": results, "existing_rules_unchanged": True,
              "log_queries_executed": 0, "incidents_created": 0, "new_sources": 0, "kusto_executed": False}
    print("PORTFOLIO_EVIDENCE=" + json.dumps(report, separators=(",", ":")))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write("Ten portfolio rules verified disabled by Azure REST; existing rules unchanged. No KQL, ingestion or incident creation.\n")


if __name__ == "__main__":
    try:
        deploy()
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Portfolio stopped: {exc}. Earlier verified creations may persist disabled; no automatic deletion or retry.") from None
