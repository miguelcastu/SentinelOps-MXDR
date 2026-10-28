"""Preview-first local VirtualBox VM. No Azure call or changes to other VMs.

Downloads an official Ubuntu OVA, checks its published SHA-256, and uses an
ephemeral pycdlib dependency to create NoCloud media. Requires --apply to create
the VM; --start is separate. No host hypervisor installation or reboot.
"""
import argparse
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

from ama.plan import MACHINE

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".local/ama-vm"
VBOX = Path(r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe")
IMAGE = "noble-server-cloudimg-amd64.ova"
ORIGIN = "https://cloud-images.ubuntu.com/noble/current/"


def run(*args, timeout=120):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        BASE.mkdir(parents=True, exist_ok=True)
        (BASE / "command-error.private.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        raise ValueError("Local command failed; inspect the ignored local diagnostic file")
    return result.stdout


def download():
    BASE.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(ORIGIN + "SHA256SUMS", timeout=60) as response:
        manifest = response.read(100_000).decode()
    matches = [line.split()[0] for line in manifest.splitlines() if line.split()[-1].lstrip("*") == IMAGE]
    if len(matches) != 1:
        raise ValueError("Official image hash is ambiguous")
    path = BASE / IMAGE
    if not path.exists():
        with urllib.request.urlopen(ORIGIN + IMAGE, timeout=60) as response, path.open("wb") as output:
            total = 0
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                total += len(chunk)
                if total % (64 * 1024 * 1024) == 0:
                    print(f"Ubuntu official image downloaded: {total // (1024 * 1024)} MiB", flush=True)
    with path.open("rb") as image_file:
        digest = hashlib.file_digest(image_file, "sha256").hexdigest()
    if digest != matches[0]:
        raise ValueError("Image checksum mismatch; do not import")
    (BASE / "image-receipt.json").write_text(json.dumps({"source": ORIGIN + IMAGE, "sha256": digest,
                                                    "bytes": path.stat().st_size}, indent=2) + "\n")
    return path


def seed():
    import pycdlib
    key = BASE / "id_ed25519"
    if not key.exists():
        run("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "sentinelops-local-lab", "-f", key)
        sid = run("powershell", "-NoProfile", "-Command", "[Security.Principal.WindowsIdentity]::GetCurrent().User.Value").strip()
        run("icacls", key, "/inheritance:r", "/grant:r", "*" + sid + ":F")
    public = key.with_suffix(".pub").read_text().strip()
    config = ("#cloud-config\nhostname: " + MACHINE + "\nmanage_etc_hosts: true\ntimezone: UTC\nssh_pwauth: false\ndisable_root: true\n"
              "users:\n  - name: labops\n    lock_passwd: true\n    shell: /bin/bash\n    sudo: ALL=(ALL) NOPASSWD:ALL\n    ssh_authorized_keys:\n      - " + public + "\n"
              "write_files:\n  - path: /etc/ssh/sshd_config.d/00-sentinelops-lab.conf\n    permissions: '0644'\n    content: |\n      PermitRootLogin no\n      PasswordAuthentication no\n      KbdInteractiveAuthentication no\n"
              "package_update: true\npackages:\n  - rsyslog\n  - curl\n  - wget\n  - gnupg\n  - ca-certificates\n  - openssh-server\n  - python3\nruncmd:\n  - [systemctl, reload, ssh]\n")
    (BASE / "user-data").write_text(config, encoding="utf-8", newline="\n")
    (BASE / "meta-data").write_text("instance-id: sentinelops-linux-lab-v1\nlocal-hostname: " + MACHINE + "\n", encoding="utf-8", newline="\n")
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, vol_ident="cidata", joliet=3, rock_ridge="1.09")
    for name, iso_name in (("user-data", "USERDATA.;1"), ("meta-data", "METADATA.;1")):
        iso.add_file(str(BASE / name), iso_path="/" + iso_name, joliet_path="/" + name, rr_name=name)
    iso.write(str(BASE / "seed.iso"))
    iso.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume only this stopped VM inside the dedicated workspace directory")
    args = parser.parse_args()
    print("Local VM plan: Ubuntu 24.04, 1 vCPU, 1536 MiB, NAT/loopback SSH, no shared folders, no Azure request.", flush=True)
    if not args.download and not args.apply:
        print("PREVIEW ONLY")
        return
    if not VBOX.exists():
        raise ValueError("Existing VirtualBox required; no installer is launched")
    image = download()
    if not args.apply:
        return
    existing = run(VBOX, "list", "vms")
    exists = any(line.startswith('"' + MACHINE + '" ') for line in existing.splitlines())
    if exists and not args.resume:
        raise ValueError("Target name already exists; inspect instead of modifying or recreating")
    if exists:
        info = run(VBOX, "showvminfo", MACHINE, "--machinereadable")
        fields = dict(line.split("=", 1) for line in info.splitlines() if "=" in line)
        config_path = Path(json.loads(fields["CfgFile"]))
        if not config_path.resolve().is_relative_to(BASE.resolve()) or fields.get("VMState") != '"poweroff"':
            raise ValueError("Resume requires this workspace's own stopped VM")
    seed()
    if not exists:
        run(VBOX, "import", image, "--options=importtovdi", "--vsys=0", "--vmname=" + MACHINE,
            "--basefolder=" + str(BASE), "--memory=1536", "--cpus=1", timeout=300)
    run(VBOX, "modifyvm", MACHINE, "--nic1", "nat",
        "--cpus", "1", "--ioapic", "on", "--x86-x2apic", "on", "--paravirt-provider", "kvm",
        "--clipboard-mode", "disabled", "--drag-and-drop", "disabled", "--vrde", "off", "--audio-enabled", "off")
    info = run(VBOX, "showvminfo", MACHINE, "--machinereadable")
    if 'Forwarding(0)="labssh,tcp,127.0.0.1,22221,,22"' not in info:
        run(VBOX, "modifyvm", MACHINE, "--natpf1", "labssh,tcp,127.0.0.1,22221,,22")
    controller = "IDE" if 'storagecontrollername0="IDE"' in info else "NoCloud"
    if controller == "NoCloud" and '="NoCloud"' not in info:
        run(VBOX, "storagectl", MACHINE, "--name", controller, "--add", "ide")
    run(VBOX, "storageattach", MACHINE, "--storagectl", controller, "--port", "0", "--device", "0",
        "--type", "dvddrive", "--medium", BASE / "seed.iso")
    receipt = {"evidence": "local-vm-created", "machine": MACHINE, "ram_mib": 1536, "vcpus": 1,
               "ssh": "127.0.0.1:22221", "cloud_connected": False, "azure_requests": 0, "started": False}
    if args.start:
        run(VBOX, "startvm", MACHINE, "--type", "headless")
        receipt["started"] = True
    (BASE / "vm-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from None
