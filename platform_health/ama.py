"""Offline adapter for already recorded pilot/shutdown evidence, never a collector.

The pilot measured four aggregate columns, not the health schema/latency
contract. Preserve that fact instead of filling unmeasured metrics with zeros.
Local JSON records are not independently authenticated Azure responses.
"""
from datetime import timedelta

from ama.plan import MACHINE
from platform_health.engine import blank_observation, instant, require


def pilot_observation(pilot, shutdown):
    require(isinstance(pilot, dict) and set(pilot) == {
        "evidence", "observed_utc", "events", "unique_events", "last_seen", "billable_bytes",
        "messages_sent", "payload_bytes", "query_attempts", "raw_events_returned", "reconciled", "kusto_executed"})
    require(pilot["evidence"] == "actual-log-analytics-aggregate" and pilot["kusto_executed"] is True)
    require(pilot["reconciled"] is True and type(pilot["events"]) is int and
            pilot["events"] == pilot["unique_events"] == pilot["messages_sent"] == 10)
    require(type(pilot["payload_bytes"]) is int and 0 < pilot["payload_bytes"] <= 4096)
    require(isinstance(shutdown, dict) and set(shutdown) == {
        "evidence", "observed_utc", "machine", "shutdown_method", "vm_state", "azure_compute_created", "pilot_replayed"})
    require(shutdown["evidence"] == "actual-local-hypervisor" and shutdown["machine"] == MACHINE)
    require(shutdown["vm_state"] == "poweroff" and shutdown["shutdown_method"] == "guest-sudo-shutdown")
    require(shutdown["azure_compute_created"] is False and shutdown["pilot_replayed"] is False)
    at = instant(pilot["observed_utc"])
    require(instant(shutdown["observed_utc"]) >= at)
    stamp = at.isoformat().replace("+00:00", "Z")
    start = (at - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    result = blank_observation("ama-linux-syslog", stamp, start)
    result["operation_context"] = {"machine_state": "stopped", "observed_at": shutdown["observed_utc"],
                                   "evidence": "local-hypervisor", "reason": "operator-shutdown"}
    result["pilot_evidence"] = {
        "evidence": "recorded-pilot-aggregate", "observed_at": stamp,
        "total_events": pilot["events"], "distinct_events": pilot["unique_events"],
        "last_seen": pilot["last_seen"], "billable_bytes": pilot["billable_bytes"],
        "query_attempts": pilot["query_attempts"], "raw_events_returned": pilot["raw_events_returned"],
        "complete_health_metrics": False}
    # query_status remains not_collected: no full HEALTH aggregate was executed.
    # The recorded pilot columns are separate and never imply schema/latency.
    return result
