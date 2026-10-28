"""One bounded local rsyslog test, refusing cloud-connected/AMA-installed guests.

Preview only by default. This is evidence for the local collection layer,
never AMA transport or Kusto execution. No Azure credentials are used.
"""
import argparse
import json
import subprocess
import uuid
from datetime import datetime, timezone

from ama.pilot import messages
from ama.plan import MACHINE
from scripts.prepare_local_ama_vm import BASE, ROOT
from scripts.verify_local_ama_vm import main as verify_guest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        print("PREVIEW ONLY: ten local labeled messages; no SSH or Azure request")
        return
    verify_guest()
    run_id = "local-" + uuid.uuid4().hex
    batch = messages(run_id)
    # The payload is data serialized into a Python literal. SSH receives a fixed
    # interpreter command, with no generated shell text or command substitution.
    probe = r'''
import json, pathlib, socket, subprocess, time
if socket.gethostname() != "lab-sentinelops-linux-01":
    raise SystemExit("Unexpected guest")
unit = subprocess.run(["systemctl", "list-unit-files", "azuremonitoragent.service", "--no-legend"], capture_output=True, text=True)
if unit.returncode not in (0, 1):
    raise SystemExit("Cannot determine AMA unit state")
if pathlib.Path("/opt/microsoft/azuremonitoragent").exists() or "azuremonitoragent" in unit.stdout:
    raise SystemExit("AMA is installed; local-only test is prohibited")
if pathlib.Path("/opt/azcmagent/bin/azcmagent").exists():
    arc = subprocess.run(["azcmagent", "show", "--json"], capture_output=True, text=True, check=True)
    if json.loads(arc.stdout).get("status") != "Disconnected":
        raise SystemExit("Arc is connected or ambiguous; local-only test is prohibited")
existing = pathlib.Path("/var/log/syslog")
if not existing.exists():
    raise SystemExit("Expected local syslog file is absent")
if any(message in existing.read_text() for message in batch):
    raise SystemExit("Run ID already present; no replay")
for message in batch:
    subprocess.run(["logger", "--priority", "local4.warning", "--tag", "sentinelops-lab", "--", message], check=True, timeout=10)
for attempt in range(5):
    lines = existing.read_text().splitlines()
    counts = [sum(message in line for line in lines) for message in batch]
    if counts == [1] * 10:
        break
    time.sleep(1)
print(json.dumps({"events": sum(counts), "unique_events": sum(count > 0 for count in counts), "reconciled": counts == [1] * 10}))
'''
    probe = "batch = " + repr(batch) + "\n" + probe
    result = subprocess.run(["ssh", "-i", str(BASE / "id_ed25519"), "-p", "22221",
                             "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                             "-o", "StrictHostKeyChecking=yes",
                             "-o", "UserKnownHostsFile=" + str(BASE / "known_hosts"),
                             "labops@127.0.0.1", "sudo python3 -"], input=probe,
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        (BASE / "local-syslog-error.private.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        raise ValueError("Local test failed; inspect ignored private diagnostics; no automatic resend")
    data = json.loads(result.stdout)
    data.update({"evidence": "actual-local-rsyslog-only", "machine": MACHINE,
                 "verified_utc": datetime.now(timezone.utc).isoformat(), "facility": "local4",
                 "severity": "warning", "payload_bytes": sum(len((m + "\n").encode()) for m in batch),
                 "azure_requests": 0, "ama_transport_verified": False, "kusto_executed": False})
    (ROOT / ".local/ama/local-syslog.sanitized.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data))
    if not data["reconciled"]:
        raise ValueError("Local message counts do not reconcile; no automatic resend")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from None
