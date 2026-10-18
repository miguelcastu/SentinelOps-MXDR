"""Evaluate bounded aggregate evidence, preserving Unknown when evidence is absent."""
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = ("Healthy", "Delayed", "Missing", "Misconfigured", "Unknown")
QUERY_STATES = ("success", "not_collected", "not_authorized", "error", "partial")
REASONS = {
    "fresh_complete": "Valid observed events satisfy this source's collection policy.",
    "quiet_event_source": "No events; an event-driven source has no heartbeat obligation.",
    "no_active_batch": "No approved test batch is expected; source onboarding is offline only.",
    "query_unavailable": "Fresh complete query evidence is unavailable; do not infer zero events.",
    "stale_snapshot": "The observation is too old to establish current health.",
    "stale_last_seen": "The last event is old; without a heartbeat this is insufficient freshness evidence.",
    "clock_inconsistent": "Observation timestamps or latency indicate clock inconsistency.",
    "schema_errors": "The observed schema or required-field contract is violated.",
    "mapping_errors": "Required normalized fields do not match the source mapping.",
    "duplicate_events": "Duplicate event IDs were observed; reconcile before replay.",
    "incomplete_batch": "The approved batch deadline passed without all expected unique events.",
    "waiting_batch": "The approved batch has not reached its acceptance deadline.",
    "latency_threshold": "Observed p95 ingestion latency exceeds the source warning threshold.",
    "missing_metrics": "Events exist but freshness or latency evidence is incomplete.",
    "configuration_drift": "Observed configuration differs from the approved source.",
    "configuration_matches": "Observed managed properties match the approved configuration.",
    "metadata_unavailable": "Configuration could not be read using the existing permissions.",
    "export_not_authorized": "CI has no export-read permission; export configuration was not collected.",
    "runtime_not_collected": "Rule execution health was not collected; configuration is separate.",
    "deployment_success": "The latest observed workflow run succeeded.",
    "deployment_failed": "The latest observed workflow run failed; inspect its sanitized run evidence.",
    "deployment_unavailable": "No completed trustworthy workflow observation is available.",
}
OBS_FIELDS = {"source_id", "window_start", "window_end", "observed_at", "query_status",
              "total_events", "valid_events", "distinct_events", "schema_errors", "mapping_errors",
              "negative_latency_events", "last_seen", "latency_p95_seconds", "billable_bytes",
              "expected_events", "expected_by", "hourly_volume"}
COUNTS = ("total_events", "valid_events", "distinct_events", "schema_errors", "mapping_errors",
          "negative_latency_events", "billable_bytes")


def require(condition):
    if not condition:
        raise ValueError("Invalid bounded health evidence or policy contract")


def instant(value):
    require(isinstance(value, str) and len(value) <= 40 and "T" in value)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(parsed.tzinfo is not None)
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise ValueError("Health timestamps require a valid explicit UTC offset") from None


def integer(value, maximum=1_000_000_000_000):
    return type(value) is int and 0 <= value <= maximum


def policies():
    value = json.loads((ROOT / "platform_health/policies.json").read_text(encoding="utf-8"))
    require(type(value["planning_eur_per_gb"]) in (int, float) and math.isfinite(value["planning_eur_per_gb"]) and
            0 < value["planning_eur_per_gb"] <= 100)
    inventory = json.loads((ROOT / "ingestion/sources.json").read_text(encoding="utf-8"))["sources"]
    require(len(inventory) == len({s["id"] for s in inventory}) and
            {s["id"] for s in inventory} == set(value["sources"]))
    for source in inventory:
        policy = value["sources"][source["id"]]
        require(source["heartbeat"] == policy["collection_model"])
        require(all(integer(policy[k], 86_400) and policy[k] > 0 for k in
                    ("latency_warning_seconds", "snapshot_max_age_seconds", "freshness_warning_seconds")))
    return value, inventory


def blank_observation(source_id, now, start):
    return dict(source_id=source_id, window_start=start, window_end=now, observed_at=now,
                query_status="not_collected", total_events=None, valid_events=None,
                distinct_events=None, schema_errors=None, mapping_errors=None,
                negative_latency_events=None, last_seen=None, latency_p95_seconds=None,
                billable_bytes=None, expected_events=None, expected_by=None, hourly_volume=[])


