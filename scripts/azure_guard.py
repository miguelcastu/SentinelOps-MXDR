"""Azure CLI wrapper with GitHub OIDC context and immutable target checks."""
import json
import os
import re
import shutil
import subprocess
import uuid

from scripts.validate_detection import require

API_VERSION = "2025-09-01"
RG = "rg-sentinelops-mxdr"
WORKSPACE = "law-sentinelops-mxdr-euw"
AZ = shutil.which("az") or "az"


def az_json(*args):
    try:
        result = subprocess.run([AZ, *args, "--only-show-errors", "-o", "json"],
                                text=True, capture_output=True, check=False, timeout=90)
    except subprocess.TimeoutExpired:
        raise ValueError("Azure request timed out; no automatic retry was attempted") from None
    # Azure errors can contain identities, resource IDs and KQL. Never echo them.
    if result.returncode:
        match = re.search(r'''["']code["']\s*:\s*["']([A-Za-z][A-Za-z0-9]+)["']''', result.stderr)
        if not match:
            match = re.search(r"\(([A-Za-z][A-Za-z0-9]+)\)", result.stderr)
        code = match[1] if match else "AzureCLIError"
        detail = ""
        try:
            start = result.stderr.index("{")
            payload, _ = json.JSONDecoder().raw_decode(result.stderr[start:])
            message = payload.get("error", payload).get("message", "")
            if isinstance(message, str):
                message = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}", "[identifier]", message)
                message = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[identity]", message)
                message = re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[token]", message)
                detail = " " + message[:500]
        except (ValueError, AttributeError, TypeError):
            pass
        stage = "CLI context"
        if "--url" in args:
            url = args[args.index("--url") + 1]
            stage = "analytics rule" if "/alertRules" in url else "workspace metadata"
        verb = args[args.index("--method") + 1].upper() if "--method" in args else "READ"
        raise ValueError(f"Azure {verb} {stage} failed ({code}).{detail} No permission escalation was attempted.")
    return json.loads(result.stdout)


def canonical_uuid(value):
    try:
        parsed = uuid.UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("A valid, preapproved UUID is required") from exc
    require(str(parsed) == value.lower(), "UUID must use canonical hyphenated form")
    require(parsed.int != 0, "Placeholder UUIDs are prohibited")
    return str(parsed)


def context(workflow):
    require(os.environ.get("GITHUB_ACTIONS") == "true", "Cloud operations require GitHub Actions OIDC")
    require(os.environ.get("GITHUB_REPOSITORY") == "miguelcastu/SentinelOps-MXDR", "Unapproved repository")
    require(os.environ.get("GITHUB_REF") == "refs/heads/main", "Cloud operations require the approved main branch")
    require(os.environ.get("GITHUB_WORKFLOW_REF", "").split("@", 1)[0] ==
            f"miguelcastu/SentinelOps-MXDR/.github/workflows/{workflow}", "Unapproved workflow")
    subscription = canonical_uuid(os.environ.get("AZURE_SUBSCRIPTION_ID", ""))
    client = canonical_uuid(os.environ.get("AZURE_CLIENT_ID", ""))
    tenant = canonical_uuid(os.environ.get("AZURE_TENANT_ID", ""))
    account = az_json("account", "show")
    require(account.get("id", "").lower() == subscription, "Subscription mismatch; refusing to switch")
    require(account.get("tenantId", "").lower() == tenant, "Tenant mismatch")
    user = account.get("user", {})
    require(user.get("type", "").lower() == "serviceprincipal" and
            user.get("name", "").lower() == client, "Personal sessions and unexpected identities are prohibited")
    workspace_id = (f"/subscriptions/{subscription}/resourceGroups/{RG}/providers/"
                    f"Microsoft.OperationalInsights/workspaces/{WORKSPACE}")
    return workspace_id


def rule_url(workspace_id, rule_id):
    canonical_uuid(rule_id)
    return f"https://management.azure.com{workspace_id}/providers/Microsoft.SecurityInsights/alertRules/{rule_id}?api-version={API_VERSION}"
