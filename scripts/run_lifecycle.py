"""Manual OIDC-only lifecycle: one self-expiring test, bounded observation, cleanup."""
import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from ama.cloud import Client
from lifecycle.contract import API, RULE_UUID, TITLE, close_body, fingerprint, instant, parameters, require, rule, validate_incident
from scripts.azure_guard import context
from scripts.deploy_ama_pilot import workspace_settings
from scripts.prepare_portfolio import NoRedirect


class LifecycleClient(Client):
    def request(self, method, path, body=None, missing_ok=False):
        require(method in {"GET", "PUT"})
        headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
        # Resource upserts retain optimistic concurrency rather than disabling it.
        if method == "PUT":
            headers.update({"If-Match": body["etag"]} if body.get("etag") else {"If-None-Match": "*"})
        request = urllib.request.Request("https://management.azure.com" + path, method=method,
                    data=None if body is None else json.dumps(body).encode(), headers=headers)
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=45) as response:
                raw = response.read(2_097_153)
                require(len(raw) <= 2_097_152, "Bounded lifecycle response exceeded")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            code = "AzureHTTPError"
            try:
                candidate = json.loads(exc.read(65536)).get("error", {}).get("code", "")
                if isinstance(candidate, str) and candidate.isalnum() and len(candidate) <= 80:
                    code = candidate
            except (ValueError, AttributeError):
                pass
            if missing_ok and exc.code == 404 and code in {"ResourceNotFound", "NotFound"}:
                return None
            raise ValueError(f"Lifecycle Azure {method} rejected: HTTP {exc.code}, {code}; no wider permission fallback") from None


def listing(client, path):
    result = client.request("GET", path)
    require(isinstance(result, dict) and isinstance(result.get("value"), list) and not result.get("nextLink"), "Complete bounded lifecycle inventory required")
    return result["value"]


def other_rules(client, workspace):
    rows = listing(client, workspace + "/providers/Microsoft.SecurityInsights/alertRules?api-version=" + API)
    return {r["name"]: {"kind": r["kind"], "properties": r["properties"]} for r in rows if r["name"].lower() != RULE_UUID}


def disabled(client, target):
    current = client.request("GET", target + "?api-version=" + API, missing_ok=True)
    if current is None:
        return False
    run, started = parameters(current)
    require(current.get("id", "").lower() == target.lower())
    if current["properties"]["enabled"]:
        body = rule(run, started, False) | {"etag": current["etag"]}
        client.request("PUT", target + "?api-version=" + API, body)
    for attempt in range(6):
        final = client.request("GET", target + "?api-version=" + API)
        require(parameters(final) == (run, started) and final.get("id", "").lower() == target.lower(), "Cleanup read-back changed the fixed test contract")
        if final["properties"]["enabled"] is False:
            break
        if attempt < 5:
            time.sleep(3)
    require(final["properties"]["enabled"] is False, "Test rule cleanup not verified")
    return True


def find_incident(client, workspace, target):
    query = urllib.parse.urlencode({"api-version": API, "$filter": "properties/title eq '" + TITLE + "'", "$top": 20})
    rows = listing(client, workspace + "/providers/Microsoft.SecurityInsights/incidents?" + query)
    require(len(rows) <= 1, "Ambiguous synthetic incidents; stop without classification")
    if not rows:
        return None
    validate_incident(rows[0], target)
    from scripts.azure_guard import canonical_uuid
    identifier = canonical_uuid(rows[0].get("name", ""))
    require(rows[0].get("id", "").lower() == (workspace + "/providers/Microsoft.SecurityInsights/incidents/" + identifier).lower(), "Incident outside the exact workspace")
    current_rule = client.request("GET", target + "?api-version=" + API)
    _, started = parameters(current_rule)
    activity = rows[0]["properties"].get("firstActivityTimeUtc", "")
    try:
        delta = (datetime.fromisoformat(activity.replace("Z", "+00:00")) - instant(started)).total_seconds()
    except (ValueError, TypeError):
        raise ValueError("Synthetic incident activity time is unverified") from None
    require(-1 <= delta <= 1200, "Incident does not belong to the current synthetic test window")
    return rows[0]


