"""Preview-first authorized AMA administration: three providers, four exact RBAC scopes.

Never deploys the DCR/extension/association or sends logs. Reuses the existing
identity/trust/environment; the protected main OIDC workflow owns deployment.
"""
import argparse
import json
import os
import time
import uuid

from ama.cloud import ROLES, fingerprint, contract
from scripts.azure_guard import RG, WORKSPACE, az_json, canonical_uuid
from scripts.bootstrap_oidc import (PIN, IDENTITY, ENVIRONMENT, check_role, github, github_token,
                                    oidc_subject, set_variable)
from scripts.prepare_portfolio import Arm
from scripts.validate_detection import require


def ensure_exact_assignment(arm, listing_path, principal, role, scope):
    # Inspect RBAC directly, keeping the exact scope. Azure can still require
    # the target resource to exist; ResourceNotFound must never widen the scope.
    listing = arm.request("GET", listing_path)
    require(isinstance(listing.get("value"), list) and not listing.get("nextLink"), "Complete exact-assignment preflight required")
    require(all(a["properties"].get("principalId", "").lower() == principal for a in listing["value"]), "Assignment principal filter mismatch")
    exact = [a for a in listing["value"] if a["properties"].get("scope", "").lower() == scope.lower() and
             a["properties"].get("roleDefinitionId", "").lower() == role["id"].lower()]
    require(len(exact) <= 1, "Duplicate AMA assignment; do not add another")
    if not exact:
        assignment_id = str(uuid.uuid5(uuid.NAMESPACE_URL, (principal + scope + role["id"]).lower()))
        created = arm.request("PUT", scope + "/providers/Microsoft.Authorization/roleAssignments/" + assignment_id + "?api-version=2022-04-01",
                     {"properties": {"roleDefinitionId": role["id"], "principalId": principal, "principalType": "ServicePrincipal"}})
        props = created.get("properties", {})
        require(props.get("principalId", "").lower() == principal and props.get("scope", "").lower() == scope.lower() and
                props.get("roleDefinitionId", "").lower() == role["id"].lower(), "Persisted exact AMA assignment mismatch")


