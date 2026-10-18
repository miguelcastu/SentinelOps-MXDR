"""Manual OIDC collector: existing workspace/rule GETs only, no Logs API or mutation."""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from platform_health.engine import blank_observation, policies
from scripts.azure_guard import API_VERSION, az_json, canonical_uuid, context
from scripts.check_drift import changed_properties
from scripts.validate_detection import DETECTIONS, validate_rule

WORKFLOWS = ("validate.yml", "deploy-sentinel.yml", "deploy-additional-detection.yml")
REPO = "miguelcastu/SentinelOps-MXDR"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github_runs(token):
    # One fixed request; do not follow pagination or expose author/identity fields.
    request = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/runs?branch=main&per_page=30",
        headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "SentinelOps-health"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
            return json.loads(response.read(1_048_577))
    except (ValueError, OSError, urllib.error.URLError):
        return {}


def deployment_checks(payload):
    runs = payload.get("workflow_runs", []) if isinstance(payload, dict) else []
    runs = runs if isinstance(runs, list) else []
    checks = []
    for filename in WORKFLOWS:
        matches = [r for r in runs if isinstance(r, dict) and isinstance(r.get("path"), str) and
                   r["path"].split("@", 1)[0] == ".github/workflows/" + filename and
                   r.get("head_branch") == "main" and r.get("event") != "pull_request"]
        # API ordering is not used as an implicit contract; reject ambiguous identifiers.
        valid = [r for r in matches if type(r.get("run_number")) is int]
        latest = max(valid, key=lambda r: r["run_number"]) if valid else {}
        state, reason = "Unknown", "deployment_unavailable"
        if latest.get("status") == "completed":
            if latest.get("conclusion") == "success":
                state, reason = "Healthy", "deployment_success"
            elif latest.get("conclusion") in ("failure", "timed_out", "action_required", "startup_failure"):
                state, reason = "Misconfigured", "deployment_failed"
        checks.append({"id": filename, "state": state, "reason": reason})
    return checks


def collect():
    # Context failures stop before requests; never use a personal account fallback.
    workspace_id = context("check-health.yml")
    first_id = canonical_uuid(os.environ.get("SENTINEL_RULE_ID", ""))
    config, inventory = policies()
    now = datetime.now(timezone.utc)
    stamp = now.isoformat().replace("+00:00", "Z")
    start = (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    snapshot = {"schema_version": "1.0", "evidence": "azure-control-plane", "observed_at": stamp,
                "sources": [blank_observation(s["id"], stamp, start) for s in inventory], "checks": [],
                "rules": {"expected": 2, "present": None, "matching": None, "active": None, "intentionally_disabled": None}}
    for source in snapshot["sources"]:
        source["query_status"] = "not_authorized" if source["source_id"] == "azure-activity" else "not_collected"
    checks = snapshot["checks"]
    try:
        workspace = az_json("rest", "--method", "get", "--url",
                            f"https://management.azure.com{workspace_id}?api-version=2025-02-01")
        if not isinstance(workspace, dict) or not isinstance(workspace.get("properties"), dict):
            raise ValueError("Invalid workspace metadata")
        props, target = workspace.get("properties", {}), config["expected_workspace"]
        matches = (workspace.get("id", "").lower() == workspace_id.lower() and workspace.get("location") == target["region"] and
                   props.get("retentionInDays") == target["retention_days"] and
                   props.get("sku", {}).get("name", "").lower() == target["pricing_tier"].lower() and
                   props.get("workspaceCapping", {}).get("dailyQuotaGb") == target["daily_cap_gb"])
        checks.append({"id": "workspace", "state": "Healthy" if matches else "Misconfigured",
                       "reason": "configuration_matches" if matches else "configuration_drift"})
        if workspace.get("id", "").lower() != workspace_id.lower():
            # A mismatched response cannot authorize subsequent requests.
            return snapshot
    except (ValueError, OSError):
        checks.append({"id": "workspace", "state": "Unknown", "reason": "metadata_unavailable"})
    try:
        listing = az_json("rest", "--method", "get", "--url",
                          f"https://management.azure.com{workspace_id}/providers/Microsoft.SecurityInsights/alertRules?api-version={API_VERSION}")
        if (not isinstance(listing, dict) or listing.get("nextLink") or not isinstance(listing.get("value"), list) or
                len(listing["value"]) > 1000 or any(not isinstance(r, dict) for r in listing["value"])):
            raise ValueError("Incomplete inventory")
        present = matching = active = intentionally_disabled = 0
        for key, rule_id in (("AZ-DET-001", first_id), ("AZ-DET-002", DETECTIONS["AZ-DET-002"]["resource_uuid"])):
            desired = validate_rule(detection=key)
            expected_id = workspace_id + "/providers/Microsoft.SecurityInsights/alertRules/" + rule_id
            candidates = [r for r in listing["value"] if r.get("name", "").lower() == rule_id or
                          r.get("properties", {}).get("displayName", "").casefold() == DETECTIONS[key]["name"].casefold()]
            current = candidates[0] if len(candidates) == 1 else {}
            valid = (len(candidates) == 1 and current.get("id", "").lower() == expected_id.lower() and
                     current.get("kind") == "Scheduled" and not changed_properties(current, desired))
            present += bool(current)
            matching += valid
            active += current.get("properties", {}).get("enabled") is True
            intentionally_disabled += valid and current.get("properties", {}).get("enabled") is False
            checks.append({"id": key, "state": "Healthy" if valid else "Misconfigured",
                           "reason": "configuration_matches" if valid else "configuration_drift"})
        snapshot["rules"] = dict(expected=2, present=present, matching=matching, active=active, intentionally_disabled=intentionally_disabled)
    except (ValueError, OSError):
        checks.extend({"id": key, "state": "Unknown", "reason": "metadata_unavailable"} for key in DETECTIONS)
    checks.extend([{"id": "activity-export", "state": "Unknown", "reason": "export_not_authorized"},
                   {"id": "rule-runtime", "state": "Unknown", "reason": "runtime_not_collected"}])
    token = os.environ.get("GH_TOKEN", "")
    checks.extend(deployment_checks(github_runs(token) if token else {}))
    return snapshot
