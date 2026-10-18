"""Operator-only one-time OIDC bootstrap. Preview is the default; never run --apply autonomously.

The optional apply mode needs PyNaCl for GitHub sealed-box encryption. CI and
normal detection tooling remain dependency-free. Azure user credentials are used
only by the operator during this explicit administrative prerequisite.
"""
import argparse
import base64
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from scripts.azure_guard import RG, WORKSPACE, az_json, canonical_uuid
from scripts.validate_detection import ROOT, require

PIN = ROOT / ".local/azure-target.json"
REPO = "miguelcastu/SentinelOps-MXDR"
ENVIRONMENT = "sentinel-lab"
IDENTITY = "id-sentinelops-rule002-ci"
ACTIONS = ["Microsoft.SecurityInsights/alertRules/read", "Microsoft.SecurityInsights/alertRules/write",
           "Microsoft.OperationalInsights/workspaces/read"]
ROLE_NAME = "SentinelOps Disabled Rule Lab Deployer"
SUBJECT = f"repo:{REPO}:environment:{ENVIRONMENT}"


def github_token():
    result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                            text=True, capture_output=True, timeout=30,
                            env=dict(os.environ, GCM_INTERACTIVE="never", GIT_TERMINAL_PROMPT="0"))
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    require(result.returncode == 0 and values.get("password"), "GitHub Git credential is unavailable; no Azure setup was started")
    return values["password"]


