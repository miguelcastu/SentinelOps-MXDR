"""Preview-first exact test RBAC; personal setup only, never analytics deployment."""
import argparse
import json
import os
import subprocess
import uuid
from pathlib import Path

from lifecycle.contract import API, CLOSER, CLOSE_ACTIONS, READER, READ_ACTIONS, RULE_UUID, fingerprint, parameters, require
from scripts.azure_guard import RG, WORKSPACE, az_json, canonical_uuid
from scripts.bootstrap_oidc import IDENTITY, ENVIRONMENT, PIN, ROLE_NAME, ACTIONS, check_role, github, github_token, oidc_subject, seal, set_variable
from scripts.prepare_ama import ensure_exact_assignment
from scripts.prepare_portfolio import Arm
from scripts.run_lifecycle import find_incident


def ensure_role(arm, group, name, actions):
    roles = az_json("role", "definition", "list", "--name", name, "--scope", group)
    require(len(roles) <= 1, "Ambiguous lifecycle role")
    if roles:
        role = roles[0]
    else:
        identifier = str(uuid.uuid5(uuid.NAMESPACE_URL, group.lower() + "/" + name))
        body = {"properties": {"roleName": name, "type": "CustomRole", "description": "One reviewed synthetic lifecycle acceptance; exact target assignment; no deletion, playbook, containment, billing or collection changes",
            "permissions": [{"actions": actions, "notActions": [], "dataActions": [], "notDataActions": []}], "assignableScopes": [group]}}
        created = arm.request("PUT", group + "/providers/Microsoft.Authorization/roleDefinitions/" + identifier + "?api-version=2022-04-01", body)
        role = dict(created["properties"], id=created["id"])
    check_role(role, group, name, actions)
    return role