def validate_observation(value, policy):
    require(isinstance(value, dict) and set(value) == OBS_FIELDS and value["query_status"] in QUERY_STATES)
    start, end, observed = (instant(value[k]) for k in ("window_start", "window_end", "observed_at"))
    require(0 < (end - start).total_seconds() <= 86_400 and end <= observed)
    for key in COUNTS:
        require(value[key] is None or integer(value[key]))
    latency = value["latency_p95_seconds"]
    require(latency is None or (type(latency) in (int, float) and math.isfinite(latency) and 0 <= latency <= 604_800))
    expected, deadline = value["expected_events"], value["expected_by"]
    require((expected is None and deadline is None) or
            (integer(expected, 100) and expected > 0 and deadline is not None))
    if deadline is not None:
        require(policy["collection_model"] == "single-approved-test-batch-only")
        require(start <= instant(deadline) <= end + timedelta(minutes=15))
    if value["last_seen"] is not None:
        require(start <= instant(value["last_seen"]) <= end)
    if value["query_status"] == "success":
        require(all(value[k] is not None for k in COUNTS))
        total = value["total_events"]
        require(value["valid_events"] <= total and value["distinct_events"] <= total and
                all(value[k] <= total for k in ("schema_errors", "mapping_errors", "negative_latency_events")))
        require(value["valid_events"] + value["schema_errors"] == total)
        require(total != 0 or value["last_seen"] is None)
    require(isinstance(value["hourly_volume"], list) and len(value["hourly_volume"]) <= 24)
    seen = set()
    for bucket in value["hourly_volume"]:
        require(isinstance(bucket, dict) and set(bucket) == {"start", "events"} and integer(bucket["events"]))
        time = instant(bucket["start"])
        require(start <= time < end and time not in seen)
        seen.add(time)
    if value["hourly_volume"] and value["query_status"] == "success":
        require(sum(b["events"] for b in value["hourly_volume"]) == value["total_events"])


def evaluate_source(observation, policy, now):
    validate_observation(observation, policy)
    source = observation["source_id"]

    def result(state, reason):
        success = observation["query_status"] == "success"
        total = observation["total_events"] if success else None
        return {"source_id": source, "state": state, "reason": reason, "explanation": REASONS[reason],
                "window_start": observation["window_start"], "window_end": observation["window_end"],
                "query_status": observation["query_status"], "total_events": total,
                "distinct_events": observation["distinct_events"] if success else None,
                "schema_errors": observation["schema_errors"] if success else None,
                "mapping_errors": observation["mapping_errors"] if success else None,
                "negative_latency_events": observation["negative_latency_events"] if success else None,
                "expected_events": observation["expected_events"], "expected_by": observation["expected_by"],
                "last_seen": observation["last_seen"] if success else None,
                "latency_p95_seconds": observation["latency_p95_seconds"] if success else None,
                "validity_ratio": observation["valid_events"] / total if total else None,
                "uniqueness_ratio": observation["distinct_events"] / total if total else None,
                "duplicate_events": total - observation["distinct_events"] if success else None,
                "billable_bytes": observation["billable_bytes"] if success else None,
                "hourly_volume": observation["hourly_volume"] if success else []}

    age = (now - instant(observation["observed_at"])).total_seconds()
    if age < -60:
        return result("Misconfigured", "clock_inconsistent")
    if age > policy["snapshot_max_age_seconds"]:
        return result("Unknown", "stale_snapshot")
    if observation["query_status"] != "success":
        return result("Unknown", "query_unavailable")
    if observation["negative_latency_events"]:
        return result("Misconfigured", "clock_inconsistent")
    if observation["schema_errors"] or observation["valid_events"] < observation["total_events"]:
        return result("Misconfigured", "schema_errors")
    if observation["mapping_errors"]:
        return result("Misconfigured", "mapping_errors")
    if observation["distinct_events"] < observation["total_events"]:
        return result("Misconfigured", "duplicate_events")
    expected = observation["expected_events"]
    if expected is not None and observation["distinct_events"] < expected:
        if now >= instant(observation["expected_by"]):
            return result("Missing", "incomplete_batch")
        return result("Unknown", "waiting_batch")
    if observation["total_events"] == 0:
        reason = "quiet_event_source" if policy["collection_model"] == "event-driven" else "no_active_batch"
        return result("Unknown", reason)
    if observation["last_seen"] is None or observation["latency_p95_seconds"] is None:
        return result("Unknown", "missing_metrics")
    if observation["latency_p95_seconds"] > policy["latency_warning_seconds"]:
        return result("Delayed", "latency_threshold")
    if (now - instant(observation["last_seen"])).total_seconds() > policy["freshness_warning_seconds"]:
        return result("Unknown", "stale_last_seen")
    return result("Healthy", "fresh_complete")