def github(token, method, path, body=None):
    request = urllib.request.Request("https://api.github.com/repos/" + REPO + path,
                                    data=None if body is None else json.dumps(body).encode(), method=method,
                                    headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                                             "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "SentinelOps-operator-bootstrap"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
            return json.loads(data) if data else None
    except urllib.error.HTTPError as exc:
        raise ValueError(f"GitHub HTTP {exc.code}; inspect permissions privately and rerun the idempotent setup") from None


def seal(value, key):
    from nacl.public import PublicKey, SealedBox
    return base64.b64encode(SealedBox(PublicKey(base64.b64decode(key))).encrypt(value.encode())).decode()


def check_role(role, scope):
    require(role.get("roleName") == ROLE_NAME, "Existing role name mismatch")
    scopes = role.get("assignableScopes", [])
    require(len(scopes) == 1 and scopes[0].lower() == scope.lower(), "Existing role has unapproved assignable scope")
    permissions = role.get("permissions", [])
    require(len(permissions) == 1, "Unexpected custom-role permission blocks")
    entry = permissions[0]
    require(sorted(a.lower() for a in entry.get("actions", [])) == sorted(a.lower() for a in ACTIONS) and
            all(entry.get(field) == [] for field in ("notActions", "dataActions", "notDataActions")),
            "Existing custom role differs from the approved permissions; do not overwrite or widen it")


def bootstrap(apply=False):
    require(os.environ.get("GITHUB_ACTIONS") != "true", "Administrative bootstrap must never run in CI")
    require(PIN.exists(), "Missing private subscription pin. Ask the agent to prepare it from the existing local account metadata.")
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    subscription = canonical_uuid(pin["subscription_id"])
    tenant = canonical_uuid(pin["tenant_id"])
    account = az_json("account", "show")  # reads cached local context; does not switch it
    require(account.get("id", "").lower() == subscription and account.get("tenantId", "").lower() == tenant,
            "Subscription/tenant differs from the private pin. Refusing to select a different subscription.")
    print("Plan: existing pinned subscription; existing West Europe workspace; one dedicated managed identity; narrow analytics-rule RBAC; GitHub OIDC and encrypted environment identifiers. No paid compute, connectors, queries, or billing changes.")
    if not apply:
        print("PREVIEW ONLY: no Azure cloud request or GitHub mutation performed. The operator must review the runbook and run --apply personally.")
        return
    require(account.get("user", {}).get("type") == "user", "Operator setup requires your own administrative user session")
    # Resolve all local dependencies and GitHub protections before Azure mutations.
    from nacl.public import SealedBox  # noqa: F401
    token = github_token()
    repository = github(token, "GET", "")
    require(repository.get("visibility") == "public" and repository.get("permissions", {}).get("admin"), "Expected public repository and administrator GitHub access")
    environment = github(token, "GET", f"/environments/{ENVIRONMENT}")
    require(environment.get("deployment_branch_policy") == {"protected_branches": False, "custom_branch_policies": True}, "Expected custom main-only environment policy")
    branches = github(token, "GET", f"/environments/{ENVIRONMENT}/deployment-branch-policies")
    require([(b.get("name"), b.get("type")) for b in branches.get("branch_policies", [])] == [("main", "branch")], "Environment must permit only branch main")
    protection = github(token, "GET", "/branches/main/protection")
    require(protection.get("enforce_admins", {}).get("enabled") and protection.get("required_pull_request_reviews") is not None,
            "Main must enforce PR protection for administrators")
    public_key = github(token, "GET", f"/environments/{ENVIRONMENT}/secrets/public-key")
    resource_group = f"/subscriptions/{subscription}/resourceGroups/{RG}"
    workspace_id = f"{resource_group}/providers/Microsoft.OperationalInsights/workspaces/{WORKSPACE}"
    workspace = az_json("monitor", "log-analytics", "workspace", "show", "--resource-group", RG, "--workspace-name", WORKSPACE)
    require(workspace.get("id", "").lower() == workspace_id.lower() and workspace.get("location") == "westeurope", "Existing workspace mismatch; no replacement is provisioned")
    identities = az_json("identity", "list", "--resource-group", RG)
    matches = [identity for identity in identities if identity.get("name") == IDENTITY]
    require(len(matches) <= 1, "Ambiguous managed identity")
    identity = matches[0] if matches else az_json("identity", "create", "--name", IDENTITY, "--resource-group", RG, "--location", "westeurope")
    role_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, resource_group.lower() + "/sentinelops-rule002-deployer"))
    roles = az_json("role", "definition", "list", "--name", role_uuid, "--scope", resource_group)
    if roles:
        require(len(roles) == 1, "Ambiguous custom role")
        check_role(roles[0], resource_group)
        role = roles[0]
    else:
        definition = {"Name": ROLE_NAME, "Id": role_uuid, "IsCustom": True,
                      "Description": "Analytics rules only in the existing lab workspace; no infrastructure, delete, queries or billing permissions",
                      "Actions": ACTIONS, "NotActions": [], "DataActions": [], "NotDataActions": [], "AssignableScopes": [resource_group]}
        with tempfile.TemporaryDirectory(prefix="sentinelops-role-") as directory:
            path = Path(directory) / "role.json"
            path.write_text(json.dumps(definition), encoding="utf-8")
            role = az_json("role", "definition", "create", "--role-definition", str(path))
        check_role(role, resource_group)
    assignments = az_json("role", "assignment", "list", "--scope", workspace_id, "--include-inherited")
    own = [assignment for assignment in assignments if assignment.get("principalId", "").lower() == identity["principalId"].lower()]
    require(all(a.get("roleDefinitionId", "").lower() == role["id"].lower() and a.get("scope", "").lower() == workspace_id.lower() for a in own),
            "Dedicated identity has unexpected/inherited assignments. Administrator review required; no automatic removal or escalation.")
    if not own:
        az_json("role", "assignment", "create", "--assignee-object-id", identity["principalId"],
                "--assignee-principal-type", "ServicePrincipal", "--role", role["id"], "--scope", workspace_id)
    credentials = az_json("identity", "federated-credential", "list", "--identity-name", IDENTITY, "--resource-group", RG)
    require(len(credentials) <= 1, "Unexpected federated trusts on dedicated identity; review privately")
    if credentials:
        credential = credentials[0]
        require(credential.get("issuer") == "https://token.actions.githubusercontent.com" and credential.get("subject") == SUBJECT and
                credential.get("audiences") == ["api://AzureADTokenExchange"], "Existing federated trust differs; no overwrite attempted")
    else:
        az_json("identity", "federated-credential", "create", "--identity-name", IDENTITY, "--resource-group", RG,
                "--name", "github-sentinel-lab", "--issuer", "https://token.actions.githubusercontent.com",
                "--subject", SUBJECT, "--audiences", "api://AzureADTokenExchange")
    for name, value in {"AZURE_ADDITIONAL_CLIENT_ID": identity["clientId"], "AZURE_TENANT_ID": tenant, "AZURE_SUBSCRIPTION_ID": subscription}.items():
        github(token, "PUT", f"/environments/{ENVIRONMENT}/secrets/{name}",
               {"encrypted_value": seal(value, public_key["key"]), "key_id": public_key["key_id"]})
    # Keep all earlier rule/query approval flags unchanged.
    variables = github(token, "GET", f"/environments/{ENVIRONMENT}/variables")
    exists = any(v["name"] == "SENTINEL_AZ_DET_002_APPROVED" for v in variables.get("variables", []))
    github(token, "PATCH" if exists else "POST", f"/environments/{ENVIRONMENT}/variables" + ("/SENTINEL_AZ_DET_002_APPROVED" if exists else ""),
           {"name": "SENTINEL_AZ_DET_002_APPROVED", "value": "true"})
    print("SETUP COMPLETE: dedicated OIDC identity and encrypted GitHub identifiers configured. No Sentinel rule deployed by this script. Review/merge the PR; GitHub CI performs the disabled-rule deployment and REST verification.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Operator-only explicit administrative configuration after review")
    try:
        bootstrap(parser.parse_args().apply)
    except (ValueError, OSError, subprocess.SubprocessError, ImportError) as exc:
        raise SystemExit(f"Setup stopped: {exc}") from None
