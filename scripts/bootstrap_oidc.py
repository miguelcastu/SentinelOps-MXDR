"""Explicitly authorized one-time setup of the existing identity and AZ-DET-001.

The optional apply mode needs PyNaCl for GitHub sealed-box encryption. CI and
normal detection tooling remain dependency-free. The personal MFA session is
used only for administrative setup, never routine analytics-rule deployment.
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
from scripts.validate_detection import DETECTIONS, ROOT, require

PIN = ROOT / ".local/azure-target.json"
REPO = "miguelcastu/SentinelOps-MXDR"
ENVIRONMENT = "sentinel-lab"
IDENTITY = "id-sentinelops-ci"
ACTIONS = ["Microsoft.SecurityInsights/alertRules/read", "Microsoft.SecurityInsights/alertRules/write"]
ROLE_NAME = "SentinelOps Existing Analytics Rule Deployer"
METADATA_ACTIONS = ["Microsoft.OperationalInsights/workspaces/read"]
METADATA_ROLE_NAME = "SentinelOps Workspace Metadata Reader"
INVENTORY_ACTIONS = ["Microsoft.SecurityInsights/alertRules/read"]
INVENTORY_ROLE_NAME = "SentinelOps Analytics Rule Inventory Reader"
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


def oidc_subject(repository, settings):
    require(settings.get("use_default") is True, "Custom OIDC templates require explicit inspection; do not guess the subject")
    legacy = "repo:" + REPO
    owner, name = REPO.split("/")
    immutable = f"repo:{owner}@{repository.get('owner', {}).get('id')}/{name}@{repository.get('id')}"
    prefix = settings.get("sub_claim_prefix")
    require(prefix in (legacy, immutable), "OIDC prefix does not match the authenticated repository identity")
    return prefix + ":environment:" + ENVIRONMENT


def check_role(role, scope, name=ROLE_NAME, actions=None):
    actions = ACTIONS if actions is None else actions
    require(role.get("roleName") == name, "Existing role name mismatch")
    scopes = role.get("assignableScopes", [])
    require(len(scopes) == 1 and scopes[0].lower() == scope.lower(), "Existing role has unapproved assignable scope")
    permissions = role.get("permissions", [])
    require(len(permissions) == 1, "Unexpected custom-role permission blocks")
    entry = permissions[0]
    require(sorted(a.lower() for a in entry.get("actions", [])) == sorted(a.lower() for a in actions) and
            all(entry.get(field) == [] for field in ("notActions", "dataActions", "notDataActions")),
            "Existing custom role differs from the approved permissions; do not overwrite or widen it")


def ensure_role(name, slug, actions, resource_group):
    role_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, resource_group.lower() + "/" + slug))
    # Discover by verified role name, including roles created by older CLI
    # versions that ignored the template's requested Id on create.
    roles = az_json("role", "definition", "list", "--name", name, "--scope", resource_group)
    require(len(roles) <= 1, "Ambiguous custom role")
    if roles:
        check_role(roles[0], resource_group, name, actions)
        return roles[0]
    definition = {"properties": {"roleName": name, "type": "CustomRole",
                  "description": "Narrow SentinelOps lab CI permission; no infrastructure, delete, queries or billing operations",
                  "permissions": [{"actions": actions, "notActions": [], "dataActions": [], "notDataActions": []}], "assignableScopes": [resource_group]}}
    with tempfile.TemporaryDirectory(prefix="sentinelops-role-") as directory:
        path = Path(directory) / "role.json"
        path.write_text(json.dumps(definition), encoding="utf-8")
        result = az_json("rest", "--method", "put", "--url",
                         f"https://management.azure.com{resource_group}/providers/Microsoft.Authorization/roleDefinitions/{role_uuid}?api-version=2022-04-01",
                         "--body", "@" + str(path))
        role = dict(result["properties"], id=result["id"])
    check_role(role, resource_group, name, actions)
    return role


def ensure_assignment(principal, role, scope):
    assignments = az_json("role", "assignment", "list", "--scope", scope,
                          "--include-inherited", "--fill-principal-name", "false")
    own = [a for a in assignments if a.get("principalId", "").lower() == principal.lower()]
    matches = [a for a in own if a.get("roleDefinitionId", "").lower() == role["id"].lower() and a.get("scope", "").lower() == scope.lower()]
    require(len(matches) <= 1, "Duplicate role assignments; review without creating more")
    if not matches:
        assignment_id = str(uuid.uuid5(uuid.NAMESPACE_URL, (principal + scope + role["id"]).lower()))
        az_json("role", "assignment", "create", "--name", assignment_id, "--assignee-object-id", principal,
                "--assignee-principal-type", "ServicePrincipal", "--role", role["id"], "--scope", scope)


def set_variable(token, name, value):
    variables = github(token, "GET", f"/environments/{ENVIRONMENT}/variables")
    require(not variables.get("total_count", 0) > len(variables.get("variables", [])), "Paginated variables need complete review")
    exists = any(v["name"] == name for v in variables.get("variables", []))
    github(token, "PATCH" if exists else "POST", f"/environments/{ENVIRONMENT}/variables" + ("/" + name if exists else ""),
           {"name": name, "value": value})


def bootstrap(apply=False, include_additional=False):
    require(os.environ.get("GITHUB_ACTIONS") != "true", "Administrative bootstrap must never run in CI")
    require(PIN.exists(), "Missing private subscription pin; no target can be guessed")
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    subscription = canonical_uuid(pin["subscription_id"])
    tenant = canonical_uuid(pin["tenant_id"])
    account = az_json("account", "show")
    require(account.get("id", "").lower() == subscription and account.get("tenantId", "").lower() == tenant,
            "Subscription/tenant differs from the private pin. Refusing to select a different subscription.")
    print("Plan: reuse id-sentinelops-ci, existing pinned workspace and existing disabled AZ-DET-001; exact-rule write scope, workspace metadata read, GitHub OIDC and encrypted identifiers. No new identity, infrastructure, queries or billing changes.")
    if include_additional:
        print("Additional plan: read-only analytics inventory and write only at the fixed AZ-DET-002 UUID; deployment remains in the disabled-rule CI workflow.")
    if not apply:
        print("PREVIEW ONLY: no Azure cloud request or GitHub mutation performed. Explicit setup authorization and MFA are required for --apply.")
        return
    require(account.get("user", {}).get("type") == "user", "Setup requires the authorized administrative MFA session")
    from nacl.public import SealedBox  # dependency checked before any cloud mutation
    token = github_token()
    repository = github(token, "GET", "")
    require(repository.get("visibility") == "public" and repository.get("permissions", {}).get("admin"), "Expected public repository and administrator GitHub access")
    subject = oidc_subject(repository, github(token, "GET", "/actions/oidc/customization/sub"))
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
    print("Checking existing workspace, identity and unique disabled rule...")
    workspace = az_json("rest", "--method", "get", "--url", f"https://management.azure.com{workspace_id}?api-version=2025-02-01")
    require(workspace.get("id", "").lower() == workspace_id.lower() and workspace.get("location") == "westeurope", "Existing workspace mismatch; no replacement is provisioned")
    identities = az_json("identity", "list", "--resource-group", RG)
    matches = [identity for identity in identities if identity.get("name") == IDENTITY]
    require(len(matches) == 1, "Expected existing id-sentinelops-ci; no duplicate identity will be created")
    identity = matches[0]
    require(identity.get("tenantId", "").lower() == tenant, "Identity tenant mismatch")
    rules = az_json("rest", "--method", "get", "--url", f"https://management.azure.com{workspace_id}/providers/Microsoft.SecurityInsights/alertRules?api-version=2025-09-01")
    require(not rules.get("nextLink") and isinstance(rules.get("value"), list), "Incomplete analytics rule inventory")
    matches = [r for r in rules["value"] if r.get("properties", {}).get("displayName") == "AZ-DET-001 - Azure Diagnostic Settings Modified"]
    require(len(matches) == 1 and matches[0].get("kind") == "Scheduled" and matches[0]["properties"].get("enabled") is False,
            "Expected exactly one existing disabled Scheduled AZ-DET-001")
    rule = matches[0]
    rule_uuid = canonical_uuid(rule["name"])
    expected_id = workspace_id + "/providers/Microsoft.SecurityInsights/alertRules/" + rule_uuid
    require(rule.get("id", "").lower() == expected_id.lower(), "Rule resource ID mismatch")
    additional = [r for r in rules["value"] if r.get("properties", {}).get("displayName") == DETECTIONS["AZ-DET-002"]["name"]]
    require(len(additional) <= 1, "Duplicate AZ-DET-002 resources")
    additional_id = None
    if additional:
        additional_id = workspace_id + "/providers/Microsoft.SecurityInsights/alertRules/" + DETECTIONS["AZ-DET-002"]["resource_uuid"]
        require(additional[0].get("id", "").lower() == additional_id.lower() and additional[0].get("kind") == "Scheduled" and
                additional[0]["properties"].get("enabled") is False, "Existing additional rule has unapproved ID/kind/state")
    elif include_additional:
        additional_id = workspace_id + "/providers/Microsoft.SecurityInsights/alertRules/" + DETECTIONS["AZ-DET-002"]["resource_uuid"]
        require(not any(r.get("id", "").lower() == additional_id.lower() for r in rules["value"]), "The new fixed UUID is already occupied by an unrelated rule")
    sources = az_json("rest", "--method", "get", "--url", f"https://management.azure.com{workspace_id}/providers/Microsoft.SecurityInsights/sourcecontrols?api-version=2025-09-01")
    require(sources.get("value") == [] and not sources.get("nextLink"), "Existing Sentinel Repositories configuration requires ownership review")
    backup = PIN.parent / "AZ-DET-001-original.private.json"
    if not backup.exists():
        backup.write_text(json.dumps(rule, indent=2), encoding="utf-8")
    print("Ensuring narrow role definitions and exact resource assignments...")
    writer = ensure_role(ROLE_NAME, "sentinelops-existing-rule-deployer", ACTIONS, resource_group)
    reader = ensure_role(METADATA_ROLE_NAME, "sentinelops-workspace-metadata-reader", METADATA_ACTIONS, resource_group)
    allowed = {(writer["id"].lower(), expected_id.lower()), (reader["id"].lower(), workspace_id.lower())}
    inventory_reader = None
    if additional_id:
        inventory_reader = ensure_role(INVENTORY_ROLE_NAME, "sentinelops-rule-inventory-reader", INVENTORY_ACTIONS, resource_group)
        allowed |= {(writer["id"].lower(), additional_id.lower()), (inventory_reader["id"].lower(), workspace_id.lower())}
    for scope in (workspace_id, expected_id, *([additional_id] if additional_id else [])):
        assignments = az_json("role", "assignment", "list", "--scope", scope, "--include-inherited", "--fill-principal-name", "false")
        own = [a for a in assignments if a.get("principalId", "").lower() == identity["principalId"].lower()]
        require(all((a.get("roleDefinitionId", "").lower(), a.get("scope", "").lower()) in allowed for a in own),
                "Dedicated identity has unexpected/inherited permissions; no automatic removal or broader grant")
    ensure_assignment(identity["principalId"], reader, workspace_id)
    ensure_assignment(identity["principalId"], writer, expected_id)
    if additional_id:
        ensure_assignment(identity["principalId"], inventory_reader, workspace_id)
        ensure_assignment(identity["principalId"], writer, additional_id)
    print("Ensuring exact GitHub OIDC federation...")
    credentials = az_json("identity", "federated-credential", "list", "--identity-name", IDENTITY, "--resource-group", RG)
    require(len(credentials) <= 1, "Unexpected or duplicate federated trusts")
    if credentials:
        credential = credentials[0]
        require(credential.get("issuer") == "https://token.actions.githubusercontent.com" and
                credential.get("audiences") == ["api://AzureADTokenExchange"], "Existing trust differs; no overwrite attempted")
        if credential.get("subject") != subject:
            require(credential.get("subject") == SUBJECT, "Existing trust belongs to another subject; no overwrite attempted")
            az_json("identity", "federated-credential", "update", "--identity-name", IDENTITY, "--resource-group", RG,
                    "--name", credential["name"], "--subject", subject)
    else:
        az_json("identity", "federated-credential", "create", "--identity-name", IDENTITY, "--resource-group", RG,
                "--name", "github-sentinel-lab", "--issuer", "https://token.actions.githubusercontent.com",
                "--subject", subject, "--audiences", "api://AzureADTokenExchange")
    print("Encrypting authentication identifiers into the existing GitHub environment...")
    for name, value in {"AZURE_CLIENT_ID": identity["clientId"], "AZURE_TENANT_ID": tenant, "AZURE_SUBSCRIPTION_ID": subscription}.items():
        github(token, "PUT", f"/environments/{ENVIRONMENT}/secrets/{name}",
               {"encrypted_value": seal(value, public_key["key"]), "key_id": public_key["key_id"]})
    set_variable(token, "SENTINEL_RULE_ID", rule_uuid)
    set_variable(token, "SENTINEL_EXCLUSIVE_RULE_OWNER", "true")
    set_variable(token, "SENTINEL_DEPLOYMENT_APPROVED", "true")
    if include_additional:
        set_variable(token, "SENTINEL_AZ_DET_002_APPROVED", "true")
    print("SETUP COMPLETE: existing identity, exact-rule RBAC, OIDC and GitHub configuration verified. No Sentinel rule deployed by this script. Use the approved main GitHub workflow for deployment and actual REST verification.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Explicitly authorized administrative setup with interactive MFA")
    parser.add_argument("--include-additional", action="store_true", help="Also prepare the exact AZ-DET-002 scope and read-only inventory; never broad workspace write")
    try:
        arguments = parser.parse_args()
        bootstrap(arguments.apply, arguments.include_additional)
    except (ValueError, OSError, subprocess.SubprocessError, ImportError) as exc:
        raise SystemExit(f"Setup stopped: {exc}") from None
