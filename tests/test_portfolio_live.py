"""Fixed-query and single-attempt privacy boundaries; no real Azure requests."""
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import scripts.validate_portfolio_live as live
from portfolio.catalog import query_for
from scripts.validate_detection import validate_rule


SUBSCRIPTION = "11111111-1111-4111-8111-111111111111"
TENANT = "22222222-2222-4222-8222-222222222222"
CUSTOMER = "33333333-3333-4333-8333-333333333333"
WORKSPACE = f"/subscriptions/{SUBSCRIPTION}/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"


def result():
    return {"tables": [{"name": "PrimaryResult", "columns": [{"name": "DetectionId", "type": "string"}, {"name": "Matches", "type": "long"}], "rows": [[key, 0] for key in live.DETECTIONS]}]}


class Response:
    def __init__(self, value):
        self.body = value if isinstance(value, bytes) else json.dumps(value).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self, maximum):
        return self.body[:maximum]


class TestPortfolioLiveBoundaries(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.pin = self.root / "pin.private.json"
        self.approval = self.root / "approved.private.json"
        self.ledger = self.root / "attempt.private.json"
        self.report = self.root / "report.sanitized.json"
        self.pin.write_text(json.dumps({"subscription_id": SUBSCRIPTION, "tenant_id": TENANT}), encoding="utf-8")
        self.approval.write_text(json.dumps({"sha256": live.query_fingerprint(), "allow_one_aggregate_query": True}), encoding="utf-8")
        for key, value in (("PIN", self.pin), ("APPROVAL", self.approval), ("LEDGER", self.ledger), ("REPORT", self.report)):
            context = patch.object(live, key, value)
            context.start()
            self.addCleanup(context.stop)
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        clean = patch.object(live, "_git_clean_main")
        clean.start()
        self.addCleanup(clean.stop)

    def auth(self):
        return [{"id": SUBSCRIPTION, "tenantId": TENANT, "user": {"type": "user"}}, {"accessToken": "private-arm-token"}, {"accessToken": "private-logs-token"}]

    def metadata(self):
        return {"id": WORKSPACE, "location": "westeurope", "properties": {"customerId": CUSTOMER}}

    def test_preview_never_authenticates_uses_network_or_consumes_ledger(self):
        self.approval.unlink()
        self.pin.unlink()
        with patch.object(live, "az_json") as auth, patch.object(live.urllib.request, "build_opener") as network:
            preview = live.run()
        self.assertEqual(preview["evidence"], "offline-preview")
        self.assertEqual(preview["planned_log_queries"], 1)
        self.assertEqual(len(preview["fixed_detections"]), 12)
        auth.assert_not_called()
        network.assert_not_called()
        self.assertFalse(self.ledger.exists())

    def test_complete_nested_let_queries_survive_function_wrapping(self):
        query = live.fixed_query()
        self.assertIn(validate_rule(detection="AZ-DET-001")["properties"]["query"].strip(), query)
        self.assertIn(query_for("AZ-DET-012").strip(), query)
        self.assertEqual(query.count("let F"), 12)
        self.assertEqual(query.count("| summarize Matches=count()"), 12)
        self.assertTrue(query.endswith("| project DetectionId, Matches\n"))
        self.assertEqual(live.query_fingerprint(), live.query_fingerprint())
        self.assertLessEqual(len(query.encode()), 100000)

    def test_response_requires_exact_ids_columns_integer_counts_and_no_raw_fields(self):
        self.assertEqual(live.aggregate_result(result()), {key: 0 for key in live.DETECTIONS})
        invalid = []
        for count in (-1, True, "0", 2**63):
            response = result()
            response["tables"][0]["rows"][0][1] = count
            invalid.append(response)
        for kind in ("duplicate", "unknown", "missing", "raw", "error", "extra-table"):
            response = result()
            table = response["tables"][0]
            if kind == "duplicate": table["rows"][1] = table["rows"][0]
            elif kind == "unknown": table["rows"][0][0] = "AZ-DET-999"
            elif kind == "missing": table["rows"].pop()
            elif kind == "raw": table["columns"].append({"name": "Caller", "type": "string"})
            elif kind == "error": response["error"] = {"code": "PartialError"}
            else: response["tables"].append(copy.deepcopy(table))
            invalid.append(response)
        for response in invalid:
            with self.subTest(response=invalid.index(response)), self.assertRaises(ValueError):
                live.aggregate_result(response)

    def test_bad_approval_or_absent_pin_stops_before_authentication(self):
        self.approval.write_text(json.dumps({"sha256": "wrong", "allow_one_aggregate_query": True}), encoding="utf-8")
        with patch.object(live, "az_json") as auth, self.assertRaises(ValueError):
            live.run(True)
        auth.assert_not_called()
        self.approval.write_text(json.dumps({"sha256": live.query_fingerprint(), "allow_one_aggregate_query": True}), encoding="utf-8")
        self.pin.unlink()
        with patch.object(live, "az_json") as auth, self.assertRaises(OSError):
            live.run(True)
        auth.assert_not_called()

    def test_pinned_account_mismatch_has_no_token_or_http_fallback(self):
        mismatch = self.auth()[0]
        mismatch["tenantId"] = SUBSCRIPTION
        with patch.object(live, "az_json", return_value=mismatch) as auth, patch.object(live.urllib.request, "build_opener") as network, self.assertRaises(ValueError):
            live.run(True)
        self.assertEqual(auth.call_count, 1)
        network.assert_not_called()
        self.assertFalse(self.ledger.exists())

    def test_ci_and_unreviewed_state_cannot_use_personal_verification_path(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch.object(live, "az_json") as auth, self.assertRaises(ValueError):
            live.run(True)
        auth.assert_not_called()
        with patch.object(live, "_git_clean_main", side_effect=ValueError("unreviewed branch")), patch.object(live, "az_json") as auth, self.assertRaises(ValueError):
            live.run(True)
        auth.assert_not_called()

    def test_success_posts_exactly_one_bounded_query_and_blocks_replay(self):
        with patch.object(live, "az_json", side_effect=self.auth()) as auth, patch.object(live.urllib.request, "build_opener") as factory:
            opener = factory.return_value
            opener.open.side_effect = [Response(self.metadata()), Response(result())]
            report = live.run(True)
        self.assertEqual(opener.open.call_count, 2)
        get = opener.open.call_args_list[0].args[0]
        post = opener.open.call_args_list[1].args[0]
        self.assertEqual(get.get_method(), "GET")
        self.assertEqual(post.get_method(), "POST")
        self.assertTrue(post.full_url.startswith("https://api.loganalytics.azure.com/v1/workspaces/"))
        self.assertEqual(json.loads(post.data), {"query": live.fixed_query(), "timespan": "PT1H"})
        self.assertEqual(report["detections_validated"], 12)
        self.assertEqual(report["raw_events_returned"], 0)
        self.assertIsNone(report["measured_false_positive_rate"])
        self.assertNotIn(CUSTOMER, json.dumps(report))
        self.assertNotIn(SUBSCRIPTION, json.dumps(report))
        self.assertNotIn("private-", json.dumps(report))
        self.assertTrue(json.loads(self.ledger.read_text(encoding="utf-8"))["completed"])
        self.assertTrue(self.report.exists())
        self.assertIn(("account", "get-access-token", "--resource", "https://api.loganalytics.io"), [call.args for call in auth.call_args_list])
        with patch.object(live, "az_json") as auth, self.assertRaises(ValueError):
            live.run(True)
        auth.assert_not_called()

    def test_metadata_mismatch_stops_before_attempt_claim_or_query_token(self):
        bad = self.metadata()
        bad["id"] += "-wrong"
        with patch.object(live, "az_json", side_effect=self.auth()) as auth, patch.object(live, "request_json", return_value=bad) as request, self.assertRaises(ValueError):
            live.run(True)
        self.assertEqual(auth.call_count, 2)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.args[0], "GET")
        self.assertFalse(self.ledger.exists())

    def test_partial_or_ambiguous_failure_preserves_consumed_attempt(self):
        for failure in (live.QueryFailure("query", ("Timeout",)), result() | {"error": {"code": "PartialError"}}):
            with self.subTest(failure=type(failure).__name__):
                if self.ledger.exists(): self.ledger.unlink()
                with patch.object(live, "az_json", side_effect=self.auth()), patch.object(live, "request_json", side_effect=[self.metadata(), failure]), self.assertRaises(ValueError):
                    live.run(True)
                ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
                self.assertFalse(ledger["completed"])
                self.assertEqual(ledger["query_attempts"], 1)
                self.assertFalse(self.report.exists())
                with patch.object(live, "az_json") as auth, self.assertRaises(ValueError):
                    live.run(True)
                auth.assert_not_called()

    def test_http_error_exposes_codes_only_and_never_follows_redirects(self):
        body = {"error": {"code": "BadArgumentError", "message": "private-identity private-query", "innererror": {"code": "SemanticError", "message": "private event"}}}
        failure = urllib.error.HTTPError("https://example.invalid", 400, "private-response", {}, io.BytesIO(json.dumps(body).encode()))
        with patch.object(live.urllib.request, "build_opener") as factory:
            factory.return_value.open.side_effect = failure
            with self.assertRaises(live.QueryFailure) as caught:
                live.request_json("POST", "https://example.invalid", "private-token", {}, "fixed query")
        self.assertEqual(caught.exception.codes, ("BadArgumentError", "SemanticError"))
        self.assertNotIn("private", str(caught.exception))
        self.assertIsInstance(factory.call_args.args[0], live.NoRedirect)
        self.assertEqual(factory.return_value.open.call_count, 1)

    def test_transport_and_oversized_invalid_json_responses_do_not_retry(self):
        for value in (Response(b"x" * (live.MAX_RESPONSE + 1)), Response(b"invalid json"), urllib.error.URLError("private host")):
            with self.subTest(value=type(value).__name__), patch.object(live.urllib.request, "build_opener") as factory:
                factory.return_value.open.side_effect = value if isinstance(value, Exception) else None
                factory.return_value.open.return_value = value
                with self.assertRaises(live.QueryFailure) as caught:
                    live.request_json("POST", "https://example.invalid", "private-token", {})
                self.assertNotIn("private", str(caught.exception))
                self.assertEqual(factory.return_value.open.call_count, 1)

    def test_shared_cli_diagnostic_messages_are_not_echoed(self):
        with patch.object(live, "az_json", side_effect=ValueError("private account telemetry and query")), self.assertRaises(live.QueryFailure) as caught:
            live.safe_az("account", "show")
        self.assertEqual(caught.exception.codes, ("AzureCLIError",))
        self.assertNotIn("private", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
