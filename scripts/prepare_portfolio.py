"""Preview-first administrative setup: reuse identity/roles, exact rule scopes only.

Personal MFA session is only used for RBAC setup and verification. It cannot
deploy analytics rules. Deployment remains the protected main OIDC workflow.
"""
import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid

from portfolio.catalog import SPECS, fingerprint, resource_uuid, validate
from scripts.azure_guard import RG, WORKSPACE, az_json, canonical_uuid
from scripts.bootstrap_oidc import (ACTIONS, ENVIRONMENT, IDENTITY, INVENTORY_ACTIONS,
                                    INVENTORY_ROLE_NAME, METADATA_ACTIONS, METADATA_ROLE_NAME,
                                    PIN, ROLE_NAME, check_role, github, github_token,
                                    oidc_subject, set_variable)
from scripts.deploy_portfolio import target_current
from scripts.validate_detection import require, validate_rule


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Arm:
    def __init__(self):
        self.token = az_json("account", "get-access-token", "--scope", "https://management.core.windows.net//.default")["accessToken"]

    def request(self, method, path, body=None):
        request = urllib.request.Request("https://management.azure.com" + path, method=method,
                                         data=None if body is None else json.dumps(body).encode(),
                                         headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=60) as response:
                return json.loads(response.read(2_097_152))
        except urllib.error.HTTPError as exc:
            code = "AzureHTTPError"
            try:
                candidate = json.loads(exc.read(65536)).get("error", {}).get("code", "")
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,80}", candidate):
                    code = candidate
            except (ValueError, AttributeError):
                pass
            raise ValueError(f"Azure administrative request failed (HTTP {exc.code}, {code}); no subscription switch or fallback") from None


