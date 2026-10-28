"""Manual main-only OIDC provisioning of exactly one approved AMA configuration."""
import json
import os
import time
from datetime import datetime, timezone

from ama.cloud import ARC_API, MONITOR_API, Client, contract, fingerprint, matches
from scripts.azure_guard import context
from scripts.deploy_portfolio import complete_inventory
from scripts.validate_detection import require


def inventory(client, path):
    response = client.request("GET", path)
    require(isinstance(response, dict) and isinstance(response.get("value"), list) and not response.get("nextLink"), "Complete machine inventory required")
    return response["value"]


def workspace_settings(value):
    props = value["properties"]
    return {"sku": props.get("sku"), "retention": props.get("retentionInDays"), "cap": props.get("workspaceCapping")}


def configure(client, workspace, auth_mode="github-oidc"):
    require(auth_mode in {"github-oidc", "one-time-personal-bootstrap"}, "Unapproved configuration mode")
    spec = contract(workspace)
    metadata = client.request("GET", workspace + "?api-version=2025-02-01")
    require(metadata.get("location") == "westeurope", "Existing workspace region mismatch")
    baseline_settings = workspace_settings(metadata)
    baseline_rules = complete_inventory(workspace)
    machine = client.request("GET", spec["machine_id"] + "?api-version=" + ARC_API)
    require(machine.get("id", "").lower() == spec["machine_id"].lower() and machine.get("location") == "westeurope" and machine.get("properties", {}).get("status") == "Connected", "Expected owned Arc machine must already be connected")
    require(machine.get("properties", {}).get("osType", "").lower() == "linux" and machine.get("identity", {}).get("type") == "SystemAssigned", "Expected Linux managed-identity machine required")
    extensions_path = spec["machine_id"] + "/extensions?api-version=" + ARC_API
    associations_path = spec["machine_id"] + "/providers/Microsoft.Insights/dataCollectionRuleAssociations?api-version=" + MONITOR_API
    ext = inventory(client, extensions_path)
    associations = inventory(client, associations_path)
    require(all(r.get("id", "").lower() == spec["extension_id"].lower() for r in ext) and len(ext) <= 1, "Unreviewed extension present")
    require(all(r.get("id", "").lower() == spec["association_id"].lower() for r in associations) and len(associations) <= 1, "Additional DCR association present")
    plan = [(kind, spec[kind + "_id"], spec[kind], ARC_API if kind == "extension" else MONITOR_API)
            for kind in ("dcr", "extension", "association")]
    # Preflight the whole fixed batch. Never overwrite drift or another owner.
    existing = {}
    for kind, target, desired, version in plan:
        current = client.request("GET", target + "?api-version=" + version, missing_ok=True)
        if current is not None:
            require(matches(current, desired, target, kind), "Existing AMA target conflicts with reviewed ownership/contract: " + kind)
        existing[kind] = current
    results = []
    for kind, target, desired, version in plan:
        path = target + "?api-version=" + version
        if existing[kind] is None:
            client.request("PUT", path, desired)
        verified = None
        for attempt in range(30):
            verified = client.request("GET", path, missing_ok=True)
            state = (verified or {}).get("properties", {}).get("provisioningState")
            require(state not in {"Failed", "Canceled"}, "AMA provisioning failed: " + kind)
            if verified and state in (None, "Succeeded"):
                break
            time.sleep(10)
        require(matches(verified, desired, target, kind), "AMA persisted properties do not match: " + kind)
        require(verified.get("properties", {}).get("provisioningState") in (None, "Succeeded"), "AMA provisioning is incomplete: " + kind)
        results.append({"kind": kind, "action": "created" if existing[kind] is None else "already-matching", "persisted_contract_match": True, "provisioning": verified.get("properties", {}).get("provisioningState", "not-reported")})
        print("VERIFIED AMA: " + kind + "; persisted fixed contract, no raw machine metadata")
    require(workspace_settings(client.request("GET", workspace + "?api-version=2025-02-01")) == baseline_settings, "Workspace settings changed")
    require(complete_inventory(workspace) == baseline_rules, "Analytics rule inventory changed")
    require(len(inventory(client, extensions_path)) == 1 and len(inventory(client, associations_path)) == 1, "Unexpected final machine inventory")
    report = {"evidence": "actual-azure-rest-control-plane", "auth_mode": auth_mode, "verified_utc": datetime.now(timezone.utc).isoformat(), "approved_sha256": fingerprint(), "resources": results,
              "workspace_settings_unchanged": True, "analytics_rules_unchanged": True, "queries_executed": 0, "messages_sent": 0, "ingestion_verified": False}
    return report


def deploy():
    require(os.environ.get("SENTINEL_AMA_APPROVED_SHA256") == fingerprint(), "Exact AMA approval fingerprint required")
    workspace = context("deploy-ama-pilot.yml")
    report = configure(Client(), workspace)
    print("AMA_EVIDENCE=" + json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    try:
        deploy()
    except (ValueError, OSError) as exc:
        raise SystemExit(f"AMA deployment stopped: {exc}. Earlier fixed resources may persist; no automatic deletion or sender.") from None
