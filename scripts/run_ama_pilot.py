"""One approved ten-message AMA pilot and bounded aggregate-only verification.

Preview by default. A persistent local attempt ledger blocks automatic replay.
Does not alter DCRs, agents, Azure permissions, workspace settings or rules.
"""
import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

from ama.cloud import ARC_API, MONITOR_API, Client, contract, fingerprint, matches
from ama.pilot import messages
from scripts.azure_guard import az_json
from scripts.bootstrap_oidc import PIN
from scripts.prepare_local_ama_vm import ROOT, BASE
from scripts.prepare_portfolio import NoRedirect
from scripts.validate_detection import require
from scripts.verify_local_ama_vm import main as verify_guest

LEDGER = ROOT / ".local/ama/cloud-pilot-ledger.private.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        print("PREVIEW ONLY: one ten-message batch, <=4096 payload bytes; at most three one-hour aggregate queries; no network")
        return
    require(os.environ.get("GITHUB_ACTIONS") != "true", "No cloud sender workflow is authorized")
    require(subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() == "main", "Reviewed merged main required")
    require(not LEDGER.exists(), "Pilot already attempted; no automatic resend, ledger reset or second batch")
    approved = json.loads((ROOT / ".local/ama/rollout-approved.json").read_text())
    require(approved.get("sha256") == fingerprint(), "Exact pilot approval required")
    pin = json.loads(PIN.read_text())
    account = az_json("account", "show")
    require(account.get("id", "").lower() == pin["subscription_id"].lower() and account.get("tenantId", "").lower() == pin["tenant_id"].lower() and account.get("user", {}).get("type") == "user", "Pinned verification session required; never switch account")
    guest = verify_guest()
    require(guest.get("arc_status") == "Connected" and guest["ama_active"], "Connected guest and active AMA required")
    workspace = f"/subscriptions/{pin['subscription_id']}/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
    spec = contract(workspace)
    arm = Client()
    metadata = arm.request("GET", workspace + "?api-version=2025-02-01")
    for kind in ("dcr", "extension", "association"):
        value = arm.request("GET", spec[kind + "_id"] + "?api-version=" + (ARC_API if kind == "extension" else MONITOR_API))
        require(matches(value, spec[kind], spec[kind + "_id"], kind, metadata["properties"].get("customerId")), "Live pilot configuration drift")
    associations = arm.request("GET", spec["machine_id"] + "/providers/Microsoft.Insights/dataCollectionRuleAssociations?api-version=" + MONITOR_API)
    require(not associations.get("nextLink") and len(associations.get("value", [])) == 1, "Exactly one DCR association required")
    # Obtain query authorization before consuming the single sending attempt.
    log_token = az_json("account", "get-access-token", "--resource", "https://api.loganalytics.io")["accessToken"]
    run_id = "cloud-" + uuid.uuid4().hex
    batch = messages(run_id)
    record = {"run_id": run_id, "started_utc": datetime.now(timezone.utc).isoformat(), "attempted": True,
              "expected_messages": 10, "payload_bytes": sum(len((m + "\n").encode()) for m in batch), "query_attempts": 0}
    # Claim before the SSH call; an ambiguous disconnect cannot cause a replay.
    with LEDGER.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
    probe = r'''
import json, pathlib, socket, subprocess
if socket.gethostname() != "lab-sentinelops-linux-01":
    raise SystemExit("Unexpected guest")
arc = subprocess.run(["azcmagent", "show", "--json"], capture_output=True, text=True, check=True)
if json.loads(arc.stdout).get("resourceId", "").lower() != expected_machine.lower():
    raise SystemExit("Guest Arc resource does not match approved machine")
if subprocess.run(["systemctl", "is-active", "--quiet", "azuremonitoragent"]).returncode:
    raise SystemExit("AMA inactive")
cache = pathlib.Path("/etc/opt/microsoft/azuremonitoragent/config-cache")
config_ready = any("local4" in p.read_text(errors="ignore") for p in cache.rglob("*") if p.is_file() and p.stat().st_size < 1000000)
if not config_ready:
    raise SystemExit("AMA has not downloaded the local4 DCR; no messages sent")
for message in batch:
    subprocess.run(["logger", "--priority", "local4.warning", "--tag", "sentinelops-lab", "--", message], check=True, timeout=10)
print(json.dumps({"messages_sent": len(batch), "dcr_downloaded": True}))
'''
    program = "batch = " + repr(batch) + "\nexpected_machine = " + repr(spec["machine_id"]) + "\n" + probe
    sent = subprocess.run(["ssh", "-i", str(BASE / "id_ed25519"), "-p", "22221", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                           "-o", "UserKnownHostsFile=" + str(BASE / "known_hosts"), "labops@127.0.0.1", "sudo python3 -"], input=program.encode(), capture_output=True, timeout=60)
    require(sent.returncode == 0, "Pilot sending failed or was ambiguous; no automatic resend; inspect local agent configuration")
    require(json.loads(sent.stdout).get("messages_sent") == 10, "Pilot count mismatch; no resend")
    print("AMA pilot: ten messages sent once; waiting for aggregate destination evidence", flush=True)
    query = (ROOT / "ama/validation.kql").read_text().replace("<EXACT_ARC_MACHINE_RESOURCE_ID>", spec["machine_id"]).replace("<EXACT_PILOT_RUN_ID>", run_id)
    endpoint = "https://api.loganalytics.azure.com/v1/workspaces/" + metadata["properties"]["customerId"] + "/query"
    report = None
    for attempt in range(3):
        # Long waits use short sleeps and are interruptible by the parent process.
        print("AMA pilot: bounded wait for ingestion; no messages resent", flush=True)
        for interval in range(12 if attempt == 0 else 18):
            time.sleep(10)
            if interval % 6 == 5:
                print("AMA pilot: waiting for the approved aggregate check; no new batch", flush=True)
        record["query_attempts"] += 1
        LEDGER.write_text(json.dumps(record, indent=2))
        request = urllib.request.Request(endpoint, method="POST", data=json.dumps({"query": query, "timespan": "PT1H"}).encode(),
                    headers={"Authorization": "Bearer " + log_token, "Content-Type": "application/json"})
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=60) as response:
                value = json.loads(response.read(131072))
        except urllib.error.HTTPError as exc:
            code = "LogQueryError"
            missing_table = False
            try:
                error = json.loads(exc.read(65536)).get("error", {})
                candidate = error.get("code", "")
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,80}", candidate):
                    code = candidate
                # A new standard table can become queryable after the first
                # arrival. Retrying only this known transient uses the same
                # three-attempt query allowance and never resends messages.
                detail = json.dumps(error)
                missing_table = exc.code == 400 and "Failed to resolve" in detail and "Syslog" in detail
            except (ValueError, AttributeError):
                pass
            if missing_table:
                print("AMA pilot: Syslog table not queryable yet; within the bounded query allowance", flush=True)
                continue
            raise ValueError(f"Aggregate query failed (HTTP {exc.code}, {code}); no raw response, permission fallback or resend") from None
        require(not value.get("error") and len(value.get("tables", [])) == 1, "Complete single aggregate result required")
        table = value["tables"][0]
        require([c["name"] for c in table["columns"]] == ["Events", "UniqueEvents", "LastSeen", "BillableBytes"] and len(table["rows"]) == 1, "Unexpected query shape; do not print telemetry")
        row = table["rows"][0]
        report = {"evidence": "actual-log-analytics-aggregate", "observed_utc": datetime.now(timezone.utc).isoformat(),
                  "events": row[0], "unique_events": row[1], "last_seen": row[2], "billable_bytes": row[3], "messages_sent": 10,
                  "payload_bytes": record["payload_bytes"], "query_attempts": record["query_attempts"], "raw_events_returned": 0,
                  "reconciled": row[0] == 10 and row[1] == 10, "kusto_executed": True}
        (ROOT / ".local/ama/ingestion.sanitized.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report), flush=True)
        require(row[0] <= 10 and row[1] <= 10, "Unexpected duplicate pilot events; stop without another batch")
        if report["reconciled"]:
            return
    raise ValueError("Pilot not yet reconciled after three aggregate queries; no automatic resend or additional queries")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from None
