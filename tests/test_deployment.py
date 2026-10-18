"""Exercise cloud boundaries with mocked Azure calls; never contact Azure."""
import copy
import contextlib
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.azure_guard import canonical_uuid, context, rule_url
from scripts.check_prerequisites import check
from scripts.deploy_rule import deploy, verify_existing
from scripts.validate_detection import validate_rule

SUB = "11111111-1111-4111-8111-111111111111"
CLIENT = "22222222-2222-4222-8222-222222222222"
TENANT = "33333333-3333-4333-8333-333333333333"
RULE_ID = "44444444-4444-4444-8444-444444444444"
WORKSPACE_ID = f"/subscriptions/{SUB}/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
RESOURCE_ID = f"{WORKSPACE_ID}/providers/Microsoft.SecurityInsights/alertRules/{RULE_ID}"
ENV = {
    "GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": "miguelcastu/SentinelOps-MXDR",
    "GITHUB_REF": "refs/heads/main",
    "GITHUB_WORKFLOW_REF": "miguelcastu/SentinelOps-MXDR/.github/workflows/deploy-sentinel.yml@refs/heads/main",
    "AZURE_SUBSCRIPTION_ID": SUB, "AZURE_CLIENT_ID": CLIENT, "AZURE_TENANT_ID": TENANT,
    "SENTINEL_RULE_ID": RULE_ID, "SENTINEL_DEPLOYMENT_APPROVED": "true",
    "SENTINEL_EXCLUSIVE_RULE_OWNER": "true",
}


def current_rule():
    return dict(validate_rule(), id=RESOURCE_ID, type="Microsoft.SecurityInsights/alertRules", etag='"test-etag"')


