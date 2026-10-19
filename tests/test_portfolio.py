"""Synthetic detection semantics and fail-closed OIDC deployment boundaries."""
import contextlib
import copy
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from portfolio.catalog import SPECS, definition, fingerprint, resource_uuid, validate
from portfolio.simulate import evaluate, event, scenarios
from scripts.deploy_portfolio import deploy, verify
from scripts.prepare_portfolio import prepare
from scripts.bootstrap_oidc import ACTIONS, ROLE_NAME, METADATA_ACTIONS, METADATA_ROLE_NAME, INVENTORY_ACTIONS, INVENTORY_ROLE_NAME

WORKSPACE = "/subscriptions/11111111-1111-4111-8111-111111111111/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
AS_OF = "2026-10-19T12:20:00Z"


def cloud(key):
    return dict(definition(key), id=WORKSPACE + "/providers/Microsoft.SecurityInsights/alertRules/" + resource_uuid(key),
                name=resource_uuid(key), type="Microsoft.SecurityInsights/alertRules", etag='"fixture"')


class TestPortfolioSemantics(unittest.TestCase):
    def test_all_synthetic_positive_and_negative_controls(self):
        validate()
        for case in scenarios():
            with self.subTest(case=case["id"]):
                self.assertEqual(len(evaluate(case["detection"], case["events"], AS_OF)), case["expected"])

    def test_expected_legitimate_administration_matches_are_not_claimed_false_positive_rate(self):
        # No broad allowlist hides administration by the CI principal.
        for key, spec in SPECS.items():
            if spec[5] == "single":
                self.assertEqual(len(evaluate(key, [event(spec[4][0], caller="synthetic-approved-ci")], AS_OF)), 1)

    def test_burst_distinct_events_threshold_actor_scope_and_fixed_bin_boundaries(self):
        key = "AZ-DET-011"
        events = [event(SPECS[key][4][0], suffix=str(i), status="Failed") for i in range(5)]
        self.assertEqual(len(evaluate(key, events, AS_OF)), 1)
        self.assertEqual(len(evaluate(key, [dict(e, Caller=e["Caller"].upper(), ResourceGroup=e["ResourceGroup"].upper()) if i % 2 else e for i, e in enumerate(events)], AS_OF)), 1)
        for changed in (events[:4], [events[0]] * 100,
                        events[:4] + [dict(events[4], Caller="another-actor")],
                        events[:4] + [dict(events[4], ResourceGroup="another-scope")],
                        events[:4] + [dict(events[4], SubscriptionId="another-subscription")],
                        events[:4] + [dict(events[4], TimeGenerated="2026-10-19T12:10:00Z")],
                        [dict(e, ActivityStatusValue="Succeeded") for e in events]):
            self.assertEqual(evaluate(key, changed, AS_OF), [])

    def test_aggregate_maps_resource_group_context_without_guessing_caller_or_ip(self):
        body = definition("AZ-DET-011")["properties"]
        self.assertEqual(body["entityMappings"], [{"entityType": "AzureResource", "fieldMappings": [{"identifier": "ResourceId", "columnName": "TargetResourceId"}]}])
        self.assertIn('strcat("/subscriptions/", SubscriptionId, "/resourceGroups/", ResourceGroup)', body["query"])
        for key in SPECS:
            self.assertGreaterEqual(len(definition(key)["properties"]["entityMappings"]), 1)

    def test_sequence_strict_order_identity_scope_and_fifteen_minute_bound(self):
        key = "AZ-DET-012"
        grant = event(SPECS[key][4][0], suffix="grant", time="2026-10-19T12:00:00Z")
        diag = event(SPECS[key][4][1], suffix="diag", time="2026-10-19T12:15:00Z")
        self.assertEqual(len(evaluate(key, [grant, diag], AS_OF)), 1)
        for changed in (dict(diag, TimeGenerated=grant["TimeGenerated"]),
                        dict(diag, TimeGenerated="2026-10-19T11:59:59Z"),
                        dict(diag, TimeGenerated="2026-10-19T12:15:00.001Z"),
                        dict(diag, Caller="another-actor"), dict(diag, ResourceGroup="another-scope"),
                        dict(diag, SubscriptionId="another-subscription"), dict(diag, SubscriptionId=""),
                        dict(diag, Caller=""), dict(diag, ActivityStatusValue="Failed")):
            self.assertEqual(evaluate(key, [grant, changed], AS_OF), [])
        self.assertEqual(len(evaluate(key, [grant, dict(diag, Caller=diag["Caller"].upper(), ResourceGroup=diag["ResourceGroup"].upper())], AS_OF)), 1)

    def test_sequence_latest_grant_and_equal_time_tie_preserve_lineage(self):
        grant = event(SPECS["AZ-DET-012"][4][0], suffix="a")
        tie = dict(grant, EventDataId="synthetic-event-z")
        diag = event(SPECS["AZ-DET-012"][4][1], suffix="diag", time="2026-10-19T12:10:00Z")
        self.assertEqual(evaluate("AZ-DET-012", [grant, tie, diag, diag], AS_OF), [(tie["EventDataId"], diag["EventDataId"])])

    def test_missing_lineage_future_window_and_case_insensitive_operation_status(self):
        key = "AZ-DET-003"
        normal = event(SPECS[key][4][0].upper(), status="sUcCeSs")
        self.assertEqual(len(evaluate(key, [normal], AS_OF)), 1)
        for time, expected in (("2026-10-19T11:20:00Z", 1), ("2026-10-19T11:19:59.999Z", 0),
                               (AS_OF, 1), ("2026-10-19T12:20:00.001Z", 0)):
            self.assertEqual(len(evaluate(key, [dict(normal, TimeGenerated=time)], AS_OF)), expected)
        self.assertEqual(evaluate(key, [dict(normal, EventDataId="")], AS_OF), [])

    def test_real_input_conflicting_duplicates_and_unbounded_input_are_rejected(self):
        original = event(SPECS["AZ-DET-003"][4][0])
        for data in ([dict(original, synthetic=False)], [dict(original, EventDataId="real-identifier")],
                     [original, dict(original, Caller="different")], [original] * 1001):
            with self.assertRaises(ValueError):
                evaluate("AZ-DET-003", data, AS_OF)


