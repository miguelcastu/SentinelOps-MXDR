"""Install only the reviewed Arc package inside the owned local guest.

Preview by default. Never runs azcmagent connect, authenticates to Azure,
registers a provider or installs AMA. The installer is Microsoft's published
Linux package installer, pinned to the bytes reviewed for this lab increment.
"""
import argparse
import hashlib
import subprocess
import urllib.parse
import urllib.request

from scripts.prepare_local_ama_vm import BASE
from scripts.verify_local_ama_vm import main as verify_guest

INSTALLER_URL = "https://aka.ms/azcmagent"
INSTALLER_SHA256 = "a41c8b0626e41aac6c51a9c01a0c35e87cedc77bdd38155a416b1a49bf1e9101"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print("Local package only: install Arc in the dedicated Ubuntu guest; no connect, AMA or Azure authentication.", flush=True)
    if not args.apply:
        print("PREVIEW ONLY: no network request")
        return
    guest = verify_guest()
    if guest["arc_installed"]:
        if guest.get("arc_status") != "Disconnected":
            raise ValueError("Arc is connected or ambiguous; local preparation must not modify it")
        print("Arc package already installed and disconnected; no reinstall or download")
        return
    if guest["ama_active"]:
        raise ValueError("AMA is active; local preparation cannot modify a collecting guest")
    with urllib.request.urlopen(INSTALLER_URL, timeout=45) as response:
        origin = urllib.parse.urlparse(response.url)
        if origin.scheme != "https" or origin.hostname not in {"gbl.his.arc.azure.com", "download.microsoft.com", "packages.microsoft.com"}:
            raise ValueError("Unexpected final installer origin")
        content = response.read(1_000_000)
    if hashlib.sha256(content).hexdigest() != INSTALLER_SHA256:
        raise ValueError("Microsoft installer changed; review before updating the pinned hash")
    (BASE / "Install_linux_azcmagent.sh").write_bytes(content)
    result = subprocess.run(["ssh", "-i", str(BASE / "id_ed25519"), "-p", "22221",
                             "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                             "-o", "StrictHostKeyChecking=yes",
                             "-o", "UserKnownHostsFile=" + str(BASE / "known_hosts"),
                             "labops@127.0.0.1", "sudo bash -s --"],
                            input=content, capture_output=True, timeout=600)
    (BASE / "arc-install.private.log").write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise ValueError("Local Arc package install failed; inspect the ignored private log; no automatic retry")
    verify_guest()
    print("Local package installed. Azure connection and AMA collection remain pending.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from None
