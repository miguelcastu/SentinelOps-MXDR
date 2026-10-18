"""Check configuration names locally, before requesting an OIDC token."""
import argparse
import os

from scripts.azure_guard import canonical_uuid
from scripts.validate_detection import require


def check(mode):
    required = ["AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID"]
    if mode == "deploy":
        required += ["SENTINEL_RULE_ID", "SENTINEL_DEPLOYMENT_APPROVED", "SENTINEL_EXCLUSIVE_RULE_OWNER"]
    elif mode == "additional":
        required += ["SENTINEL_AZ_DET_002_APPROVED"]
    else:
        required += ["SENTINEL_LIVE_VALIDATION_APPROVED"]
    missing = [name for name in required if not os.environ.get(name)]
    require(not missing, "Missing environment configuration: " + ", ".join(missing) +
            ". Follow docs/deployment/detection-cicd.md; do not use the personal Azure session.")
    for name in required:
        if name.endswith("_ID"):
            canonical_uuid(os.environ[name])
        else:
            require(os.environ[name] == "true", f"{name} must be explicitly reviewed and set to true")
    print("PASS: required configuration is present; Azure identity/resource access is checked after OIDC login")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["deploy", "query", "additional"], required=True)
    try:
        check(parser.parse_args().mode)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
