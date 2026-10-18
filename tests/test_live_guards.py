"""Verify fixed query requests, privacy and opt-in gates without a cloud session."""
import contextlib
import io
import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.azure_guard import az_json
from scripts.validate_live import live

WORKSPACE_ID = "/subscriptions/11111111-1111-4111-8111-111111111111/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
CUSTOMER_ID = "55555555-5555-4555-8555-555555555555"


class TestLiveGuards(unittest.TestCase):
    def test_no_opt_in_means_no_azure_calls(self):
        with patch.dict(os.environ, {}, clear=True), patch("scripts.validate_live.az_json") as az:
            with self.assertRaises(ValueError):
                live()
            az.assert_not_called()

    def test_fixed_workspace_and_queries_only_print_aggregates(self):
        calls = []

        def fake_az(*args):
            calls.append(args)
            if "get" in args:
                return {"id": WORKSPACE_ID, "location": "westeurope", "properties": {"customerId": CUSTOMER_ID}}
            self.assertIn("post", args)
            self.assertEqual(args[args.index("--url") + 1], f"https://api.loganalytics.io/v1/workspaces/{CUSTOMER_ID}/query")
            self.assertEqual(args[args.index("--resource") + 1], "https://api.loganalytics.io")
            body = json.loads(Path(args[args.index("--body") + 1].removeprefix("@")).read_text())
            self.assertEqual(body["timespan"], "PT1H")
            self.assertEqual(set(body), {"query", "timespan"})
            names = ["Mismatches"] if "let Actual" in body["query"] else ["TotalEvents", "DiagnosticChanges"]
            return {"tables": [{"columns": [{"name": n} for n in names], "rows": [[0] * len(names)]}]}

        output = io.StringIO()
        with patch.dict(os.environ, {"SENTINEL_LIVE_VALIDATION_APPROVED": "true"}, clear=True), patch("scripts.validate_live.context", return_value=WORKSPACE_ID), patch("scripts.validate_live.az_json", side_effect=fake_az), contextlib.redirect_stdout(output):
            live()
        self.assertEqual(len(calls), 3)
        self.assertNotIn(CUSTOMER_ID, output.getvalue())
        self.assertNotIn("Caller", output.getvalue())
        self.assertIn('"Mismatches": 0', output.getvalue())

    def test_wrong_workspace_stops_before_query(self):
        with patch.dict(os.environ, {"SENTINEL_LIVE_VALIDATION_APPROVED": "true"}, clear=True), patch("scripts.validate_live.context", return_value=WORKSPACE_ID), patch("scripts.validate_live.az_json", return_value={"id": "/wrong"}) as az:
            with self.assertRaises(ValueError):
                live()
            self.assertEqual(az.call_count, 1)

    def test_kusto_mismatch_fails_the_run(self):
        workspace = {"id": WORKSPACE_ID, "location": "westeurope", "properties": {"customerId": CUSTOMER_ID}}
        health = {"tables": [{"columns": [{"name": "TotalEvents"}, {"name": "DiagnosticChanges"}], "rows": [[0, 0]]}]}
        mismatch = {"tables": [{"columns": [{"name": "Mismatches"}], "rows": [[1]]}]}
        with patch.dict(os.environ, {"SENTINEL_LIVE_VALIDATION_APPROVED": "true"}, clear=True), patch("scripts.validate_live.context", return_value=WORKSPACE_ID), patch("scripts.validate_live.az_json", side_effect=[workspace, health, mismatch]), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "fixture mismatch"):
                live()


class TestAzureErrorPrivacy(unittest.TestCase):
    def test_azure_errors_are_not_echoed(self):
        response = subprocess.CompletedProcess([], 1, stdout="sensitive stdout", stderr="sensitive identity and logs")
        with patch("scripts.azure_guard.subprocess.run", return_value=response):
            with self.assertRaises(ValueError) as caught:
                az_json("rest", "--method", "get", "--url", "https://management.azure.com/example")
        self.assertNotIn("sensitive", str(caught.exception))

    def test_timeout_does_not_expose_command_or_retry(self):
        with patch("scripts.azure_guard.subprocess.run", side_effect=subprocess.TimeoutExpired("sensitive target", 90)) as process:
            with self.assertRaises(ValueError) as caught:
                az_json("account", "show")
        self.assertNotIn("sensitive", str(caught.exception))
        self.assertEqual(process.call_count, 1)
