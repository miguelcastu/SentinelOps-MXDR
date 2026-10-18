"""OIDC format compatibility, drift visibility and sanitized diagnostics."""
import copy
import unittest
from unittest.mock import patch
import subprocess

from scripts.azure_guard import az_json
from scripts.bootstrap_oidc import oidc_subject
from scripts.check_drift import changed_properties
from scripts.validate_detection import validate_rule


class TestOidcSubject(unittest.TestCase):
    def setUp(self):
        self.repository = {"id": 123, "owner": {"id": 456}}

    def test_immutable_subject_uses_authoritative_prefix(self):
        settings = {"use_default": True, "use_immutable_subject": True,
                    "sub_claim_prefix": "repo:miguelcastu@456/SentinelOps-MXDR@123"}
        self.assertEqual(oidc_subject(self.repository, settings),
                         "repo:miguelcastu@456/SentinelOps-MXDR@123:environment:sentinel-lab")

    def test_legacy_subject_remains_supported_for_legacy_repositories(self):
        self.assertEqual(oidc_subject(self.repository, {"use_default": True,
                         "sub_claim_prefix": "repo:miguelcastu/SentinelOps-MXDR"}),
                         "repo:miguelcastu/SentinelOps-MXDR:environment:sentinel-lab")

    def test_unrelated_or_uninspected_subject_cannot_be_trusted(self):
        for settings in ({"use_default": True, "sub_claim_prefix": "repo:someone/else"},
                         {"use_default": False, "sub_claim_prefix": "repo:miguelcastu/SentinelOps-MXDR"},
                         {"use_default": True, "sub_claim_prefix": "repo:miguelcastu@999/SentinelOps-MXDR@123"},
                         {"use_default": True}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                oidc_subject(self.repository, settings)


class TestDrift(unittest.TestCase):
    def test_matching_state_is_not_drift(self):
        desired = validate_rule()
        self.assertEqual(changed_properties(copy.deepcopy(desired), desired), [])

    def test_disabled_schedule_query_and_incident_changes_are_drift(self):
        desired = validate_rule()
        for key, value in (("enabled", True), ("queryPeriod", "P1D"), ("query", "unsafe"),
                           ("incidentConfiguration", {"createIncident": True})):
            current = copy.deepcopy(desired)
            current["properties"][key] = value
            self.assertEqual(changed_properties(current, desired), [key])

    def test_azure_failure_reports_code_without_identity_or_token(self):
        result = subprocess.CompletedProcess([], 1, stdout="", stderr="ERROR: (AuthorizationFailed) sensitive client and token")
        with patch("scripts.azure_guard.subprocess.run", return_value=result):
            with self.assertRaisesRegex(ValueError, "AuthorizationFailed") as caught:
                az_json("rest", "--method", "get")
        self.assertNotIn("sensitive", str(caught.exception))

    def test_json_wrapped_azure_error_is_diagnosable_without_identifiers(self):
        identity = "11111111-1111-4111-8111-111111111111"
        result = subprocess.CompletedProcess([], 1, stdout="", stderr='ERROR: Bad Request({"error":{"code":"BadRequest","message":"Invalid payload for ' + identity + ' synthetic@example.invalid"}})')
        with patch("scripts.azure_guard.subprocess.run", return_value=result):
            with self.assertRaises(ValueError) as caught:
                az_json("rest", "--method", "put", "--url", "https://management.azure.com/example/alertRules/synthetic")
        self.assertIn("PUT analytics rule failed (BadRequest)", str(caught.exception))
        self.assertIn("Invalid payload", str(caught.exception))
        self.assertNotIn(identity, str(caught.exception))
        self.assertNotIn("synthetic@example.invalid", str(caught.exception))
