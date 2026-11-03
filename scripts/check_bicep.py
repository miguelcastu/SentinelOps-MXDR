"""Obtain only the locked public compiler, verify bytes, compile without Azure."""
import hashlib
import json
import os
from pathlib import Path
import platform
import urllib.request

from infrastructure.preview import BICEP, compile_templates, require


def main():
    require(platform.system() == "Linux" and platform.machine().lower() in {"x86_64", "amd64"}, "CI compiler check requires Linux x64")
    lock = json.loads((BICEP / "tools.lock.json").read_text(encoding="utf-8"))
    target = lock["linux-x64"]
    require(target["url"] == f'https://github.com/Azure/bicep/releases/download/v{lock["version"]}/bicep-linux-x64')
    directory = Path(os.environ["RUNNER_TEMP"]) / "sentinelops-bicep"
    directory.mkdir(exist_ok=True)
    binary = directory / "bicep"
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(target["url"], timeout=60) as response, binary.open("wb") as destination:
        while chunk := response.read(1048576):
            total += len(chunk)
            require(total <= 268435456, "Compiler download exceeds pinned tool allowance")
            digest.update(chunk)
            destination.write(chunk)
    require(digest.hexdigest() == target["sha256"], "Public compiler SHA-256 mismatch")
    binary.chmod(0o700)
    print(json.dumps(compile_templates(binary, directory / "compiled"), sort_keys=True))


if __name__ == "__main__":
    main()