def prepare(apply=False):
    require(os.environ.get("GITHUB_ACTIONS") != "true", "Administrative setup cannot run in CI")
    digest = validate()
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    subscription, tenant = canonical_uuid(pin["subscription_id"]), canonical_uuid(pin["tenant_id"])
    account = az_json("account", "show")
    require(account.get("id", "").lower() == subscription and account.get("tenantId", "").lower() == tenant, "Pinned account mismatch; refusing to switch")
    print(f"Portfolio plan: {len(SPECS)} disabled fixed targets; fingerprint {digest}. Reuse identity, existing narrow role and OIDC trust. No source, query, activation or billing change.")
    if not apply:
        print("PREVIEW: no Azure REST requests or GitHub mutations.")
        return
    require(account.get("user", {}).get("type") == "user", "Administrative MFA session required")
    token = github_token()
    repo = github(token, "GET", "")
    require(repo.get("visibility") == "public" and repo.get("permissions", {}).get("admin"), "Public repository administrator access required")
    protection = github(token, "GET", "/branches/main/protection")
    require(protection.get("enforce_admins", {}).get("enabled") and protection.get("required_pull_request_reviews") is not None,
            "Protected PR path required")
    checks = protection.get("required_status_checks", {})
    require(checks.get("strict") and "offline" in checks.get("contexts", []), "Required offline CI protection missing")
    environment = github(token, "GET", f"/environments/{ENVIRONMENT}")
    require(environment.get("deployment_branch_policy") == {"protected_branches": False, "custom_branch_policies": True}, "Environment protection mismatch")
    branches = github(token, "GET", f"/environments/{ENVIRONMENT}/deployment-branch-policies")
    require([(b.get("name"), b.get("type")) for b in branches.get("branch_policies", [])] == [("main", "branch")], "Main-only environment required")
    subject = oidc_subject(repo, github(token, "GET", "/actions/oidc/customization/sub"))
    arm = Arm()
    group = f"/subscriptions/{subscription}/resourceGroups/{RG}"
    workspace = group + f"/providers/Microsoft.OperationalInsights/workspaces/{WORKSPACE}"
    metadata = arm.request("GET", workspace + "?api-version=2025-02-01")
    require(metadata.get("id", "").lower() == workspace.lower() and metadata.get("location") == "westeurope", "Workspace mismatch")
    identities = arm.request("GET", group + "/providers/Microsoft.ManagedIdentity/userAssignedIdentities?api-version=2023-01-31")
    require(isinstance(identities.get("value"), list) and not identities.get("nextLink"), "Complete identity inventory required")
    identities = [x for x in identities["value"] if x.get("name") == IDENTITY]
    require(len(identities) == 1 and identities[0].get("properties", {}).get("tenantId", "").lower() == tenant, "Existing identity mismatch")
    identity = identities[0]
    principal = canonical_uuid(identity["properties"]["principalId"])
    trusts = arm.request("GET", identity["id"] + "/federatedIdentityCredentials?api-version=2023-01-31")
    require(not trusts.get("nextLink") and len(trusts.get("value", [])) == 1, "One existing trust required")
    trust = trusts["value"][0].get("properties", {})
    require(trust.get("subject") == subject and trust.get("issuer") == "https://token.actions.githubusercontent.com" and
            trust.get("audiences") == ["api://AzureADTokenExchange"], "Existing exact trust mismatch; no trust changes")
    listing = arm.request("GET", workspace + "/providers/Microsoft.SecurityInsights/alertRules?api-version=2025-09-01")
    require(isinstance(listing.get("value"), list) and not listing.get("nextLink"), "Complete rule inventory required")
    sources = arm.request("GET", workspace + "/providers/Microsoft.SecurityInsights/sourcecontrols?api-version=2025-09-01")
    require(sources.get("value") == [] and not sources.get("nextLink"), "Other deployment ownership requires review")
    for key in SPECS:
        target_current(listing["value"], workspace, key)
    # Preserve the two deployed rules and discover their existing IDs without publishing them.
    existing = []
    for key in ("AZ-DET-001", "AZ-DET-002"):
        expected = validate_rule(detection=key)
        found = [r for r in listing["value"] if r.get("properties", {}).get("displayName") == expected["properties"]["displayName"]]
        require(len(found) == 1 and found[0].get("kind") == "Scheduled" and
                all(found[0].get("properties", {}).get(k) == v for k, v in expected["properties"].items()), "Original rule drift")
        expected_id = workspace + "/providers/Microsoft.SecurityInsights/alertRules/" + canonical_uuid(found[0]["name"])
        require(found[0].get("id", "").lower() == expected_id.lower(), "Original rule identity mismatch")
        if key == "AZ-DET-002":
            from scripts.validate_detection import DETECTIONS
            require(found[0]["name"].lower() == DETECTIONS[key]["resource_uuid"], "Original additional target mismatch")
        existing.append(found[0]["id"])
    selected = {}
    for name, actions in ((ROLE_NAME, ACTIONS), (METADATA_ROLE_NAME, METADATA_ACTIONS), (INVENTORY_ROLE_NAME, INVENTORY_ACTIONS)):
        role_filter = urllib.parse.quote("roleName eq '" + name + "'", safe="")
        roles = arm.request("GET", group + "/providers/Microsoft.Authorization/roleDefinitions?api-version=2022-04-01&$filter=" + role_filter)
        require(isinstance(roles.get("value"), list) and not roles.get("nextLink"), "Complete named-role inventory required")
        matches = [r for r in roles["value"] if r.get("properties", {}).get("roleName") == name]
        require(len(matches) == 1, "Existing narrow custom role required; no new role definition")
        role = dict(matches[0]["properties"], id=matches[0]["id"])
        check_role(role, group, name, actions)
        selected[name] = role
    writer = selected[ROLE_NAME]
    targets = [workspace + "/providers/Microsoft.SecurityInsights/alertRules/" + resource_uuid(key) for key in SPECS]
    allowed = {(writer["id"].lower(), scope.lower()) for scope in existing + targets}
    allowed |= {(selected[name]["id"].lower(), workspace.lower()) for name in (METADATA_ROLE_NAME, INVENTORY_ROLE_NAME)}
    assignments = arm.request("GET", f"/subscriptions/{subscription}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&$filter=principalId%20eq%20%27{principal}%27")
    require(isinstance(assignments.get("value"), list) and not assignments.get("nextLink"), "Complete identity assignments required")
    own = [a for a in assignments["value"] if a.get("properties", {}).get("principalId", "").lower() == principal]
    pairs = [(a["properties"]["roleDefinitionId"].lower(), a["properties"]["scope"].lower()) for a in own]
    require(len(pairs) == len(set(pairs)) and set(pairs) <= allowed, "Unexpected or duplicate identity permissions; no broadening")
    baseline = allowed - {(writer["id"].lower(), scope.lower()) for scope in targets}
    require(baseline <= set(pairs), "Existing baseline permissions are missing; stop before any new assignment")
    for scope in targets:
        pair = (writer["id"].lower(), scope.lower())
        if pair in pairs:
            continue
        assignment_id = str(uuid.uuid5(uuid.NAMESPACE_URL, (principal + scope + writer["id"]).lower()))
        result = arm.request("PUT", scope + f"/providers/Microsoft.Authorization/roleAssignments/{assignment_id}?api-version=2022-04-01",
                             {"properties": {"roleDefinitionId": writer["id"], "principalId": principal, "principalType": "ServicePrincipal"}})
        props = result.get("properties", {})
        require(props.get("principalId", "").lower() == principal and props.get("scope", "").lower() == scope.lower() and
                props.get("roleDefinitionId", "").lower() == writer["id"].lower(), "Persisted exact assignment mismatch")
    final = arm.request("GET", f"/subscriptions/{subscription}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&$filter=principalId%20eq%20%27{principal}%27")
    require(isinstance(final.get("value"), list) and not final.get("nextLink"), "Complete final assignments required")
    final_own = [a["properties"] for a in final["value"] if a.get("properties", {}).get("principalId", "").lower() == principal]
    final_pairs = [(a["roleDefinitionId"].lower(), a["scope"].lower()) for a in final_own]
    require(len(final_pairs) == len(allowed) and set(final_pairs) == allowed, "Final narrow assignment verification failed")
    set_variable(token, "SENTINEL_PORTFOLIO_APPROVED_SHA256", fingerprint())
    print("SETUP VERIFIED: existing identity/trust/role reused; ten exact rule scopes prepared, approved fingerprint recorded. No rule deployed by personal account.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    try:
        prepare(parser.parse_args().apply)
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Portfolio setup stopped: {exc}") from None