def combine(states):
    require(all(state in STATES for state in states))
    return next((state for state in ("Misconfigured", "Missing", "Delayed", "Unknown") if state in states), "Healthy")


def report(snapshot, now=None):
    require(isinstance(snapshot, dict) and set(snapshot) ==
            {"schema_version", "evidence", "observed_at", "sources", "checks", "rules"})
    require(snapshot["schema_version"] == "1.0" and snapshot["evidence"] in
            ("synthetic", "azure-control-plane", "external-aggregate"))
    now = datetime.now(timezone.utc) if now is None else instant(now)
    config, inventory = policies()
    require(isinstance(snapshot["sources"], list) and len(snapshot["sources"]) == len(inventory) and
            {s["source_id"] for s in snapshot["sources"]} == set(config["sources"]))
    sources = [evaluate_source(s, config["sources"][s["source_id"]], now) for s in snapshot["sources"]]
    by_id = {s["id"]: s for s in inventory}
    for source in sources:
        entry = by_id[source["source_id"]]
        source.update(table=entry["table"], owner=entry["owner"], onboarding_state=entry["state"],
                      collection_model=config["sources"][source["source_id"]]["collection_model"])
    checks = snapshot["checks"]
    require(isinstance(checks, list) and len(checks) <= 12)
    allowed_checks = {"workspace", "AZ-DET-001", "AZ-DET-002", "rule-runtime", "activity-export",
                      "validate.yml", "deploy-sentinel.yml", "deploy-additional-detection.yml"}
    require(len({c["id"] for c in checks}) == len(checks))
    for check in checks:
        require(set(check) == {"id", "state", "reason"} and check["id"] in allowed_checks and
                check["state"] in STATES and check["reason"] in REASONS)
    age = (now - instant(snapshot["observed_at"])).total_seconds()
    if age > 900 or age < -60:
        checks = [dict(c, state="Unknown", reason="stale_snapshot") for c in checks]
    rules = snapshot["rules"]
    require(isinstance(rules, dict) and set(rules) == {"expected", "present", "matching", "active", "intentionally_disabled"})
    require(all(v is None or integer(v, 100) for v in rules.values()))
    require(rules["expected"] == 2)
    if all(v is not None for v in rules.values()):
        require(rules["matching"] <= rules["present"] and
                rules["active"] + rules["intentionally_disabled"] <= rules["present"])
    known_cost = [s["billable_bytes"] for s in sources if s["billable_bytes"] is not None]
    return {"schema_version": "1.0", "evidence": snapshot["evidence"], "observed_at": snapshot["observed_at"],
            "evaluated_at": now.isoformat().replace("+00:00", "Z"),
            "state": combine([s["state"] for s in sources] + [c["state"] for c in checks]),
            "sources": sources, "checks": checks, "rules": rules,
            "coverage": {"inventoried_sources": len(inventory), "queried_sources": sum(s["query_status"] == "success" for s in sources),
                         "healthy_sources": sum(s["state"] == "Healthy" for s in sources),
                         "inventory_cloud_sources": sum(s["state"] == "existing-cloud-source" for s in inventory)},
            "cost": {"known_sources": len(known_cost), "complete": len(known_cost) == len(sources),
                     "observed_billable_bytes": sum(known_cost) if known_cost else None,
                     "planning_eur_per_gb": config["planning_eur_per_gb"],
                     "estimated_observed_eur": sum(known_cost) / 1e9 * config["planning_eur_per_gb"] if known_cost else None,
                     "invoice_verified": False},
            "limits": {"log_queries_executed": 0, "recurring_schedule": False,
                       "runtime_health_verified": False}}