def observe(client, workspace, target, sleep=time.sleep):
    for attempt in range(24):
        value = find_incident(client, workspace, target)
        if value:
            # Detailed alert reads need extra access. CI proves exact rule/time/
            # workspace linkage and the service's alert count; the operator's
            # separately recorded read-only investigation verifies alert details.
            count = value["properties"]["additionalData"]["alertsCount"]
            return {"incident_created": True, "linked_alerts": count, "incident_status": value["properties"]["status"],
                    "alert_count_source": "actual-incident-metadata", "detailed_alert_read_performed_by_ci": False,
                    "incident_reference": hashlib.sha256(value["id"].lower().encode()).hexdigest(),
                    "scheduled_rule_link_verified": True, "poll_attempts": attempt + 1,
                    "defender_portal_url_present": bool(value["properties"].get("additionalData", {}).get("providerIncidentUrl")),
                    "first_activity_utc": value["properties"].get("firstActivityTimeUtc"),
                    "last_activity_utc": value["properties"].get("lastActivityTimeUtc")}
        print(f"Lifecycle observation {attempt + 1}/24: no matching synthetic incident yet; no raw output", flush=True)
        if attempt < 23:
            sleep(30)
    raise ValueError("No scheduled-rule incident observed within the finite acceptance window")


def recovery_current(client, workspace, target):
    current = client.request("GET", target + "?api-version=" + API)
    parameters(current)
    require(current.get("id", "").lower() == target.lower() and current["properties"]["enabled"] is False, "Recovery requires the exact disabled test")
    approved = os.environ.get("SENTINEL_LIFECYCLE_RECOVERY_REFERENCE", "")
    require(len(approved) == 64 and approved == hashlib.sha256(current["properties"]["query"].encode()).hexdigest(), "Exact prior test query reference required; no automatic replay")
    require(find_incident(client, workspace, target) is None, "Existing linked incident must be investigated, not replayed")
    return current


