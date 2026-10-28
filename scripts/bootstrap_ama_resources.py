"""PROPOSAL: one-time fixed-resource initialization, separately approval-gated.

The original pilot approval did not allow personal DCR/extension deployment.
This alternative remains unavailable without an explicit additional approval
record. It avoids granting the CI identity resource-group write permission.
Routine configuration/verification remains merged-main OIDC.
"""
import argparse
import json
import os
import subprocess

from ama.cloud import Client, fingerprint
from scripts.azure_guard import az_json, canonical_uuid
from scripts.bootstrap_oidc import PIN
from scripts.deploy_ama_pilot import configure
from scripts.prepare_local_ama_vm import ROOT
from scripts.validate_detection import require


def bootstrap(apply=False):
    print("One-time bootstrap proposal: only the reviewed DCR, AMA extension and association; no broader CI role, query or sender")
    if not apply:
        print("PREVIEW ONLY: additional operator approval required; zero network requests")
        return
    # Fail before authentication/network when this extra exception is absent.
    approved = json.loads((ROOT / ".local/ama/one-time-bootstrap-approved.json").read_text())
    require(approved.get("allow_one_time_personal_bootstrap") is True and approved.get("sha256") == fingerprint(), "Explicit one-time personal initialization approval is missing")
    require(os.environ.get("GITHUB_ACTIONS") != "true", "One-time local administrative exception cannot run in CI")
    require(subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() == "main", "Reviewed merged main required")
    ledger = ROOT / ".local/ama/resource-bootstrap.private.json"
    if ledger.exists():
        prior = json.loads(ledger.read_text())
        require(prior.get("sha256") == fingerprint(), "Bootstrap ledger contract mismatch")
        require(not prior.get("completed"), "One-time initialization already completed; use OIDC for future verification")
    pin = json.loads(PIN.read_text())
    subscription, tenant = canonical_uuid(pin["subscription_id"]), canonical_uuid(pin["tenant_id"])
    account = az_json("account", "show")
    require(account.get("id", "").lower() == subscription and account.get("tenantId", "").lower() == tenant and account.get("user", {}).get("type") == "user", "Pinned administrative MFA session required; never switch subscription")
    workspace = f"/subscriptions/{subscription}/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
    ledger.write_text(json.dumps({"sha256": fingerprint(), "completed": False}))
    report = configure(Client(), workspace, auth_mode="one-time-personal-bootstrap")
    ledger.write_text(json.dumps({"sha256": fingerprint(), "completed": True, "report": report}, indent=2))
    (ROOT / ".local/ama/resource-bootstrap.sanitized.json").write_text(json.dumps(report, indent=2) + "\n")
    print("AMA_BOOTSTRAP_EVIDENCE=" + json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    try:
        bootstrap(parser.parse_args().apply)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit("One-time initialization stopped: " + str(exc) + "; no broader role or automatic sender") from None