class TestPortfolioDeployment(unittest.TestCase):
    def run_deployment(self, fake):
        with patch.dict(os.environ, {"SENTINEL_PORTFOLIO_APPROVED_SHA256": fingerprint(), "SENTINEL_EXCLUSIVE_RULE_OWNER": "true"}, clear=True), \
             patch("scripts.deploy_portfolio.context", return_value=WORKSPACE), \
             patch("scripts.deploy_portfolio.az_json", side_effect=fake), contextlib.redirect_stdout(io.StringIO()) as output:
            deploy()
        return output.getvalue()

    def test_create_fixed_ten_disabled_targets_once_then_idempotent_without_writes(self):
        inventory, puts = [], []
        untouched = {"id": WORKSPACE + "/providers/Microsoft.SecurityInsights/alertRules/fusion", "name": "fusion", "kind": "Fusion", "properties": {"enabled": True}}
        def fake(*args):
            url = args[args.index("--url") + 1]
            if "api-version=2025-02-01" in url:
                return {"id": WORKSPACE, "location": "westeurope"}
            if "/alertRules?" in url:
                return {"value": copy.deepcopy([untouched] + inventory)}
            key = next(k for k in SPECS if resource_uuid(k) in url)
            if "put" in args:
                self.assertIn("If-None-Match=*", args)
                body = json.loads(Path(args[args.index("--body") + 1][1:]).read_text())
                self.assertEqual(body, definition(key))
                self.assertIs(body["properties"]["enabled"], False)
                self.assertIs(body["properties"]["incidentConfiguration"]["createIncident"], False)
                inventory.append(cloud(key))
                puts.append(key)
            return cloud(key)
        output = self.run_deployment(fake)
        self.assertEqual(puts, list(SPECS))
        self.assertIn('"existing_rules_unchanged":true', output)
        self.assertIn("PORTFOLIO_EVIDENCE=", output)
        self.run_deployment(fake)
        self.assertEqual(len(puts), 10)

    def test_all_targets_preflight_before_any_write(self):
        for mutate in (lambda r: r["properties"].update(enabled=True),
                       lambda r: r.update(id=r["id"] + "wrong"),
                       lambda r: r.update(kind="Fusion"),
                       lambda r: r["properties"].update(alertRuleTemplateName="external"),
                       lambda r: r["properties"].update(query="arbitrary query")):
            bad = cloud("AZ-DET-012")
            mutate(bad)
            with patch.dict(os.environ, {"SENTINEL_PORTFOLIO_APPROVED_SHA256": fingerprint(), "SENTINEL_EXCLUSIVE_RULE_OWNER": "true"}, clear=True), \
                 patch("scripts.deploy_portfolio.context", return_value=WORKSPACE), \
                 patch("scripts.deploy_portfolio.az_json", side_effect=[{"id": WORKSPACE, "location": "westeurope"}, {"value": [bad]}]) as az:
                with self.assertRaises(ValueError):
                    deploy()
                self.assertFalse(any("put" in c.args for c in az.call_args_list))

    def test_ambiguous_partial_inventory_and_transport_errors_never_mean_absence(self):
        for listing in ({"value": [], "nextLink": "external"}, {"value": [cloud("AZ-DET-003"), cloud("AZ-DET-003")]},
                        {"value": "invalid"}, ValueError("403")):
            with self.assertRaises(ValueError):
                self.run_deployment(Mock(side_effect=[{"id": WORKSPACE, "location": "westeurope"}, listing]))

    def test_missing_approval_fingerprint_or_ownership_blocks_before_authentication(self):
        for values in ({}, {"SENTINEL_PORTFOLIO_APPROVED_SHA256": "old"}, {"SENTINEL_PORTFOLIO_APPROVED_SHA256": fingerprint()}):
            with patch.dict(os.environ, values, clear=True), patch("scripts.deploy_portfolio.context") as context, patch("scripts.deploy_portfolio.az_json") as az:
                with self.assertRaises(ValueError):
                    deploy()
                context.assert_not_called()
                az.assert_not_called()

    def test_cloud_property_drift_cannot_be_reported_as_success(self):
        changed = cloud("AZ-DET-003")
        changed["properties"]["incidentConfiguration"]["createIncident"] = True
        with self.assertRaises(ValueError):
            verify(changed, WORKSPACE, "AZ-DET-003")

    def test_personal_session_cannot_call_deployment(self):
        # Exercise the actual OIDC guard, not the mocked context used above.
        with patch.dict(os.environ, {"SENTINEL_PORTFOLIO_APPROVED_SHA256": fingerprint(), "SENTINEL_EXCLUSIVE_RULE_OWNER": "true"}, clear=True), patch("scripts.deploy_portfolio.az_json") as az:
            with self.assertRaises(ValueError):
                deploy()
            az.assert_not_called()

    def test_health_scope_expands_only_with_matching_portfolio_approval(self):
        from platform_health.collect import collect
        first_id = "66666666-6666-4666-8666-666666666666"
        from scripts.validate_detection import validate_rule, DETECTIONS
        original = [dict(validate_rule(detection=key), id=WORKSPACE + "/providers/Microsoft.SecurityInsights/alertRules/" + rule_id, name=rule_id)
                    for key, rule_id in (("AZ-DET-001", first_id), ("AZ-DET-002", DETECTIONS["AZ-DET-002"]["resource_uuid"]))]
        workspace = {"id": WORKSPACE, "location": "westeurope", "properties": {"retentionInDays": 30, "sku": {"name": "pergb2018"}, "workspaceCapping": {"dailyQuotaGb": 0.1}}}
        for approval, count in ((fingerprint(), 12), ("", 2), ("stale", 2)):
            with patch.dict(os.environ, {"SENTINEL_RULE_ID": first_id, "SENTINEL_PORTFOLIO_APPROVED_SHA256": approval}, clear=True), \
                 patch("platform_health.collect.context", return_value=WORKSPACE), \
                 patch("platform_health.collect.az_json", side_effect=[workspace, {"value": original + [cloud(k) for k in SPECS]}]) as az:
                value = collect()
                from platform_health.engine import report
                rendered = report(value, value["observed_at"])
                self.assertEqual(rendered["rules"]["expected"], count)
                self.assertEqual(value["rules"]["expected"], count)
                self.assertEqual(value["rules"]["matching"], count)
                self.assertEqual(value["rules"]["active"], 0)
                self.assertEqual(az.call_count, 2)
                if approval == "stale":
                    self.assertIn("Misconfigured", [c["state"] for c in value["checks"] if c["id"] == "portfolio-approval"])

    def test_setup_preview_and_pin_mismatch_never_request_token_or_cloud(self):
        with patch.dict(os.environ, {}, clear=True), tempfile.TemporaryDirectory() as directory:
            pin = Path(directory) / "pin.json"
            pin.write_text(json.dumps({"subscription_id": "11111111-1111-4111-8111-111111111111", "tenant_id": "22222222-2222-4222-8222-222222222222"}))
            with patch("scripts.prepare_portfolio.PIN", pin), patch("scripts.prepare_portfolio.Arm") as arm, \
                 patch("scripts.prepare_portfolio.github_token") as gh, patch("scripts.prepare_portfolio.az_json", return_value={"id": "wrong"}):
                with self.assertRaises(ValueError):
                    prepare(apply=True)
                arm.assert_not_called()
                gh.assert_not_called()
            with patch("scripts.prepare_portfolio.PIN", pin), patch("scripts.prepare_portfolio.Arm") as arm, patch("scripts.prepare_portfolio.github_token") as gh, \
                 patch("scripts.prepare_portfolio.az_json", return_value={"id": "11111111-1111-4111-8111-111111111111", "tenantId": "22222222-2222-4222-8222-222222222222"}), contextlib.redirect_stdout(io.StringIO()):
                prepare()
                arm.assert_not_called()
                gh.assert_not_called()


