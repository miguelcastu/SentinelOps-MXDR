"""Approved one-time administrative connection of the existing owned guest.

Default preview. Credentials travel only over the dedicated SSH channel into a
root-only /run temporary JSON, removed in finally. No token in argv or output.
No tenant join, application registration, service-principal secret or OIDC change.
"""
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone

from ama.cloud import ARC_API, Client, contract, fingerprint
from scripts.azure_guard import az_json, canonical_uuid
from scripts.bootstrap_oidc import PIN
from scripts.prepare_local_ama_vm import BASE, ROOT
from scripts.verify_local_ama_vm import main as verify_guest
from scripts.validate_detection import require


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print("Arc connection plan: one owned local guest in the existing pinned subscription; no AMA or log sender", flush=True)
    if not args.apply:
        print("PREVIEW ONLY: no SSH or Azure request")
        return
    require(os.environ.get("GITHUB_ACTIONS") != "true", "Local administrative connection cannot run in CI")
    require(subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() == "main", "Reviewed merged main required")
    approved = json.loads((ROOT / ".local/ama/rollout-approved.json").read_text())
    require(approved.get("sha256") == fingerprint(), "Current one-machine rollout approval required")
    pin = json.loads(PIN.read_text())
    subscription, tenant = canonical_uuid(pin["subscription_id"]), canonical_uuid(pin["tenant_id"])
    account = az_json("account", "show")
    require(account.get("id", "").lower() == subscription and account.get("tenantId", "").lower() == tenant and account.get("user", {}).get("type") == "user", "Pinned administrative MFA account required; no account switch")
    guest = verify_guest()
    require(guest["arc_installed"] and not guest["ama_active"], "Prepared owned guest required")
    workspace = f"/subscriptions/{subscription}/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
    spec = contract(workspace)
    client = Client()
    before = client.request("GET", spec["machine_id"] + "?api-version=" + ARC_API, missing_ok=True)
    if before is not None:
        raise ValueError("Arc resource already exists; independently verify its guest identity; no automatic reconnect")
    require(guest.get("arc_status") == "Disconnected", "Guest must be unregistered and disconnected")
    config = {"access-token": client.token, "subscription-id": subscription, "tenant-id": tenant,
              "resource-group": "rg-sentinelops-mxdr", "resource-name": "lab-sentinelops-linux-01",
              "location": "westeurope", "cloud": "AzureCloud", "tags": "Project=SentinelOps,Source=ama-linux-syslog"}
    probe = r'''
import json, pathlib, re, socket, subprocess, tempfile
if socket.gethostname() != "lab-sentinelops-linux-01":
    raise SystemExit("Unexpected guest")
old = subprocess.run(["azcmagent", "show", "--json"], capture_output=True, text=True, check=True)
if json.loads(old.stdout).get("status") != "Disconnected":
    raise SystemExit("Guest already connected or ambiguous")
with tempfile.NamedTemporaryFile(mode="w", prefix="sentinelops-arc-", suffix=".json", dir="/run", delete=False) as stream:
    json.dump(config, stream)
    target = pathlib.Path(stream.name)
try:
    result = subprocess.run(["azcmagent", "connect", "--config", str(target)], capture_output=True, text=True, timeout=240)
    if result.returncode:
        code = re.search(r"AZCM[0-9]{4}", result.stdout + result.stderr)
        print(json.dumps({"connected": False, "error_code": code.group() if code else "ArcConnectFailed"}))
        raise SystemExit(1)
    current = subprocess.run(["azcmagent", "show", "--json"], capture_output=True, text=True, check=True)
    print(json.dumps({"connected": json.loads(current.stdout).get("status") == "Connected"}))
finally:
    target.unlink(missing_ok=True)
'''
    program = "config = " + repr(config) + "\n" + probe
    result = subprocess.run(["ssh", "-i", str(BASE / "id_ed25519"), "-p", "22221", "-o", "BatchMode=yes",
                             "-o", "StrictHostKeyChecking=yes", "-o", "UserKnownHostsFile=" + str(BASE / "known_hosts"),
                             "labops@127.0.0.1", "sudo python3 -"], input=program.encode(), capture_output=True, timeout=280)
    if result.returncode:
        try:
            code = json.loads(result.stdout).get("error_code", "ArcConnectFailed")
        except ValueError:
            code = "ArcConnectFailed"
        raise ValueError("Arc connect stopped (" + code + "); raw output and credentials suppressed; no automatic retry")
    require(json.loads(result.stdout).get("connected") is True, "Arc agent did not confirm connection")
    current = client.request("GET", spec["machine_id"] + "?api-version=" + ARC_API)
    require(current.get("id", "").lower() == spec["machine_id"].lower() and current.get("location") == "westeurope" and current.get("properties", {}).get("status") == "Connected", "Actual Azure Arc read-back failed")
    (ROOT / ".local/ama/arc-resource.private.json").write_text(json.dumps(current, indent=2))
    report = {"evidence": "actual-arc-agent-and-azure-rest", "machine": "lab-sentinelops-linux-01", "connected": True,
              "verified_utc": datetime.now(timezone.utc).isoformat(), "ama_installed": False, "messages_sent": 0}
    (ROOT / ".local/ama/arc-onboarding.sanitized.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from None
