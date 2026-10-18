"""Bounded signal contract: fictional identities and documentation IPs only."""
import ipaddress
import json
import math
import re
from datetime import datetime
from pathlib import Path

from ingestion.events import DOCUMENTATION_NETWORKS, timestamp

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {"synthetic", "event_id", "source_event_id", "time", "source", "kind", "actor", "host", "source_ip", "resource"}
SOURCES = {"azure-activity", "synthetic-authentication", "synthetic-endpoint"}
HEALTH_STATES = {"Healthy", "Delayed", "Missing", "Misconfigured", "Unknown"}


def require(value):
    if not value:
        raise ValueError("Invalid synthetic risk contract; no input values were logged")


def instant(value):
    return datetime.fromisoformat(timestamp(value).replace("Z", "+00:00"))


def load_policy():
    policy = json.loads((ROOT / "rba/catalog.json").read_text(encoding="utf-8"))
    require(policy["policy_version"] == "atlas-rba-1.0")
    for key, maximum in (("window_minutes", 60), ("lookback_minutes", 240), ("half_life_minutes", 120),
                         ("finding_threshold", 100), ("sequence_span_minutes", 60), ("max_events", 500), ("max_actors", 32)):
        require(type(policy[key]) is int and 0 < policy[key] <= maximum)
    require(policy["window_minutes"] <= policy["lookback_minutes"])
    require(type(policy["sequence_bonus"]) is int and 0 <= policy["sequence_bonus"] <= 20)
    for signal in policy["signals"].values():
        require(signal["source"] in SOURCES)
        require(all(type(signal[k]) in (int, float) and math.isfinite(signal[k]) and signal[k] >= 0
                    for k in ("points", "confidence", "cap")))
        require(signal["confidence"] <= 1 and signal["points"] <= 50 and signal["cap"] <= 40)
    return policy


def signal(event, policy):
    require(isinstance(event, dict) and set(event) == FIELDS and event["synthetic"] is True)
    for key, pattern in (("event_id", r"synthetic-[0-9a-f]{32}"), ("source_event_id", r"synthetic-[0-9a-f]{32}"),
                         ("actor", r"synthetic-user-[0-9]{2}")):
        require(isinstance(event[key], str) and re.fullmatch(pattern, event[key]) is not None)
    require(isinstance(event["kind"], str) and event["kind"] in policy["signals"])
    require(event["source"] == policy["signals"][event["kind"]]["source"])
    for key, pattern in (("host", r"lab-auth-[0-9]{2}"), ("resource", r"lab-resource-[a-z0-9-]{1,40}")):
        require(event[key] is None or isinstance(event[key], str) and re.fullmatch(pattern, event[key]) is not None)
    if event["source_ip"] is not None:
        try:
            ip = ipaddress.ip_address(event["source_ip"])
        except (ValueError, TypeError):
            raise ValueError("Invalid documentation IP in synthetic risk input") from None
        require(any(ip.version == n.version and ip in n for n in DOCUMENTATION_NETWORKS))
    if event["source"] == "synthetic-authentication":
        require(event["host"] is not None and event["source_ip"] is not None)
    if event["kind"] == "endpoint_execution":
        require(event["host"] is not None)
    if event["source"] == "azure-activity":
        require(event["resource"] is not None)
    return dict(event, time=timestamp(event["time"]), source_ip=str(ipaddress.ip_address(event["source_ip"])) if event["source_ip"] else None)


def baselines(policy):
    entries = json.loads((ROOT / "rba/baselines.json").read_text(encoding="utf-8"))
    require(isinstance(entries, list) and len(entries) <= 20)
    fields = {"change_id", "actor", "source", "kind", "resource", "start", "end", "factor"}
    for entry in entries:
        require(set(entry) == fields and entry["kind"] in ("rbac_assignment", "diagnostic_change", "policy_change"))
        require(re.fullmatch(r"lab-change-[0-9]{3}", entry["change_id"]) is not None)
        require(re.fullmatch(r"synthetic-user-[0-9]{2}", entry["actor"]) is not None)
        require(re.fullmatch(r"lab-resource-[a-z0-9-]{1,40}", entry["resource"]) is not None)
        require(entry["source"] == policy["signals"][entry["kind"]]["source"])
        require(0 < (instant(entry["end"]) - instant(entry["start"])).total_seconds() <= 1800)
        require(type(entry["factor"]) in (int, float) and .25 <= entry["factor"] < 1)
    for i, left in enumerate(entries):
        for right in entries[i + 1:]:
            if all(left[k] == right[k] for k in ("actor", "source", "kind", "resource")):
                require(max(instant(left["start"]), instant(right["start"])) > min(instant(left["end"]), instant(right["end"])))
    return entries


def baseline_match(event, entries):
    return next((entry for entry in entries if all(event[k] == entry[k] for k in ("actor", "source", "kind", "resource"))
                 and instant(entry["start"]) <= instant(event["time"]) <= instant(entry["end"])), None)
