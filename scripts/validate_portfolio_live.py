"""Preview-first single aggregate runtime check for twelve fixed KQL definitions.

No deployment, ingestion, rule activation, RBAC change or arbitrary query input.
One consumed local attempt ledger prevents automatic retry after ambiguity.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request

from portfolio.catalog import SPECS, definition, validate as validate_portfolio
from scripts.azure_guard import RG, WORKSPACE, az_json, canonical_uuid
from scripts.prepare_portfolio import NoRedirect
from scripts.validate_detection import ROOT, require, validate_rule

PIN = ROOT / ".local/azure-target.json"
APPROVAL = ROOT / ".local/completion/live-kql-approved.private.json"
LEDGER = ROOT / ".local/completion/live-kql-attempt.private.json"
REPORT = ROOT / ".local/completion/live-kql.sanitized.json"
DETECTIONS = tuple(f"AZ-DET-{number:03}" for number in range(1, 13))
MAX_RESPONSE = 1_048_576
VERSION = "fixed-portfolio-live-kql-1.0"


class QueryFailure(ValueError):
    """Only bounded public error codes cross the CLI boundary."""

    def __init__(self, stage, codes=("RequestFailed",), status=None):
        self.stage, self.codes, self.status = stage, tuple(codes), status
        super().__init__(f"{stage} failed ({', '.join(self.codes)}); attempt is not replayed automatically")


def fixed_query():
    """Validate and wrap complete source KQL, including nested local let bodies."""
    rules = {key: validate_rule(detection=key) for key in DETECTIONS[:2]}
    validate_portfolio()
    rules.update({key: definition(key) for key in SPECS})
    require(set(rules) == set(DETECTIONS), "Exactly twelve fixed definitions required")
    functions, aggregates = [], []
    for number, key in enumerate(DETECTIONS, 1):
        body = rules[key]["properties"]["query"].strip().rstrip(";")
        require("AzureActivity" in body and "ago(1h)" in body, "Fixed one-hour AzureActivity definition required")
        functions.append(f"let F{number:03} = () {{\n{body}\n}};")
        aggregates.append(f'(F{number:03}() | summarize Matches=count() | extend DetectionId="{key}" | project DetectionId, Matches)')
    result = "\n".join(functions) + "\nunion\n" + ",\n".join(aggregates) + "\n| project DetectionId, Matches\n"
    require(len(result.encode()) <= 100_000, "Fixed query exceeds the request bound")
    return result


def query_fingerprint():
    body = {"version": VERSION, "timespan": "PT1H", "query": fixed_query()}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def error_codes(payload):
    codes = []
    current = payload.get("error", {}) if isinstance(payload, dict) else {}
    for _ in range(4):
        if not isinstance(current, dict):
            break
        candidate = current.get("code")
        if isinstance(candidate, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,80}", candidate) and candidate not in codes:
            codes.append(candidate)
        current = current.get("innererror", current.get("innerError"))
    return tuple(codes) or ("RequestFailed",)


def request_json(method, url, token, body=None, stage="Azure request"):
    """Fixed callers only; bounded response and timeout, redirects never followed."""
    request = urllib.request.Request(url, method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=60) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise QueryFailure(stage, ("ResponseTooLarge",))
            try:
                value = json.loads(raw)
            except (ValueError, UnicodeError):
                raise QueryFailure(stage, ("InvalidJSON",)) from None
            if not isinstance(value, dict) or value.get("error"):
                raise QueryFailure(stage, error_codes(value))
            return value
    except urllib.error.HTTPError as exc:
        try:
            codes = error_codes(json.loads(exc.read(min(MAX_RESPONSE, 65536))))
        except (ValueError, UnicodeError, OSError):
            codes = ("RequestFailed",)
        raise QueryFailure(stage, codes, exc.code) from None
    except (urllib.error.URLError, OSError, TimeoutError):
        raise QueryFailure(stage, ("TransportError",)) from None


def aggregate_result(value):
    require(isinstance(value, dict) and set(value) == {"tables"}, "Complete aggregate-only response required")
    tables = value["tables"]
    require(isinstance(tables, list) and len(tables) == 1, "One aggregate table required")
    table = tables[0]
    require(isinstance(table, dict) and set(table) == {"name", "columns", "rows"}, "Unexpected aggregate table shape")
    require(table["name"] == "PrimaryResult", "Unexpected aggregate table")
    columns = table["columns"]
    require(columns == [{"name": "DetectionId", "type": "string"}, {"name": "Matches", "type": "long"}], "Only DetectionId and integer Matches may be returned")
    rows = table["rows"]
    require(isinstance(rows, list) and len(rows) == len(DETECTIONS), "Exactly twelve aggregate rows required")
    result = {}
    for row in rows:
        require(isinstance(row, list) and len(row) == 2 and isinstance(row[0], str), "Invalid aggregate row")
        key, count = row
        require(key in DETECTIONS and key not in result, "Unknown or duplicated detection aggregate")
        require(type(count) is int and 0 <= count <= 2**63 - 1, "Nonnegative aggregate count required")
        result[key] = count
    require(set(result) == set(DETECTIONS), "Missing fixed detection aggregate")
    return {key: result[key] for key in DETECTIONS}


def safe_az(*args):
    try:
        return az_json(*args)
    except (ValueError, OSError, subprocess.SubprocessError):
        # The shared CLI may include sanitized Azure message text. This command
        # deliberately returns only a generic code, never that telemetry/context.
        raise QueryFailure("Azure authentication/context", ("AzureCLIError",)) from None


def _git_clean_main():
    try:
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=10).stdout.strip()
        changes = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        raise ValueError("Reviewed clean main could not be verified") from None
    require(branch == "main" and not changes, "Reviewed clean merged main required")


def run(apply=False):
    query = fixed_query()
    fingerprint = query_fingerprint()
    if not apply:
        return {"evidence": "offline-preview", "query_sha256": fingerprint, "fixed_detections": list(DETECTIONS),
                "timespan": "PT1H", "planned_log_queries": 1, "network_requests": 0,
                "resource_changes": 0, "raw_events_returned": 0}
    require(os.environ.get("GITHUB_ACTIONS") != "true", "Personal opt-in verification only; no CI query workflow authorized")
    _git_clean_main()
    require(not LEDGER.exists(), "Aggregate already attempted; preserve ledger and do not replay")
    require(APPROVAL.stat().st_size <= 8192, "Approval record exceeds the bound")
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    require(isinstance(approval, dict) and approval.get("sha256") == fingerprint and approval.get("allow_one_aggregate_query") is True, "Exact one-query approval required before authentication")
    require(PIN.stat().st_size <= 8192, "Pinned target exceeds the bound")
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    require(isinstance(pin, dict) and set(pin) == {"subscription_id", "tenant_id"}, "Existing target pin required")
    subscription, tenant = canonical_uuid(pin["subscription_id"]), canonical_uuid(pin["tenant_id"])
    account = safe_az("account", "show")
    require(account.get("id", "").lower() == subscription and account.get("tenantId", "").lower() == tenant and account.get("user", {}).get("type") == "user", "Pinned personal verification session required; never switch or upgrade")
    arm_token = safe_az("account", "get-access-token", "--scope", "https://management.core.windows.net//.default")["accessToken"]
    workspace_id = f"/subscriptions/{subscription}/resourceGroups/{RG}/providers/Microsoft.OperationalInsights/workspaces/{WORKSPACE}"
    metadata = request_json("GET", "https://management.azure.com" + workspace_id + "?api-version=2025-02-01", arm_token, stage="Workspace metadata")
    require(metadata.get("id", "").lower() == workspace_id.lower() and metadata.get("location") == "westeurope", "Independent workspace metadata mismatch")
    customer = canonical_uuid(metadata.get("properties", {}).get("customerId"))
    token = safe_az("account", "get-access-token", "--resource", "https://api.loganalytics.io")["accessToken"]
    ledger = {"evidence": "local-single-query-ledger", "query_sha256": fingerprint,
              "started_utc": datetime.now(timezone.utc).isoformat(), "query_attempts": 1,
              "timespan": "PT1H", "completed": False, "automatic_replay_allowed": False}
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    # Claim atomically before POST. A disconnect, partial result or process
    # interruption must never turn into an automatic second query.
    with LEDGER.open("x", encoding="utf-8") as stream:
        json.dump(ledger, stream, indent=2)
    try:
        response = request_json("POST", f"https://api.loganalytics.azure.com/v1/workspaces/{customer}/query", token,
                                {"query": query, "timespan": "PT1H"}, stage="Portfolio aggregate query")
        counts = aggregate_result(response)
    except (ValueError, OSError, TypeError, KeyError):
        ledger["outcome"] = "failed-or-ambiguous; do not replay"
        LEDGER.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        raise
    observed = datetime.now(timezone.utc).isoformat()
    report = {"evidence": "actual-log-analytics-aggregate", "observed_utc": observed,
              "query_sha256": fingerprint, "timespan": "PT1H", "query_attempts": 1,
              "detections_validated": len(counts), "matches": counts, "kusto_executed": True,
              "raw_events_returned": 0, "resource_changes": 0, "measured_false_positive_rate": None,
              "limitations": ["Zero matches is valid inactivity, not a measured true-negative rate.",
                              "Compilation and aggregate execution do not verify scheduled rule alerts or incident creation.",
                              "The one-hour sample cannot establish production detection accuracy."]}
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    ledger.update(completed=True, completed_utc=observed, outcome="validated-twelve-fixed-aggregates")
    LEDGER.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.apply), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except QueryFailure as exc:
        raise SystemExit(str(exc)) from None
    except (ValueError, OSError, TypeError, KeyError, subprocess.SubprocessError):
        raise SystemExit("Portfolio KQL validation stopped: invalid contract, pin, approval or state; no automatic query replay") from None