def execute(client, workspace, mode):
    target = workspace + "/providers/Microsoft.SecurityInsights/alertRules/" + RULE_UUID
    baseline = other_rules(client, workspace)
    settings = workspace_settings(client.request("GET", workspace + "?api-version=2025-02-01"))
    require(len(baseline) == 13 and sum(r["kind"] == "Scheduled" and r["properties"].get("enabled") is False for r in baseline.values()) == 12, "Original thirteen-rule baseline required")
    report = {"evidence": "actual-azure-scheduled-lifecycle", "auth_mode": "github-oidc", "mode": mode,
              "synthetic_input": True, "customer_tables_scanned": 0, "new_ingestion_messages": 0, "containment_actions": 0,
              "approved_sha256": fingerprint()}
    if mode in {"start", "recover"}:
        require(os.environ.get("GITHUB_RUN_ATTEMPT") == "1", "Lifecycle reruns are prohibited")
        previous = recovery_current(client, workspace, target) if mode == "recover" else None
        if mode == "start":
            require(client.request("GET", target + "?api-version=" + API, missing_ok=True) is None, "Single-use rule already exists; do not replay")
        started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        run = os.environ.get("GITHUB_RUN_ID", "")
        body = rule(run, started)
        if previous:
            body["etag"] = previous["etag"]
            report["previous_test_run_reference"] = hashlib.sha256(previous["properties"]["query"].encode()).hexdigest()
            report["recovery_of_disabled_alertless_test"] = True
        print("Lifecycle stage: persist fixed disabled synthetic contract", flush=True)
        client.request("PUT", target + "?api-version=" + API, body)
        try:
            created = client.request("GET", target + "?api-version=" + API)
            parameters(created)
            print("Lifecycle stage: enable only the fixed bounded synthetic rule", flush=True)
            client.request("PUT", target + "?api-version=" + API, rule(run, started, True) | {"etag": created["etag"]})
            for attempt in range(6):
                live = client.request("GET", target + "?api-version=" + API)
                require(parameters(live) == (run, started), "Unexpected persisted synthetic contract")
                if live["properties"]["enabled"] is True:
                    break
                time.sleep(3)
            require(live["properties"]["enabled"] is True, "Enabled state did not persist within bounded read-back")
            print("Lifecycle stage: actual enabled state verified; observe linked incident", flush=True)
            report.update(observe(client, workspace, target))
            report["test_started_utc"] = started
        finally:
            require(disabled(client, target), "Created test rule must persist disabled")
        report["test_rule_disabled"] = True
    elif mode == "observe":
        require(disabled(client, target), "Existing synthetic rule must remain disabled during observation")
        report.update(observe(client, workspace, target))
        report.update(test_rule_disabled=True, observed_existing_test=True, new_rule_activations=0)
    elif mode == "disable":
        report["test_rule_disabled"] = disabled(client, target)
    elif mode == "close":
        require(disabled(client, target), "Test rule must be disabled before closure")
        value = find_incident(client, workspace, target)
        require(value is not None, "Actual linked synthetic incident required")
        from scripts.azure_guard import canonical_uuid
        expected = canonical_uuid(os.environ.get("SENTINEL_LIFECYCLE_INCIDENT_ID", ""))
        require(value.get("name", "").lower() == expected, "Exact approved incident mismatch")
        if value["properties"].get("status") != "Closed":
            client.request("PUT", value["id"] + "?api-version=" + API, close_body(value, target))
        final = client.request("GET", value["id"] + "?api-version=" + API)
        props = validate_incident(final, target)
        require(props.get("status") == "Closed" and props.get("classification") == "BenignPositive" and props.get("classificationReason") == "SuspiciousButExpected", "Final classification was not persisted")
        report.update(incident_created=True, incident_status="Closed", classification="BenignPositive", classification_reason="SuspiciousButExpected", scheduled_rule_link_verified=True, test_rule_disabled=True)
    else:
        raise ValueError("Unsupported lifecycle mode")
    require(other_rules(client, workspace) == baseline, "Original rule properties changed")
    require(workspace_settings(client.request("GET", workspace + "?api-version=2025-02-01")) == settings, "Workspace settings changed")
    report.update(original_thirteen_rules_unchanged=True, workspace_settings_unchanged=True, verified_utc=datetime.now(timezone.utc).isoformat())
    final = client.request("GET", target + "?api-version=" + API, missing_ok=True)
    if final is not None:
        source_run, _ = parameters(final)
        report["test_run_reference"] = hashlib.sha256(final["properties"]["query"].encode()).hexdigest()
        report["scheduled_execution_run"] = "https://github.com/miguelcastu/SentinelOps-MXDR/actions/runs/" + source_run
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["start", "recover", "observe", "close", "disable"])
    args = parser.parse_args()
    require(os.environ.get("SENTINEL_LIFECYCLE_APPROVED_SHA256") == fingerprint(), "Exact reviewed lifecycle approval required before authentication")
    require(datetime.now(timezone.utc) < instant("2026-11-12T18:00:16Z"), "Credit eligibility expired; close locally without cloud work")
    if args.mode in {"start", "recover"}:
        require(datetime.now(timezone.utc) + timedelta(minutes=25) < instant("2026-11-12T18:00:16Z"), "Insufficient time for observation and cleanup before credit expiry")
    workspace = context("validate-lifecycle.yml")
    report = execute(LifecycleClient(), workspace, args.mode)
    print("LIFECYCLE_EVIDENCE=" + json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        # ValueErrors originate in fixed validators and sanitized HTTP code paths.
        raise SystemExit("Lifecycle stopped: " + str(exc) + ". Cleanup step must verify disabled state; no broad permission or replay fallback.") from None
    except (OSError, KeyError, TypeError):
        raise SystemExit("Lifecycle stopped; inspect sanitized step evidence. Cleanup step must verify disabled state. No subscription/permission fallback or automatic replay.") from None
