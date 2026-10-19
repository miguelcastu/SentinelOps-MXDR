"""Synthetic Python reference model. This does not parse or execute Kusto."""
from collections import defaultdict
from datetime import datetime, timezone
from portfolio.catalog import SPECS
from scripts.validate_detection import require


def stamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "Timestamp must have an offset")
    return parsed.astimezone(timezone.utc)


def evaluate(key, events, as_of):
    require(key in SPECS and isinstance(events, list) and len(events) <= 1000, "Invalid bounded simulation")
    end = stamp(as_of)
    unique = {}
    for event in events:
        require(isinstance(event, dict) and event.get("synthetic") is True, "Only explicitly synthetic input is accepted")
        event_id = event.get("EventDataId", "")
        if not event_id:
            continue
        require(isinstance(event_id, str) and event_id.startswith("synthetic-event-"), "Only synthetic event identifiers are accepted")
        require(event_id not in unique or unique[event_id] == event, "Conflicting source event duplicates")
        unique[event_id] = event
    operations = {x.casefold() for x in SPECS[key][4]}
    kind = SPECS[key][5]
    statuses = {"failed", "failure"} if kind == "burst" else {"success", "succeeded"}
    selected = [e for e in unique.values() if 0 <= (end - stamp(e["TimeGenerated"])).total_seconds() <= 3600
                and e["OperationNameValue"].casefold() in operations and e["ActivityStatusValue"].casefold() in statuses]
    if kind == "single":
        return sorted((e["EventDataId"],) for e in selected)
    selected = [e for e in selected if e.get("Caller") and e.get("ResourceGroup")]
    if kind == "burst":
        groups = defaultdict(list)
        for event in selected:
            group = (event["Caller"].casefold(), event["ResourceGroup"].casefold(),
                     int(stamp(event["TimeGenerated"]).timestamp() // 600))
            groups[group].append(event["EventDataId"])
        return sorted(tuple(sorted(ids)) for ids in groups.values() if len(ids) >= 5)
    findings = []
    for diagnostic in selected:
        if diagnostic["OperationNameValue"].casefold() == "microsoft.authorization/roleassignments/write":
            continue
        grants = [e for e in selected if e["OperationNameValue"].casefold() == "microsoft.authorization/roleassignments/write"
                  and e["Caller"].casefold() == diagnostic["Caller"].casefold()
                  and e["ResourceGroup"].casefold() == diagnostic["ResourceGroup"].casefold()
                  and 0 < (stamp(diagnostic["TimeGenerated"]) - stamp(e["TimeGenerated"])).total_seconds() <= 900]
        if grants:
            latest = max(grants, key=lambda e: (stamp(e["TimeGenerated"]), e["EventDataId"]))
            findings.append((latest["EventDataId"], diagnostic["EventDataId"]))
    return sorted(findings)


def event(operation, *, suffix="1", time="2026-10-19T12:05:00Z", status="Succeeded", caller="synthetic-principal-00", scope="synthetic-rg-00"):
    return {"synthetic": True, "EventDataId": "synthetic-event-" + suffix, "TimeGenerated": time,
            "OperationNameValue": operation, "ActivityStatusValue": status, "Caller": caller, "ResourceGroup": scope}


def scenarios():
    rows = []
    for key, spec in SPECS.items():
        operation, kind = spec[4][0], spec[5]
        if kind == "single":
            positive = [event(operation)]
        elif kind == "burst":
            positive = [event(operation, status="Failed", suffix=str(i)) for i in range(5)]
        else:
            positive = [event(operation, suffix="grant"), event(spec[4][1], suffix="diag", time="2026-10-19T12:10:00Z")]
        rows += [{"id": key + "/positive", "detection": key, "events": positive, "expected": 1},
                 {"id": key + "/replayed", "detection": key, "events": positive + positive, "expected": 1},
                 {"id": key + "/started", "detection": key, "events": [dict(e, ActivityStatusValue="Started") for e in positive], "expected": 0},
                 {"id": key + "/wrong-operation", "detection": key, "events": [dict(e, OperationNameValue=e["OperationNameValue"] + "/extra") for e in positive], "expected": 0},
                 {"id": key + "/stale", "detection": key, "events": [dict(e, TimeGenerated="2026-10-19T10:00:00Z") for e in positive], "expected": 0},
                 {"id": key + "/missing-lineage", "detection": key, "events": [dict(e, EventDataId="") for e in positive], "expected": 0}]
    return rows
