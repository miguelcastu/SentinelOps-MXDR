"""Strict source contract and ASIM-shaped normalization (not a registered ASIM parser)."""
import ipaddress
import re
import uuid
from datetime import datetime, timedelta, timezone

SOURCE = "sentinelops-synthetic-auth"
TABLE = "SentinelOpsAuth_CL"
STREAM = "Custom-SentinelOpsAuth"
MAX_EVENTS = 100
RAW_FIELDS = {"schema_version", "synthetic", "source", "event_id", "batch_id",
              "timestamp", "event_code", "hostname", "username", "source_ip"}
COLUMNS = {
    "TimeGenerated": "datetime", "EventStartTime": "datetime", "EventEndTime": "datetime",
    "EventCount": "int", "EventType": "string", "EventResult": "string",
    "EventVendor": "string", "EventProduct": "string", "EventSchema": "string",
    "EventSchemaVersion": "string", "EventOriginalUid": "string", "EventOriginalType": "string",
    "Dvc": "string", "DvcHostname": "string", "TargetUsername": "string",
    "SrcIpAddr": "string", "Synthetic": "boolean", "BatchId": "string", "CustomerName": "string",
}
DOCUMENTATION_NETWORKS = tuple(ipaddress.ip_network(n) for n in
    ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24", "2001:db8::/32"))


def timestamp(value):
    if (not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", value)):
        raise ValueError("Timestamp must be an explicit ISO 8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
        return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    except (ValueError, OverflowError):
        raise ValueError("Timestamp requires a valid explicit UTC offset") from None


def validate(event):
    if not isinstance(event, dict) or set(event) != RAW_FIELDS:
        raise ValueError("Source event has missing or unexpected fields")
    if event["synthetic"] is not True or event["source"] != SOURCE or event["schema_version"] != "1.0":
        raise ValueError("Only explicitly labeled synthetic schema 1.0 events are accepted")
    if type(event["event_code"]) is not int or event["event_code"] not in (4624, 4625):
        raise ValueError("Only synthetic authentication codes 4624 and 4625 are supported")
    patterns = {"event_id": r"synthetic-[0-9a-f]{32}", "batch_id": r"synthetic-[0-9a-f]{32}",
                "hostname": r"lab-auth-[0-9]{2}", "username": r"synthetic-user-[0-9]{2}"}
    for key, pattern in patterns.items():
        if not isinstance(event[key], str) or not re.fullmatch(pattern, event[key]):
            raise ValueError("Synthetic identifier contract rejected")
    timestamp(event["timestamp"])
    try:
        address = ipaddress.ip_address(event["source_ip"])
    except (ValueError, TypeError):
        raise ValueError("Invalid synthetic source IP") from None
    if not any(address.version == network.version and address in network for network in DOCUMENTATION_NETWORKS):
        raise ValueError("Only documentation IP addresses are permitted")
    return event


def normalize(event):
    validate(event)
    time = timestamp(event["timestamp"])
    return {
        "TimeGenerated": time, "EventStartTime": time, "EventEndTime": time, "EventCount": 1,
        "EventType": "Logon", "EventResult": "Success" if event["event_code"] == 4624 else "Failure",
        "EventVendor": "SentinelOps", "EventProduct": "SyntheticAuthLab",
        "EventSchema": "Authentication", "EventSchemaVersion": "1.0.0",
        "EventOriginalUid": event["event_id"], "EventOriginalType": str(event["event_code"]),
        "Dvc": event["hostname"], "DvcHostname": event["hostname"],
        "TargetUsername": event["username"], "SrcIpAddr": event["source_ip"],
        "Synthetic": True, "BatchId": event["batch_id"], "CustomerName": "Atlas Financial",
    }


def normalize_many(events):
    if not isinstance(events, list) or not 1 <= len(events) <= MAX_EVENTS:
        raise ValueError("One bounded run requires 1 to 100 source events")
    result = [normalize(event) for event in events]
    if len({event["BatchId"] for event in result}) != 1:
        raise ValueError("One invocation accepts exactly one synthetic batch")
    if len({event["EventOriginalUid"] for event in result}) != len(result):
        raise ValueError("Duplicate source event IDs rejected before ingestion")
    return result


def generate(count=24, start="2026-10-18T10:00:00Z", seed="demo"):
    if type(count) is not int or not 1 <= count <= MAX_EVENTS:
        raise ValueError("Generate 1 to 100 events")
    if not isinstance(seed, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", seed):
        raise ValueError("Seed must be a short non-sensitive label")
    base = datetime.fromisoformat(timestamp(start).replace("Z", "+00:00"))
    batch = "synthetic-" + uuid.uuid5(uuid.NAMESPACE_URL, SOURCE + seed + timestamp(start)).hex
    return [{"schema_version": "1.0", "synthetic": True, "source": SOURCE,
             "event_id": "synthetic-" + uuid.uuid5(uuid.NAMESPACE_URL, batch + "/" + str(i)).hex,
             "batch_id": batch, "timestamp": timestamp((base + timedelta(seconds=i)).isoformat()),
             "event_code": 4625 if i % 3 == 0 else 4624, "hostname": f"lab-auth-{i % 3:02}",
             "username": f"synthetic-user-{i % 4:02}", "source_ip": "192.0.2." + str(10 + i % 4)}
            for i in range(count)]