def prepare(apply=False, approve_incident=False):
    require(os.environ.get("GITHUB_ACTIONS") != "true", "Administrative setup cannot run in CI")
    print("Lifecycle setup: fixed rule writer plus workspace incident read; optional later classifier only at the actual linked test incident. No cloud deployment by this script.")
    if not apply:
        print("PREVIEW: no Azure request, GitHub mutation, rule activation or log query; contract=" + fingerprint())
        return
    approval = json.loads(Path(".local/completion/lifecycle-approved.private.json").read_text(encoding="utf-8"))
    require(approval.get("approved_sha256") == fingerprint() and approval.get("single_synthetic_scheduled_lifecycle") is True, "Concrete lifecycle authorization required")
    require(subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True).stdout.strip() == "main", "Reviewed merged main required")
    require(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout == "", "Clean reviewed main required")
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    subscription, tenant = canonical_uuid(pin["subscription_id"]), canonical_uuid(pin["tenant_id"])
    account = az_json("account", "show")
    require(account.get("id", "").lower() == subscription and account.get("tenantId", "").lower() == tenant and account.get("user", {}).get("type") == "user", "Pinned personal MFA setup session required; no subscription switch")
    token = github_token()
    repo = github(token, "GET", "")
    require(repo.get("visibility") == "public" and repo.get("permissions", {}).get("admin"), "Existing public repository admin required")
    protection = github(token, "GET", "/branches/main/protection")
    require(protection.get("enforce_admins", {}).get("enabled") and protection.get("required_status_checks", {}).get("strict") and "offline" in protection.get("required_status_checks", {}).get("contexts", []) and protection.get("required_pull_request_reviews") is not None, "Protected PR path required")
    branches = github(token, "GET", f"/environments/{ENVIRONMENT}/deployment-branch-policies")
    require([(b.get("name"), b.get("type")) for b in branches.get("branch_policies", [])] == [("main", "branch")], "Existing main-only environment required")
    subject = oidc_subject(repo, github(token, "GET", "/actions/oidc/customization/sub"))
    arm = Arm()
    sub = arm.request("GET", "/subscriptions/" + subscription + "?api-version=2022-12-01")
    require(sub.get("state") == "Enabled" and sub.get("subscriptionPolicies", {}).get("spendingLimit") == "On", "Active unchanged credit subscription required")
    group = "/subscriptions/" + subscription + "/resourceGroups/" + RG
    workspace = group + "/providers/Microsoft.OperationalInsights/workspaces/" + WORKSPACE
    identity = arm.request("GET", group + "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/" + IDENTITY + "?api-version=2023-01-31")
    principal = canonical_uuid(identity["properties"]["principalId"])
    trusts = arm.request("GET", identity["id"] + "/federatedIdentityCredentials?api-version=2023-01-31")
    require(not trusts.get("nextLink") and len(trusts.get("value", [])) == 1, "Existing single OIDC trust required")
    trust = trusts["value"][0]["properties"]
    require(trust.get("subject") == subject and trust.get("issuer") == "https://token.actions.githubusercontent.com" and trust.get("audiences") == ["api://AzureADTokenExchange"], "OIDC trust mismatch")
    assignment_path = f"/subscriptions/{subscription}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&$filter=principalId%20eq%20%27{principal}%27"
    before = arm.request("GET", assignment_path)
    require(not before.get("nextLink"), "Complete role inventory required")
    target = workspace + "/providers/Microsoft.SecurityInsights/alertRules/" + RULE_UUID
    if approve_incident:
        current = arm.request("GET", target + "?api-version=" + API)
        parameters(current)
        require(current["properties"]["enabled"] is False, "Disable the single-use test before classifying")
        incident = find_incident(arm, workspace, target)
        require(incident is not None and incident["properties"]["status"] in {"New", "Active"}, "One linked actual open test incident required")
        identifier = canonical_uuid(incident["name"])
        require(incident["id"].lower() == (workspace + "/providers/Microsoft.SecurityInsights/incidents/" + identifier).lower(), "Exact incident scope mismatch")
        role = ensure_role(arm, group, CLOSER, CLOSE_ACTIONS)
        ensure_exact_assignment(arm, assignment_path, principal, role, incident["id"])
        key = github(token, "GET", f"/environments/{ENVIRONMENT}/secrets/public-key")
        github(token, "PUT", f"/environments/{ENVIRONMENT}/secrets/SENTINEL_LIFECYCLE_INCIDENT_ID", {"key_id": key["key_id"], "encrypted_value": seal(identifier, key["key"] )})
        scope = "single actual linked synthetic incident"
        added = [(role["id"].lower(), incident["id"].lower())]
    else:
        writers = az_json("role", "definition", "list", "--name", ROLE_NAME, "--scope", group)
        require(len(writers) == 1, "Reuse existing analytics writer role")
        writer = writers[0]
        check_role(writer, group, ROLE_NAME, ACTIONS)
        ensure_exact_assignment(arm, assignment_path, principal, writer, target)
        reader = ensure_role(arm, group, READER, READ_ACTIONS)
        ensure_exact_assignment(arm, assignment_path, principal, reader, workspace)
        scope = "one fixed test rule writer and workspace incident inventory read"
        added = [(writer["id"].lower(), target.lower()), (reader["id"].lower(), workspace.lower())]
    after = arm.request("GET", assignment_path)
    require(not after.get("nextLink"), "Complete final assignment inventory required")
    pairs = lambda value: {(a["properties"]["roleDefinitionId"].lower(), a["properties"]["scope"].lower()) for a in value["value"]}
    require(pairs(after) == pairs(before) | set(added), "Unrelated assignment change detected")
    set_variable(token, "SENTINEL_LIFECYCLE_APPROVED_SHA256", fingerprint())
    report = {"evidence": "actual-azure-rest-rbac-setup", "scope": scope, "existing_ci_identity_and_trust_reused": True,
              "assignments_total": len(after["value"]), "added_exact_assignments": len(added), "analytics_rules_deployed": 0, "queries_executed": 0,
              "workspace_wide_incident_write": False, "broad_rule_write": False, "approved_sha256": fingerprint()}
    destination = Path(".local/completion/lifecycle-classifier-rbac.sanitized.json" if approve_incident else ".local/completion/lifecycle-start-rbac.sanitized.json")
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approve-incident", action="store_true")
    args = parser.parse_args()
    try:
        prepare(args.apply, args.approve_incident)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise SystemExit("Lifecycle setup stopped; no scope widening or personal deployment. " + str(exc)) from None
