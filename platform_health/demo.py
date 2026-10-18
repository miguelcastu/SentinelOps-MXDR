"""Safe fault injection in memory. Never disables collection or calls Azure."""
import copy
import ipaddress
import math
import re
from datetime import timedelta

from ingestion.events import COLUMNS, generate, normalize_many
from platform_health.engine import blank_observation, instant

NOW = "2026-10-18T12:00:00Z"


def auth_observation(events, now=NOW):
    end = instant(now)
    start = (end - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    observation = blank_observation("synthetic-authentication", now, start)
    seen, times, latencies = set(), [], []
    schema_errors = mapping_errors = negative = 0
    ingested = end - timedelta(minutes=1)
    for event in events:
        bad_schema = not isinstance(event, dict) or set(event) != set(COLUMNS)
        bad_mapping = False
        time = None
        if isinstance(event, dict):
            for key, kind in COLUMNS.items():
                value = event.get(key)
                if (kind in ("string", "datetime") and not isinstance(value, str) or
                        kind == "int" and type(value) is not int or kind == "boolean" and type(value) is not bool):
                    bad_schema = True
            try:
                time = instant(event.get("TimeGenerated"))
                times.append(time)
                latency = (ingested - time).total_seconds()
                if latency < 0:
                    negative += 1
                else:
                    latencies.append(latency)
                bad_mapping = (event.get("EventType") != "Logon" or event.get("EventResult") not in ("Success", "Failure") or
                               event.get("EventSchema") != "Authentication" or event.get("Synthetic") is not True or
                               event.get("EventStartTime") != event.get("TimeGenerated") or
                               event.get("EventEndTime") != event.get("TimeGenerated") or
                               not re.fullmatch(r"synthetic-user-[0-9]{2}", event.get("TargetUsername", "")))
                ipaddress.ip_address(event.get("SrcIpAddr"))
            except (ValueError, TypeError):
                bad_mapping = True
            uid = event.get("EventOriginalUid")
            if isinstance(uid, str):
                seen.add(uid)
        schema_errors += bad_schema
        mapping_errors += bad_mapping and not bad_schema
    latencies.sort()
    observation.update(query_status="success", total_events=len(events), valid_events=len(events) - schema_errors,
        distinct_events=len(seen), schema_errors=schema_errors, mapping_errors=mapping_errors,
        negative_latency_events=negative, last_seen=max(times).isoformat().replace("+00:00", "Z") if times else None,
        latency_p95_seconds=latencies[math.ceil(.95 * len(latencies)) - 1] if latencies else None,
        billable_bytes=len(events) * 400, expected_events=24,
        expected_by=ingested.isoformat().replace("+00:00", "Z"), hourly_volume=[{"start": start, "events": len(events)}])
    return observation


def baseline():
    auth = auth_observation(normalize_many(generate(24, "2026-10-18T11:58:00Z", "health")))
    activity = copy.deepcopy(auth)
    activity.update(source_id="azure-activity", total_events=3, valid_events=3, distinct_events=3,
                    expected_events=None, expected_by=None, latency_p95_seconds=480, billable_bytes=0,
                    hourly_volume=[{"start": "2026-10-18T11:00:00Z", "events": 3}])
    return {"schema_version": "1.0", "evidence": "synthetic", "observed_at": NOW,
            "sources": [activity, auth],
            "checks": [{"id": key, "state": "Healthy", "reason": "configuration_matches"}
                       for key in ("workspace", "AZ-DET-001", "AZ-DET-002")],
            "rules": {"expected": 2, "present": 2, "matching": 2, "active": 0, "intentionally_disabled": 2}}


def scenarios():
    result = []

    def append(name, snapshot, state, target="synthetic-authentication"):
        result.append({"scenario": name, "target": target, "expected": state, "snapshot": snapshot})

    append("healthy-batch", baseline(), "Healthy")
    empty = auth_observation([])
    snapshot = baseline()
    snapshot["sources"][1] = empty
    append("missing-approved-batch", snapshot, "Missing")
    snapshot = baseline()
    snapshot["sources"][0] = dict(empty, source_id="azure-activity", expected_events=None, expected_by=None)
    append("quiet-activity-is-unknown", snapshot, "Unknown", "azure-activity")
    for name, state in (("delayed-events", "Delayed"), ("malformed-event", "Misconfigured"),
                        ("wrong-field-mapping", "Misconfigured"), ("schema-evolution", "Misconfigured"),
                        ("duplicate-event", "Misconfigured")):
        events = normalize_many(generate(24, "2026-10-18T11:30:00Z" if name == "delayed-events" else
                                        "2026-10-18T11:58:00Z", "health"))
        if name == "malformed-event":
            events[0]["EventCount"] = "one"
        elif name == "wrong-field-mapping":
            events[0]["SrcIpAddr"], events[0]["TargetUsername"] = events[0]["TargetUsername"], events[0]["SrcIpAddr"]
        elif name == "schema-evolution":
            events[0]["UnexpectedVersion2Field"] = True
        elif name == "duplicate-event":
            events.append(copy.deepcopy(events[0]))
        snapshot = baseline()
        snapshot["sources"][1] = auth_observation(events)
        append(name, snapshot, state)
    snapshot = baseline()
    snapshot["checks"][0].update(state="Misconfigured", reason="configuration_drift")
    append("configuration-drift", snapshot, "Misconfigured", "workspace")
    snapshot = baseline()
    snapshot["checks"].append({"id": "deploy-sentinel.yml", "state": "Misconfigured", "reason": "deployment_failed"})
    append("failed-deployment", snapshot, "Misconfigured", "deploy-sentinel.yml")
    snapshot = baseline()
    snapshot["sources"][1]["query_status"] = "partial"
    append("partial-query-is-unknown", snapshot, "Unknown")
    return result