class TestPortfolioAdministrativeSetup(unittest.TestCase):
    def execute(self, fault=None):
        from scripts.validate_detection import validate_rule, DETECTIONS
        subscription, tenant = "11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"
        principal = "33333333-3333-4333-8333-333333333333"
        group = WORKSPACE.split("/providers/", 1)[0]
        subject = "repo:miguelcastu/SentinelOps-MXDR:environment:sentinel-lab"
        originals = [dict(validate_rule(detection=key), id=WORKSPACE + "/providers/Microsoft.SecurityInsights/alertRules/" + target, name=target)
                     for key, target in (("AZ-DET-001", "66666666-6666-4666-8666-666666666666"), ("AZ-DET-002", DETECTIONS["AZ-DET-002"]["resource_uuid"]))]
        roles = [{"id": group + "/providers/Microsoft.Authorization/roleDefinitions/" + str(i),
                  "properties": {"roleName": name, "assignableScopes": [group], "permissions": [{"actions": actions[:], "notActions": [], "dataActions": [], "notDataActions": []}]}}
                 for i, (name, actions) in enumerate(((ROLE_NAME, ACTIONS), (METADATA_ROLE_NAME, METADATA_ACTIONS), (INVENTORY_ROLE_NAME, INVENTORY_ACTIONS)))]
        assignments = [{"properties": {"scope": scope, "roleDefinitionId": roles[index]["id"], "principalId": principal}}
                       for scope, index in ((originals[0]["id"], 0), (originals[1]["id"], 0), (WORKSPACE, 1), (WORKSPACE, 2))]
        if fault == "broad-role":
            roles[0]["properties"]["permissions"][0]["actions"] = ["*"]
        if fault == "broad-assignment":
            assignments.append({"properties": {"scope": WORKSPACE, "roleDefinitionId": roles[0]["id"], "principalId": principal}})
        writes = []
        def fake_arm(method, path, body=None):
            if method == "PUT":
                self.assertIn("/providers/Microsoft.Authorization/roleAssignments/", path)
                scope = path.rsplit("/providers/Microsoft.Authorization/roleAssignments/", 1)[0]
                self.assertIn(scope, [WORKSPACE + "/providers/Microsoft.SecurityInsights/alertRules/" + resource_uuid(k) for k in SPECS])
                self.assertEqual(body["properties"]["roleDefinitionId"], roles[0]["id"])
                result = {"properties": dict(body["properties"], scope=scope)}
                writes.append(scope)
                assignments.append(result)
                return result
            self.assertEqual(method, "GET")
            if "roleAssignments?" in path:
                return {"value": copy.deepcopy(assignments)}
            if "roleDefinitions?" in path:
                return {"value": copy.deepcopy(roles)}
            if "federatedIdentityCredentials?" in path:
                return {"value": [{"properties": {"issuer": "https://token.actions.githubusercontent.com", "subject": "wrong" if fault == "trust" else subject, "audiences": ["api://AzureADTokenExchange"]}}]}
            if "userAssignedIdentities?" in path:
                return {"value": [{"id": group + "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-sentinelops-ci", "name": "id-sentinelops-ci", "properties": {"tenantId": tenant, "principalId": principal}}]}
            if "sourcecontrols?" in path:
                return {"value": []}
            if "alertRules?" in path:
                return {"value": copy.deepcopy(originals)}
            if "api-version=2025-02-01" in path:
                return {"id": WORKSPACE, "location": "westeurope"}
            self.fail("Unexpected administrative request")
        def fake_github(token, method, path):
            self.assertEqual(method, "GET")
            responses = {"": {"visibility": "public", "permissions": {"admin": True}},
                         "/branches/main/protection": {"enforce_admins": {"enabled": True}, "required_pull_request_reviews": {}, "required_status_checks": {"strict": True, "contexts": ["offline"]}},
                         "/environments/sentinel-lab": {"deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True}},
                         "/environments/sentinel-lab/deployment-branch-policies": {"branch_policies": [{"name": "main", "type": "branch"}]},
                         "/actions/oidc/customization/sub": {"use_default": True, "sub_claim_prefix": "repo:miguelcastu/SentinelOps-MXDR"}}
            return responses[path]
        with tempfile.TemporaryDirectory() as directory:
            pin = Path(directory) / "pin.json"
            pin.write_text(json.dumps({"subscription_id": subscription, "tenant_id": tenant}))
            with patch.dict(os.environ, {}, clear=True), patch("scripts.prepare_portfolio.PIN", pin), \
                 patch("scripts.prepare_portfolio.az_json", return_value={"id": subscription, "tenantId": tenant, "user": {"type": "user"}}), \
                 patch("scripts.prepare_portfolio.github_token", return_value="fake"), patch("scripts.prepare_portfolio.github", side_effect=fake_github), \
                 patch("scripts.prepare_portfolio.Arm") as arm, patch("scripts.prepare_portfolio.set_variable") as variable, contextlib.redirect_stdout(io.StringIO()):
                arm.return_value.request.side_effect = fake_arm
                if fault:
                    with self.assertRaises(ValueError):
                        prepare(apply=True)
                    self.assertEqual(writes, [])
                    variable.assert_not_called()
                else:
                    prepare(apply=True)
                    self.assertEqual(len(writes), 10)
                    self.assertEqual(len(assignments), 14)
                    variable.assert_called_once_with("fake", "SENTINEL_PORTFOLIO_APPROVED_SHA256", fingerprint())

    def test_setup_creates_only_exact_assignments_reusing_identity_trust_and_roles(self):
        self.execute()

    def test_existing_wide_role_assignment_or_wrong_trust_stops_before_any_write(self):
        for fault in ("broad-role", "broad-assignment", "trust"):
            with self.subTest(fault=fault):
                self.execute(fault)