class TestContext(unittest.TestCase):
    def test_uuid_rejects_injection_empty_and_placeholders(self):
        for value in ("", "../another", "0" * 32, "00000000-0000-0000-0000-000000000000", RULE_ID + "?override=1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical_uuid(value)

    def test_rule_url_is_pinned(self):
        self.assertEqual(rule_url(WORKSPACE_ID, RULE_ID), "https://management.azure.com" + RESOURCE_ID + "?api-version=2025-09-01")

    def test_context_accepts_only_expected_identity_and_subscription(self):
        account = {"id": SUB, "tenantId": TENANT, "user": {"name": CLIENT, "type": "servicePrincipal"}}
        with patch.dict(os.environ, ENV, clear=True), patch("scripts.azure_guard.az_json", return_value=account):
            self.assertEqual(context("deploy-sentinel.yml"), WORKSPACE_ID)
        for change in ({"id": RULE_ID}, {"tenantId": RULE_ID}, {"user": {"type": "user", "name": "personal"}},
                       {"user": {"type": "servicePrincipal", "name": RULE_ID}}):
            with self.subTest(change=change), patch.dict(os.environ, ENV, clear=True), patch("scripts.azure_guard.az_json", return_value=dict(account, **change)):
                with self.assertRaises(ValueError):
                    context("deploy-sentinel.yml")

    def test_local_feature_branch_wrong_repo_and_workflow_rejected_before_cli(self):
        for change in ({"GITHUB_ACTIONS": "false"}, {"GITHUB_REF": "refs/heads/feature"},
                       {"GITHUB_REPOSITORY": "someone/else"}, {"GITHUB_WORKFLOW_REF": "wrong"}):
            with self.subTest(change=change), patch.dict(os.environ, dict(ENV, **change), clear=True), patch("scripts.azure_guard.az_json") as az:
                with self.assertRaises(ValueError):
                    context("deploy-sentinel.yml")
                az.assert_not_called()

    def test_configuration_prerequisites(self):
        with patch.dict(os.environ, ENV, clear=True):
            with contextlib.redirect_stdout(io.StringIO()):
                check("deploy")
        for key in ENV:
            if key.startswith(("AZURE_", "SENTINEL_")):
                missing = dict(ENV)
                del missing[key]
                with self.subTest(key=key), patch.dict(os.environ, missing, clear=True):
                    with self.assertRaises(ValueError):
                        check("deploy")


class TestDeployment(unittest.TestCase):
    def test_reject_unapproved_cloud_resources(self):
        for changes in ({"id": RESOURCE_ID + "-other"}, {"type": "Microsoft.Compute/virtualMachines"},
                        {"kind": "Fusion"}, {"etag": ""}, {"properties": {}},
                        {"properties": dict(validate_rule()["properties"], enabled=True)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                verify_existing(dict(current_rule(), **changes), RESOURCE_ID)

    def test_success_updates_exact_existing_id_and_verifies_persisted_body(self):
        current = current_rule()
        workspace = {"id": WORKSPACE_ID, "location": "westeurope"}
        payloads = []

        def fake_az(*args):
            if "put" in args:
                self.assertIn("If-Match=" + current["etag"], args)
                path = args[args.index("--body") + 1].removeprefix("@")
                payloads.append(json.loads(Path(path).read_text(encoding="utf-8")))
                self.assertEqual(args[args.index("--url") + 1], rule_url(WORKSPACE_ID, RULE_ID))
            return workspace if "api-version=2025-02-01" in str(args) else copy.deepcopy(current)

        with patch.dict(os.environ, ENV, clear=True), patch("scripts.deploy_rule.context", return_value=WORKSPACE_ID), patch("scripts.deploy_rule.az_json", side_effect=fake_az) as az:
            with contextlib.redirect_stdout(io.StringIO()):
                deploy()
        self.assertEqual(az.call_count, 4)
        self.assertEqual(len(payloads), 1)
        self.assertIs(payloads[0]["properties"]["enabled"], False)
        self.assertEqual(payloads[0]["etag"], current["etag"])

    def test_missing_rule_never_puts(self):
        workspace = {"id": WORKSPACE_ID, "location": "westeurope"}
        with patch.dict(os.environ, ENV, clear=True), patch("scripts.deploy_rule.context", return_value=WORKSPACE_ID), patch("scripts.deploy_rule.az_json", side_effect=[workspace, ValueError("404")]) as az:
            with self.assertRaises(ValueError):
                deploy()
        self.assertEqual(az.call_count, 2)
        self.assertFalse(any("put" in call.args for call in az.call_args_list))

    def test_wrong_workspace_or_enabled_existing_rule_never_puts(self):
        cases = [({"id": WORKSPACE_ID, "location": "eastus"}, current_rule()),
                 ({"id": WORKSPACE_ID, "location": "westeurope"}, dict(current_rule(), properties=dict(validate_rule()["properties"], enabled=True)))]
        for workspace, current in cases:
            with self.subTest(workspace=workspace), patch.dict(os.environ, ENV, clear=True), patch("scripts.deploy_rule.context", return_value=WORKSPACE_ID), patch("scripts.deploy_rule.az_json", side_effect=[workspace, current]) as az:
                with self.assertRaises(ValueError):
                    deploy()
                self.assertFalse(any("put" in call.args for call in az.call_args_list))

    def test_conflict_stops_without_retry(self):
        workspace = {"id": WORKSPACE_ID, "location": "westeurope"}
        with patch.dict(os.environ, ENV, clear=True), patch("scripts.deploy_rule.context", return_value=WORKSPACE_ID), patch("scripts.deploy_rule.az_json", side_effect=[workspace, current_rule(), ValueError("conflict")]) as az:
            with self.assertRaises(ValueError):
                deploy()
        self.assertEqual(az.call_count, 3)

    def test_persisted_drift_is_not_reported_as_success(self):
        workspace = {"id": WORKSPACE_ID, "location": "westeurope"}
        persisted = copy.deepcopy(current_rule())
        persisted["properties"]["queryPeriod"] = "PT2H"
        with patch.dict(os.environ, ENV, clear=True), patch("scripts.deploy_rule.context", return_value=WORKSPACE_ID), patch("scripts.deploy_rule.az_json", side_effect=[workspace, current_rule(), current_rule(), persisted]):
            with self.assertRaisesRegex(ValueError, "Persisted property mismatch"):
                deploy()

    def test_unapproved_deployment_performs_no_cloud_calls(self):
        with patch.dict(os.environ, dict(ENV, SENTINEL_DEPLOYMENT_APPROVED="false"), clear=True), patch("scripts.deploy_rule.az_json") as az:
            with self.assertRaises(ValueError):
                deploy()
            az.assert_not_called()
