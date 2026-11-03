"""No arbitrary query/target inputs; a single self-expiring test, not coverage."""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

RULE_UUID = "c2525513-183f-54a0-91df-ea25f81141ce"
TITLE = "LAB-VAL-001 - Synthetic lifecycle acceptance"
API = "2025-09-01"
READER = "SentinelOps Lifecycle Incident Reader"
CLOSER = "SentinelOps Exact Test Incident Classifier"
QUERY_ROLE = "SentinelOps Inline Query Execution Gate"
QUERY_ACTIONS = ["Microsoft.OperationalInsights/workspaces/query/read"]
READ_ACTIONS = ["Microsoft.SecurityInsights/incidents/read"]
CLOSE_ACTIONS = ["Microsoft.SecurityInsights/incidents/read", "Microsoft.SecurityInsights/incidents/write"]


def require(value, message="Fixed synthetic lifecycle contract rejected"):
    if not value:
        raise ValueError(message)


def instant(value):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value))
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def rule(run, started, enabled=False):
    require(isinstance(run, str) and re.fullmatch(r"[0-9]{6,20}", run))
    start = instant(started)
    deadline = (start + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
    require(type(enabled) is bool)
    query = (
        "// Explicit synthetic test; no customer table is read and no attack is executed.\n"
        f"let TestDeadline = datetime({deadline});\n"
        "datatable(TimeGenerated:datetime, RunToken:string, EventType:string, Synthetic:bool)\n"
        f"[datetime({started}), '{run}', 'SentinelOpsLifecycleTest', true]\n"
        f"| where now() between (datetime({started}) .. TestDeadline)\n"
        "| extend TestAccount = 'synthetic-lab-operator'\n"
    )
    return {"kind": "Scheduled", "properties": {
        "displayName": TITLE, "description": "Explicit synthetic single-use lifecycle acceptance, not a threat detection. No customer table scanned. Automatically empty after twenty minutes; finally disabled by OIDC.",
        "enabled": enabled, "severity": "Informational", "query": query,
        "queryFrequency": "PT5M", "queryPeriod": "PT30M", "triggerOperator": "GreaterThan", "triggerThreshold": 0,
        "suppressionEnabled": False, "suppressionDuration": "PT1H", "tactics": [], "techniques": [],
        "entityMappings": [{"entityType": "Account", "fieldMappings": [{"identifier": "Name", "columnName": "TestAccount"}]}],
        "customDetails": {"RunToken": "RunToken", "Synthetic": "Synthetic", "EventType": "EventType"},
        "eventGroupingSettings": {"aggregationKind": "SingleAlert"},
        "incidentConfiguration": {"createIncident": True, "groupingConfiguration": {
            "enabled": True, "reopenClosedIncident": False, "lookbackDuration": "PT1H", "matchingMethod": "AllEntities",
            "groupByEntities": [], "groupByAlertDetails": [], "groupByCustomDetails": []}}}}


def parameters(current):
    require(isinstance(current, dict) and current.get("kind") == "Scheduled")
    props = current.get("properties", {})
    query = props.get("query", "")
    match = re.search(r"\[datetime\(([^)]+)\), '([0-9]{6,20})', 'SentinelOpsLifecycleTest', true\]", query)
    require(match is not None and type(props.get("enabled")) is bool)
    started, run = match.groups()
    expected = rule(run, started, props["enabled"])
    require(all(props.get(k) == v for k, v in expected["properties"].items()))
    return run, started


def fingerprint():
    spec = {"rule": rule("1234567890", "2026-11-03T00:00:00Z"), "uuid": RULE_UUID,
            "reader": READ_ACTIONS, "closer": CLOSE_ACTIONS, "polls": 24, "interval_seconds": 30,
            "new_ingestion_messages": 0, "personal_deployment": False, "query_execution_gate": QUERY_ACTIONS,
            "table_data_grants": [], "recovery": "one explicit prior-query SHA256; disabled/no-incident preflight; fresh bounded window; no automatic replay"}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def validate_incident(value, target):
    props = value.get("properties", {})
    related = props.get("relatedAnalyticRuleIds", [])
    require(props.get("title") == TITLE and len(related) == 1 and related[0].lower() == target.lower(), "Incident is not linked exclusively to the fixed synthetic rule")
    count = props.get("additionalData", {}).get("alertsCount")
    require(type(count) is int and 1 <= count <= 5, "A bounded actual scheduled alert count is required")
    return props


def close_body(value, target):
    props = validate_incident(value, target)
    require(props.get("status") in {"New", "Active"}, "Test incident must still be open")
    require(isinstance(value.get("etag"), str) and value["etag"], "Incident concurrency token required")
    return {"etag": value["etag"], "properties": {
        "title": TITLE, "description": props.get("description", ""), "severity": props["severity"],
        "status": "Closed", "classification": "BenignPositive", "classificationReason": "SuspiciousButExpected",
        "classificationComment": "Authorized SentinelOps synthetic lifecycle test. The scheduled rule matched a labeled inline test event, not a customer attack. Related rule/alert verified; existing twelve detections remain disabled. No containment performed."}}
