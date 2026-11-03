"""Validate fictional service artifacts against versioned source; no network."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
RULE_IDS = {f"AZ-DET-{number:03d}" for number in range(1, 13)}
TICKET_CATEGORIES = {
    "source-onboarding", "connector-troubleshooting", "detection-tuning",
    "incident-investigation", "pipeline-failure", "automation-deployment",
    "cost-investigation", "configuration-drift",
}
DELIVERABLE_IDS = {
    "discovery", "security-requirements", "monitoring-scope", "architecture",
    "responsibility-matrix", "source-onboarding", "detection-coverage",
    "mitre-report", "detection-catalog", "operations-runbooks", "triage",
    "incident-response", "health-reporting", "cost-retention", "kpis-slis",
    "change-management", "troubleshooting-escalation", "acceptance-checklist",
    "risk-register", "handover",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def existing_path(value):
    require(isinstance(value, str) and value and "\\" not in value,
            "A repository-relative artifact path is required")
    candidate = (ROOT / value).resolve()
    require(not Path(value).is_absolute() and candidate.is_relative_to(ROOT)
            and not {part.casefold() for part in candidate.relative_to(ROOT).parts}
            & {".local", ".git"},
            "Artifact path must remain in public repository scope")
    require(candidate.is_file(), "Missing customer artifact: " + value)
    return candidate


def load(name):
    return json.loads((PACKAGE / name).read_text(encoding="utf-8"))


def validate():
    coverage = load("coverage.json")
    require(set(coverage) == {"schema_version", "evidence", "customer", "rules", "limitations"}
            and coverage["schema_version"] == "1.0"
            and coverage["evidence"] == "versioned-definition-summary"
            and coverage["customer"] == "Atlas Financial",
            "Invalid coverage inventory contract")
    rules = coverage["rules"]
    require(isinstance(rules, list) and len(rules) == 12
            and {row["id"] for row in rules} == RULE_IDS,
            "Coverage must contain twelve unique reviewed rule IDs")
    for row in rules:
        key = row["id"]
        require(set(row) == {"id", "title", "source", "enabled", "severity", "tactics",
                            "techniques", "schedule", "lookback", "incident_creation",
                            "definition_path", "query_path", "runbook_path"},
                "Unrecognized detection coverage field")
        require(row["definition_path"] == f"detections/azure/{key}.json"
                and row["query_path"] == f"detections/azure/{key}.kql"
                and row["runbook_path"] == f"docs/detections/{key}.md",
                "Detection path does not match its reviewed ID")
        props = json.loads(existing_path(row["definition_path"]).read_text(encoding="utf-8"))["properties"]
        existing_path(row["query_path"])
        existing_path(row["runbook_path"])
        require(row["source"] == "AzureActivity" and row["enabled"] is False
                and props["enabled"] is False and row["incident_creation"] is False
                and props["incidentConfiguration"]["createIncident"] is False,
                "Customer coverage cannot imply active detection or incident creation")
        expected = dict(title=props["displayName"], severity=props["severity"],
                        tactics=props["tactics"], techniques=props["techniques"],
                        schedule=props["queryFrequency"], lookback=props["queryPeriod"])
        require(all(row[name] == value for name, value in expected.items()),
                key + ": customer coverage disagrees with the versioned definition")

    tickets = load("service-tickets.json")
    require(set(tickets) == {"schema_version", "evidence", "customer", "tickets"}
            and tickets["schema_version"] == "1.0"
            and tickets["evidence"] == "fictional-service-ticket-examples"
            and tickets["customer"] == "Atlas Financial", "Invalid service-ticket contract")
    rows = tickets["tickets"]
    require(isinstance(rows, list) and len(rows) == 8
            and len({row["id"] for row in rows}) == 8
            and {row["category"] for row in rows} == TICKET_CATEGORIES,
            "Eight distinct required service-ticket categories are required")
    for row in rows:
        require(set(row) == {"id", "category", "title", "evidence", "priority", "status",
                            "trigger", "investigation", "root_cause", "actions", "acceptance",
                            "closure_rationale", "limitations", "reference_paths"},
                "Unrecognized service-ticket field")
        require(row["evidence"] == "fictional-service-ticket"
                and row["status"] == "ClosedSynthetic"
                and row["priority"] in {"P1", "P2", "P3"},
                "Fictional tickets cannot imply a real serviced/closed incident")
        require(all(isinstance(row[name], str) and 20 <= len(row[name]) <= 1500
                    for name in ("trigger", "root_cause", "closure_rationale")),
                "Ticket needs a substantive trigger, root cause and closure")
        for field in ("investigation", "actions", "acceptance", "limitations"):
            require(isinstance(row[field], list) and 1 <= len(row[field]) <= 10
                    and all(isinstance(text, str) and 15 <= len(text) <= 1000 for text in row[field]),
                    "Ticket needs bounded substantive investigation/actions/evidence")
        require(isinstance(row["reference_paths"], list) and 1 <= len(row["reference_paths"]) <= 8,
                "Ticket needs implementation/evidence references")
        for path in row["reference_paths"]:
            existing_path(path)

    acceptance = load("acceptance.json")
    require(set(acceptance) == {"schema_version", "evidence", "customer", "deliverables",
                              "live_incident_gate", "operational_service_claim"}
            and acceptance["schema_version"] == "1.0"
            and acceptance["evidence"] == "fictional-customer-package-acceptance"
            and acceptance["customer"] == "Atlas Financial"
            and acceptance["operational_service_claim"] is False,
            "Customer package must not assert a production service")
    deliverables = acceptance["deliverables"]
    require(isinstance(deliverables, list) and len(deliverables) == 20
            and {row["id"] for row in deliverables} == DELIVERABLE_IDS,
            "Twenty customer deliverables must be mapped")
    for row in deliverables:
        require(set(row) == {"id", "state", "path", "acceptance"}
                and row["state"] == "implemented-offline"
                and isinstance(row["acceptance"], str) and len(row["acceptance"]) >= 20,
                "Invalid deliverable acceptance state")
        existing_path(row["path"])
    gate = acceptance["live_incident_gate"]
    require(set(gate) == {"state", "reason", "authoritative_status_path"}
            and gate["state"] == "not-asserted-by-this-package"
            and isinstance(gate["reason"], str) and len(gate["reason"]) >= 30,
            "An offline customer package cannot close actual incident acceptance")
    existing_path(gate["authoritative_status_path"])
    return {"evidence": "offline-customer-contract-validation", "rules": len(rules),
            "fictional_tickets": len(rows), "customer_deliverables": len(deliverables),
            "network_calls": 0, "azure_changes": 0, "production_service_claim": False,
            "live_incident_acceptance": "not-asserted-by-this-package"}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
