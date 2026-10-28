"""Read-only SSH verification of the dedicated local guest; no Azure request.

Uses a dedicated known_hosts file and key. Never prints raw cloud-init logs,
host identifiers, IP addresses, SSH keys or telemetry. A stopped guest fails
verification instead of being automatically restarted.
"""
import json
import subprocess
from datetime import datetime, timezone

from ama.plan import MACHINE
from scripts.prepare_local_ama_vm import BASE, ROOT, VBOX, run

PROBE = r'''
import json, pathlib, platform, socket, subprocess
def command(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=20)
release = dict(line.split("=", 1) for line in pathlib.Path("/etc/os-release").read_text().splitlines() if "=" in line)
cloud = command("cloud-init", "status", "--format=json")
try:
    cloud_state = json.loads(cloud.stdout).get("status", "unknown")
except ValueError:
    cloud_state = "unknown"
data = {"machine": socket.gethostname(), "os": release.get("PRETTY_NAME", "").strip('"'),
        "architecture": platform.machine(), "cloud_init": cloud_state,
        "rsyslog_active": command("systemctl", "is-active", "--quiet", "rsyslog").returncode == 0,
        "ssh_active": command("systemctl", "is-active", "--quiet", "ssh").returncode == 0,
        "arc_installed": pathlib.Path("/opt/azcmagent/bin/azcmagent").exists(),
        "ama_active": command("systemctl", "is-active", "--quiet", "azuremonitoragent").returncode == 0,
        "root_free_mib": __import__("shutil").disk_usage("/").free // (1024*1024)}
policy = command("sudo", "-n", "/usr/sbin/sshd", "-T")
options = dict(line.split(None, 1) for line in policy.stdout.splitlines() if " " in line)
data["ssh_keys_only_no_root"] = (policy.returncode == 0 and
    all(options.get(key) == "no" for key in ("permitrootlogin", "passwordauthentication", "kbdinteractiveauthentication")))
if data["arc_installed"]:
    arc = command("sudo", "-n", "azcmagent", "show", "--json")
    try:
        details = json.loads(arc.stdout)
        state = details.get("status")
        data["arc_status"] = state if state in ("Connected", "Disconnected", "Connecting", "Expired") else "Unknown"
        data["arc_version"] = details.get("agentVersion", "Unknown")
    except ValueError:
        data["arc_status"] = "Unknown"
print(json.dumps(data))
'''


def main():
    info = run(VBOX, "showvminfo", MACHINE, "--machinereadable")
    fields = dict(line.split("=", 1) for line in info.splitlines() if "=" in line)
    from pathlib import Path
    if not Path(json.loads(fields["CfgFile"])).resolve().is_relative_to(BASE.resolve()):
        raise ValueError("Machine config is outside the dedicated local lab directory")
    if fields.get("VMState") != '"running"':
        raise ValueError("Dedicated guest is not running; no automatic start")
    result = subprocess.run(["ssh", "-i", str(BASE / "id_ed25519"), "-p", "22221",
                             "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                             "-o", "StrictHostKeyChecking=accept-new",
                             "-o", "UserKnownHostsFile=" + str(BASE / "known_hosts"),
                             "labops@127.0.0.1", "python3 -"], input=PROBE,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise ValueError("Guest SSH probe failed; raw output suppressed; inspect locally")
    data = json.loads(result.stdout)
    if data.get("machine") != MACHINE:
        raise ValueError("Guest identity does not match the dedicated lab machine")
    data.update({"evidence": "actual-local-guest-ssh", "verified_utc": datetime.now(timezone.utc).isoformat(),
                 "vcpus": int(fields["cpus"]), "ram_mib": int(fields["memory"]),
                 "azure_requests": 0, "cloud_ingestion_verified": False})
    output = ROOT / ".local/ama/guest-status.sanitized.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data))
    if data["cloud_init"] != "done" or not data["rsyslog_active"] or not data["ssh_active"] or not data["ssh_keys_only_no_root"]:
        raise ValueError("Guest preparation is not complete; no Azure acceptance is claimed")
    return data


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from None
