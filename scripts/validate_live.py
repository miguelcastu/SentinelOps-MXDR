"""Opt-in Kusto execution: aggregate-only real-data and synthetic checks."""
import json
import os
import tempfile
from pathlib import Path

from scripts.azure_guard import az_json, canonical_uuid, context
from scripts.validate_detection import KQL, ROOT, require, validate_rule

HEALTH_QUERY = """AzureActivity
| where TimeGenerated between (ago(1h) .. now())
| summarize TotalEvents=count(), DiagnosticChanges=countif(OperationNameValue in~ ("Microsoft.Insights/diagnosticSettings/write", "Microsoft.Insights/diagnosticSettings/delete") and ActivityStatusValue in~ ("Success", "Succeeded"))
"""


def synthetic_query():
    fixtures = json.loads((ROOT / "tests/fixtures/az_det_001.json").read_text(encoding="utf-8"))
    rows = []
    expected = []
    for case in fixtures:
        # JSON string quoting is valid for these fixed synthetic KQL strings.
        rows.append(", ".join((str(case["offset"]), json.dumps(case["operation"]),
                               json.dumps(case["status"]), json.dumps(case["id"]),
                               json.dumps(case.get("ip", "")))))
        if case["expected"]:
            expected.append(json.dumps(case["id"]) + ", " + json.dumps(case.get("expected_ip", "")))
    source = ("datatable(OffsetSeconds:long, OperationNameValue:string, ActivityStatusValue:string, EventDataId:string, CallerIpAddress:string)[\n" +
              ",\n".join(rows) + "\n]\n" +
              '| extend TimeGenerated = now() + OffsetSeconds * 1s, Caller = "", ResourceId = "", _ResourceId = "", ResourceGroup = "", CorrelationId = ""\n')
    body = KQL.read_text(encoding="utf-8").split("\n", 1)[1].strip()
    return ("let Actual = " + source + body + ";\n" +
            "let Expected = datatable(EventDataId:string, SourceIPAddress:string)[" + ", ".join(expected) + "];\n" +
            "union (Actual | project EventDataId, SourceIPAddress | join kind=leftanti Expected on EventDataId, SourceIPAddress), " +
            "(Expected | join kind=leftanti (Actual | project EventDataId, SourceIPAddress) on EventDataId, SourceIPAddress)\n" +
            "| summarize Mismatches=count()")


def aggregate_result(response, names):
    require(not response.get("error"), "Logs API returned an error or partial result")
    tables = response.get("tables", [])
    require(len(tables) == 1, "Unexpected Logs API tables")
    table = tables[0]
    require([column.get("name") for column in table.get("columns", [])] == names,
            "Unexpected result columns; refusing to print telemetry")
    rows = table.get("rows", [])
    require(len(rows) == 1 and len(rows[0]) == len(names), "Expected one aggregate row")
    require(all(type(value) is int and value >= 0 for value in rows[0]), "Expected nonnegative aggregate integers")
    return dict(zip(names, rows[0]))


def live():
    validate_rule()
    require(os.environ.get("SENTINEL_LIVE_VALIDATION_APPROVED") == "true", "Live validation requires operator cost review")
    workspace_id = context("validate-kql.yml")
    workspace = az_json("rest", "--method", "get", "--url", f"https://management.azure.com{workspace_id}?api-version=2025-02-01")
    require(workspace.get("id", "").lower() == workspace_id.lower(), "Workspace ID mismatch")
    require(workspace.get("location", "").lower() == "westeurope", "Workspace location mismatch")
    customer_id = canonical_uuid(workspace.get("properties", {}).get("customerId", ""))
    # Use the documented CLI Logs endpoint and audience, with no CLI extension.
    endpoint = "https://api.loganalytics.io"
    url = f"{endpoint}/v1/workspaces/{customer_id}/query"
    for query, names in ((HEALTH_QUERY, ["TotalEvents", "DiagnosticChanges"]),
                         (synthetic_query(), ["Mismatches"])):
        with tempfile.TemporaryDirectory(prefix="sentinelops-query-") as directory:
            body = Path(directory) / "aggregate-query.json"
            body.write_text(json.dumps({"query": query, "timespan": "PT1H"}), encoding="utf-8")
            response = az_json("rest", "--method", "post", "--url", url,
                               "--resource", endpoint, "--headers", "Content-Type=application/json",
                               "--body", "@" + str(body))
        values = aggregate_result(response, names)
        require(values.get("Mismatches", 0) == 0, "Synthetic Kusto fixture mismatch")
        print(json.dumps(values, sort_keys=True))
    print("PASS: real AzureActivity aggregate and synthetic Kusto checks; zero events is valid lab inactivity")


if __name__ == "__main__":
    try:
        live()
    except (ValueError, OSError, TimeoutError) as exc:
        raise SystemExit(f"Live validation stopped: {exc}") from None
