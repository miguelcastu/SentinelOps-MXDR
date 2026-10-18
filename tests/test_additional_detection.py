"""Authorized second-rule creation and update boundaries, with no Azure requests."""
import contextlib
import copy
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.bootstrap_oidc import ACTIONS, ROLE_NAME, bootstrap, check_role
from scripts.deploy_additional_rule import CONFIG, deploy
from scripts.validate_detection import DETECTIONS, ROOT, parse_predicates, validate_rule

WORKSPACE_ID = "/subscriptions/11111111-1111-4111-8111-111111111111/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
RESOURCE_ID = WORKSPACE_ID + "/providers/Microsoft.SecurityInsights/alertRules/" + CONFIG["resource_uuid"]
WORKSPACE = {"id": WORKSPACE_ID, "location": "westeurope"}


def cloud_rule():
    return dict(validate_rule(detection="AZ-DET-002"), id=RESOURCE_ID, name=CONFIG["resource_uuid"],
                type="Microsoft.SecurityInsights/alertRules", etag='"fixture"')


class TestAdditionalDetection(unittest.TestCase):
    def test_positive_negative_and_legitimate_admin_cases(self):
        query = DETECTIONS["AZ-DET-002"]["query"].read_text(encoding="utf-8")
        seconds, predicates = parse_predicates(query, "AZ-DET-002")
        fixtures = json.loads((ROOT / "tests/fixtures/az_det_002.json").read_text())
        for case in fixtures:
            with self.subTest(case=case["id"]):
                event = {"OperationNameValue": case["operation"], "ActivityStatusValue": case["status"]}
                actual = -seconds <= case["offset"] <= 0 and all(event[column].casefold() in values for column, values in predicates)
                self.assertEqual(actual, case["expected"])

    def test_both_definitions_have_separate_approved_contracts(self):
        for key in DETECTIONS:
            self.assertIs(validate_rule(detection=key)["properties"]["enabled"], False)
        with self.assertRaises(ValueError):
            validate_rule(validate_rule(), detection="AZ-DET-002")
        with self.assertRaises(ValueError):
            validate_rule(detection="AZ-DET-003")

    def test_second_rule_cannot_enable_incidents_or_execute_other_kql(self):
        for key, value in [("enabled", True), ("queryFrequency", "PT1M"), ("incidentConfiguration", {"createIncident": True})]:
            rule = validate_rule(detection="AZ-DET-002")
            rule["properties"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_rule(rule, detection="AZ-DET-002")


class TestAdditionalDeployment(unittest.TestCase):
    def run_with(self, side_effect):
        return (patch.dict(os.environ, {"SENTINEL_AZ_DET_002_APPROVED": "true"}, clear=True),
                patch("scripts.deploy_additional_rule.context", return_value=WORKSPACE_ID),
                patch("scripts.deploy_additional_rule.az_json", side_effect=side_effect))

    def test_create_only_fixed_disabled_resource_and_verify(self):
        payloads = []

        def fake_az(*args):
            if "put" in args:
                self.assertIn("If-None-Match=*", args)
                self.assertIn(RESOURCE_ID, args[args.index("--url") + 1])
                payloads.append(json.loads(Path(args[args.index("--body") + 1][1:]).read_text()))
                return cloud_rule()
            if "/alertRules?" in str(args):
                return {"value": []}
            return WORKSPACE if "api-version=2025-02-01" in str(args) else cloud_rule()

        env, context, az = self.run_with(fake_az)
        with env, context, az as request, contextlib.redirect_stdout(io.StringIO()):
            deploy()
        self.assertEqual(request.call_count, 4)
        self.assertIs(payloads[0]["properties"]["enabled"], False)
        self.assertNotIn("etag", payloads[0])

    def test_existing_target_uses_etag_and_cannot_create_duplicate(self):
        responses = [WORKSPACE, {"value": [cloud_rule()]}, cloud_rule(), cloud_rule()]
        env, context, az = self.run_with(responses)
        with env, context, az as request, contextlib.redirect_stdout(io.StringIO()):
            deploy()
        self.assertIn('If-Match="fixture"', request.call_args_list[2].args)

    def test_ambiguous_wrong_id_enabled_or_paginated_inventory_stops_before_put(self):
        wrong = dict(cloud_rule(), id=RESOURCE_ID + "-wrong")
        enabled = copy.deepcopy(cloud_rule())
        enabled["properties"]["enabled"] = True
        listings = [{"value": [cloud_rule(), cloud_rule()]}, {"value": [wrong]},
                    {"value": [enabled]}, {"value": [], "nextLink": "https://example.invalid/page2"}]
        for listing in listings:
            env, context, az = self.run_with([WORKSPACE, listing])
            with self.subTest(listing=listing), env, context, az as request:
                with self.assertRaises(ValueError):
                    deploy()
                self.assertFalse(any("put" in call.args for call in request.call_args_list))

    def test_inventory_error_is_not_treated_as_absence(self):
        env, context, az = self.run_with([WORKSPACE, ValueError("403")])
        with env, context, az as request:
            with self.assertRaises(ValueError):
                deploy()
        self.assertEqual(request.call_count, 2)

    def test_failed_verification_never_reports_success(self):
        changed = copy.deepcopy(cloud_rule())
        changed["properties"]["queryPeriod"] = "PT2H"
        env, context, az = self.run_with([WORKSPACE, {"value": []}, cloud_rule(), changed])
        with env, context, az, contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(ValueError):
                deploy()
        self.assertNotIn("PASS", output.getvalue())

    def test_no_approval_does_not_contact_azure(self):
        with patch.dict(os.environ, {}, clear=True), patch("scripts.deploy_additional_rule.az_json") as request:
            with self.assertRaises(ValueError):
                deploy()
            request.assert_not_called()


class TestOperatorBootstrap(unittest.TestCase):
    def test_private_pin_mismatch_blocks_before_cloud_setup(self):
        with tempfile.TemporaryDirectory() as directory:
            pin = Path(directory) / "pin.json"
            pin.write_text(json.dumps({"subscription_id": "11111111-1111-4111-8111-111111111111", "tenant_id": "22222222-2222-4222-8222-222222222222"}))
            with patch.dict(os.environ, {}, clear=True), patch("scripts.bootstrap_oidc.PIN", pin), patch("scripts.bootstrap_oidc.az_json", return_value={"id": "wrong"}) as az:
                with self.assertRaises(ValueError):
                    bootstrap(apply=True)
                self.assertEqual(az.call_count, 1)

    def test_operator_apply_only_creates_reviewed_identity_role_and_federation(self):
        subscription = "11111111-1111-4111-8111-111111111111"
        tenant = "22222222-2222-4222-8222-222222222222"
        scope = f"/subscriptions/{subscription}/resourceGroups/rg-sentinelops-mxdr"
        principal = "33333333-3333-4333-8333-333333333333"
        identity = {"name": "id-sentinelops-rule002-ci", "principalId": principal,
                    "clientId": "44444444-4444-4444-8444-444444444444"}
        role = {"id": scope + "/providers/Microsoft.Authorization/roleDefinitions/synthetic",
                "roleName": ROLE_NAME, "assignableScopes": [scope],
                "permissions": [{"actions": ACTIONS, "notActions": [], "dataActions": [], "notDataActions": []}]}
        calls = []
        writes = []

        def fake_az(*args):
            calls.append(args)
            if args[:2] == ("account", "show"):
                return {"id": subscription, "tenantId": tenant, "user": {"type": "user"}}
            if args[:3] == ("monitor", "log-analytics", "workspace"):
                return WORKSPACE
            if args[:2] == ("identity", "list"):
                return []
            if args[:2] == ("identity", "create"):
                return identity
            if args[:3] == ("role", "definition", "list"):
                return []
            if args[:3] == ("role", "definition", "create"):
                body = json.loads(Path(args[-1]).read_text())
                self.assertEqual(body["Actions"], ACTIONS)
                self.assertEqual(body["AssignableScopes"], [scope])
                return role
            if args[:3] == ("role", "assignment", "list"):
                return []
            if args[:3] == ("role", "assignment", "create"):
                self.assertEqual(args[-1], WORKSPACE_ID)
                self.assertIn(principal, args)
                return {}
            if args[:3] == ("identity", "federated-credential", "list"):
                return []
            if args[:3] == ("identity", "federated-credential", "create"):
                self.assertIn("repo:miguelcastu/SentinelOps-MXDR:environment:sentinel-lab", args)
                return {}
            self.fail("Unapproved Azure administrative command")

        def fake_github(token, method, path, body=None):
            if method != "GET":
                writes.append((method, path, body))
                return None
            if path == "":
                return {"visibility": "public", "permissions": {"admin": True}}
            if path.endswith("deployment-branch-policies"):
                return {"branch_policies": [{"name": "main", "type": "branch"}]}
            if path.endswith("/protection"):
                return {"enforce_admins": {"enabled": True}, "required_pull_request_reviews": {}}
            if path.endswith("public-key"):
                return {"key": "fake-key", "key_id": "fake-key-id"}
            if path.endswith("/variables"):
                return {"variables": []}
            return {"deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True}}

        public = types.ModuleType("nacl.public")
        public.SealedBox = object
        with tempfile.TemporaryDirectory() as directory:
            pin = Path(directory) / "pin.json"
            pin.write_text(json.dumps({"subscription_id": subscription, "tenant_id": tenant}))
            with patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules, {"nacl": types.ModuleType("nacl"), "nacl.public": public}), patch("scripts.bootstrap_oidc.PIN", pin), patch("scripts.bootstrap_oidc.az_json", side_effect=fake_az), patch("scripts.bootstrap_oidc.github_token", return_value="fake-token"), patch("scripts.bootstrap_oidc.github", side_effect=fake_github), patch("scripts.bootstrap_oidc.seal", return_value="sealed-ciphertext"), contextlib.redirect_stdout(io.StringIO()) as output:
                bootstrap(apply=True)
        self.assertEqual(len(writes), 4)
        self.assertTrue(all(body.get("encrypted_value") == "sealed-ciphertext" for method, path, body in writes if "/secrets/" in path))
        self.assertNotIn(subscription, output.getvalue())
        self.assertNotIn("fake-token", output.getvalue())
        self.assertFalse(any("rest" in call or "account set" in str(call) for call in calls))

    def test_bootstrap_prohibited_in_ci_even_with_apply(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True), patch("scripts.bootstrap_oidc.az_json") as request:
            with self.assertRaises(ValueError):
                bootstrap(apply=True)
            request.assert_not_called()

    def test_role_cannot_hide_extra_permissions_or_wider_scope(self):
        role = {"roleName": ROLE_NAME, "assignableScopes": ["/approved/group"],
                "permissions": [{"actions": ACTIONS, "notActions": [], "dataActions": [], "notDataActions": []}]}
        check_role(role, "/approved/group")
        for mutation in [{"assignableScopes": ["/subscriptions/all"]},
                         {"permissions": [{"actions": ["*"], "notActions": [], "dataActions": [], "notDataActions": []}]}]:
            with self.assertRaises(ValueError):
                check_role(dict(role, **mutation), "/approved/group")
