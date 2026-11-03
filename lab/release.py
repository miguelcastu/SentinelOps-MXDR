"""Portable local release packaging with an explicit source/demo allowlist."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from scripts.validate_detection import ROOT

SUFFIXES = {".py", ".json", ".md", ".kql", ".yml", ".yaml", ".bicep", ".bicepparam", ".toml"}
PUBLIC_IMAGES = {"evidence/completion/dashboard.synthetic.png"}
DEMO_FILES = {"index.html", "report.json", "ingestion/report.json", "detections/controls.synthetic.json",
              "health/report.json", "health/report.md", "health/dashboard.html", "risk/report.json",
              "risk/investigation.md", "risk/dashboard.html", "risk/dataset.synthetic.json",
              "soar/report.synthetic.json", "soar/cases.synthetic.json", "soar/audit.synthetic.json",
              "infrastructure/preview.synthetic.json"}


def bundle(output):
    output = Path(output).resolve()
    names = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True, timeout=20).stdout.decode("utf-8").split("\0")
    entries = {}
    for name in names:
        if not name:
            continue
        path = ROOT / name
        parts = Path(name).parts
        hidden_parent = any(p.startswith(".") for p in parts[:-1])
        approved_workflow = len(parts) == 3 and parts[:2] == (".github", "workflows") and path.suffix in {".yml", ".yaml"}
        if path.is_symlink() or not path.is_file() or hidden_parent and not approved_workflow or ".private." in name:
            continue
        if path.suffix not in SUFFIXES and name not in {"LICENSE", ".gitignore"} and name not in PUBLIC_IMAGES:
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(ROOT) or path.stat().st_size > 4_194_304:
            raise ValueError("Source archive boundary exceeded")
        entries["source/" + name] = path.read_bytes()
    for name in sorted(DEMO_FILES):
        path = output / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != output.parent):
            raise ValueError("Symlink in demo output is not permitted")
        if not path.is_file():
            raise ValueError("Expected generated demo file is missing")
        if not path.resolve().is_relative_to(output) or path.stat().st_size > 4_194_304:
            raise ValueError("Demo archive boundary exceeded")
        entries["demo/" + path.relative_to(output).as_posix()] = path.read_bytes()
    if sum(map(len, entries.values())) > 26_214_400:
        raise ValueError("Portable archive size exceeded")
    manifest = {"format": "sentinelops-portable-lab-1", "source": "git-tracked-text-only", "deployment_performed": False,
                "excluded": [".git", ".local private files", "credentials", "VM disks", "SQLite database", "unallowlisted/raw screenshots"],
                "files": [{"path": n, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()} for n, b in sorted(entries.items())]}
    destination = output.parent / "SentinelOps-MXDR-portfolio.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 3, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
        archive.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("Portable ZIP integrity failed")
    return {"artifact": str(destination), "files": len(entries), "bytes": destination.stat().st_size,
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(), "archive_integrity_verified": True}