def prepare(apply=False):
    require(os.environ.get("GITHUB_ACTIONS") != "true", "Administrative setup cannot run in CI")
    pin = json.loads(PIN.read_text())
    subscription, tenant = canonical_uuid(pin["subscription_id"]), canonical_uuid(pin["tenant_id"])
    account = az_json("account", "show")
    require(account.get("id", "").lower() == subscription and account.get("tenantId", "").lower() == tenant, "Pinned account mismatch; never switch subscriptions")
    print("AMA plan: existing CI identity; three Arc providers; four narrow roles at exact targets; approved SHA256=" + fingerprint())
    if not apply:
        print("PREVIEW ONLY: no Azure REST or GitHub mutation")
        return
    require(account.get("user", {}).get("type") == "user", "Authorized personal MFA setup session required")
    token = github_token()
    repo = github(token, "GET", "")
    require(repo.get("visibility") == "public" and repo.get("permissions", {}).get("admin"), "Public repository administration required")
    protection = github(token, "GET", "/branches/main/protection")
    require(protection.get("enforce_admins", {}).get("enabled") and protection.get("required_pull_request_reviews") is not None and
            protection.get("required_status_checks", {}).get("strict") and "offline" in protection.get("required_status_checks", {}).get("contexts", []), "Protected PR/CI path required")
    environment = github(token, "GET", f"/environments/{ENVIRONMENT}")
    require(environment.get("deployment_branch_policy") == {"protected_branches": False, "custom_branch_policies": True}, "Environment protection mismatch")
    branches = github(token, "GET", f"/environments/{ENVIRONMENT}/deployment-branch-policies")
    require([(b.get("name"), b.get("type")) for b in branches.get("branch_policies", [])] == [("main", "branch")], "Main-only environment required")
    subject = oidc_subject(repo, github(token, "GET", "/actions/oidc/customization/sub"))
    arm = Arm()
    group = "/subscriptions/" + subscription + "/resourceGroups/" + RG
    workspace = group + "/providers/Microsoft.OperationalInsights/workspaces/" + WORKSPACE
    targets = contract(workspace)
    identity = arm.request("GET", group + "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/" + IDENTITY + "?api-version=2023-01-31")
    principal = canonical_uuid(identity["properties"]["principalId"])
    require(identity["properties"].get("tenantId", "").lower() == tenant, "Existing identity tenant mismatch")
    trusts = arm.request("GET", identity["id"] + "/federatedIdentityCredentials?api-version=2023-01-31")
    require(not trusts.get("nextLink") and len(trusts.get("value", [])) == 1, "Exactly one existing trust required")
    trust = trusts["value"][0]["properties"]
    require(trust.get("subject") == subject and trust.get("issuer") == "https://token.actions.githubusercontent.com" and trust.get("audiences") == ["api://AzureADTokenExchange"], "Trust mismatch; do not overwrite")
    assignments_path = f"/subscriptions/{subscription}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&$filter=principalId%20eq%20%27{principal}%27"
    listing = arm.request("GET", assignments_path)
    require(not listing.get("nextLink"), "Complete existing assignment inventory required")
    before = [a["properties"] for a in listing["value"]]
    for namespace in ("Microsoft.HybridCompute", "Microsoft.GuestConfiguration", "Microsoft.HybridConnectivity"):
        provider_path = "/subscriptions/" + subscription + "/providers/" + namespace
        state = arm.request("GET", provider_path + "?api-version=2021-04-01")["registrationState"]
        require(state in {"Registered", "NotRegistered", "Registering"}, "Unexpected provider state")
        if state == "NotRegistered":
            arm.request("POST", provider_path + "/register?api-version=2021-04-01")
        for attempt in range(20):
            state = arm.request("GET", provider_path + "?api-version=2021-04-01")["registrationState"]
            if state == "Registered":
                break
            time.sleep(5)
        require(state == "Registered", "Arc provider registration incomplete; rerun only after read-only inspection")
        print("VERIFIED provider: " + namespace)
    added = []
    for kind, (name, actions) in ROLES.items():
        roles = az_json("role", "definition", "list", "--name", name, "--scope", group)
        require(len(roles) <= 1, "Ambiguous named AMA role")
        if roles:
            role = roles[0]
        else:
            identifier = str(uuid.uuid5(uuid.NAMESPACE_URL, group.lower() + "/" + name))
            value = {"properties": {"roleName": name, "type": "CustomRole", "description": "Approved single-machine AMA pilot; exact assignment scopes; no delete, billing, queries or analytics-rule writes",
                     "permissions": [{"actions": actions, "notActions": [], "dataActions": [], "notDataActions": []}], "assignableScopes": [group]}}
            created = arm.request("PUT", group + "/providers/Microsoft.Authorization/roleDefinitions/" + identifier + "?api-version=2022-04-01", value)
            role = dict(created["properties"], id=created["id"])
        check_role(role, group, name, actions)
        scope = targets[kind + "_id"]
        ensure_exact_assignment(arm, assignments_path, principal, role, scope)
        added.append((role["id"].lower(), scope.lower()))
        print("VERIFIED narrow AMA role/assignment: " + kind)
    listing = arm.request("GET", assignments_path)
    require(not listing.get("nextLink"), "Complete final assignment inventory required")
    after = [a["properties"] for a in listing["value"]]
    pairs = lambda rows: {(r["roleDefinitionId"].lower(), r["scope"].lower()) for r in rows}
    require(pairs(after) == pairs(before) | set(added), "Unrelated role assignments changed")
    set_variable(token, "SENTINEL_AMA_APPROVED_SHA256", fingerprint())
    print("AMA SETUP VERIFIED: four exact assignments; existing identity/trust preserved; no collection or cloud workload deployed by personal account")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    try:
        prepare(parser.parse_args().apply)
    except (ValueError, OSError) as exc:
        raise SystemExit("AMA administrative setup stopped: " + str(exc)) from None
