"""Synthetic contract, bounded HTTP behavior and schema-drift rejection; no Azure access."""
import json
import unittest
from unittest.mock import Mock, patch

from ingestion.client import (IngestionError, MAX_BATCH_BYTES, MAX_REQUESTS, Reply, batches,
                              destination, rest_post, retry_delay, upload)
from ingestion.config import configuration
from ingestion.events import COLUMNS, generate, normalize, normalize_many, timestamp

ENDPOINT = "https://synthetic.westeurope-1.ingest.monitor.azure.com"
DCR = "dcr-" + "a" * 32
WORKSPACE = "/subscriptions/11111111-1111-4111-8111-111111111111/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"


class TestNormalization(unittest.TestCase):
    def test_deterministic_unique_explicitly_synthetic_source(self):
        source = generate()
        self.assertEqual(source, generate())
        self.assertEqual(len({e["event_id"] for e in source}), 24)
        self.assertEqual(len({e["batch_id"] for e in source}), 1)
        self.assertTrue(all(e["synthetic"] is True for e in source))
        self.assertNotEqual(source[0]["event_id"], generate(seed="another")[0]["event_id"])

    def test_normalization_reconciles_timestamps_and_auth_results(self):
        events = generate(3, "2026-10-18T12:00:00+02:00")
        normalized = normalize_many(events)
        self.assertEqual(normalized[0]["TimeGenerated"], "2026-10-18T10:00:00.000Z")
        self.assertEqual([e["EventResult"] for e in normalized], ["Failure", "Success", "Success"])
        for event in normalized:
            self.assertEqual(set(event), set(COLUMNS))
            self.assertEqual(event["EventStartTime"], event["EventEndTime"])
            self.assertEqual(event["EventSchema"], "Authentication")

    def test_real_data_bad_types_malformed_fields_and_schema_evolution_rejected(self):
        for mutation in ({"synthetic": False}, {"synthetic": 1}, {"event_code": True},
                         {"event_code": 9999}, {"source_ip": "8.8.8.8"}, {"source_ip": "192.0.2.1/24"},
                         {"timestamp": "2026-10-18T10:00:00"}, {"timestamp": "not-a-time"},
                         {"timestamp": "2026-10-18 10:00:00+00:00"}, {"timestamp": "20261018T10:00:00Z"},
                         {"username": "someone@example.test"}, {"unknown": "new-field"}, {"schema_version": "2.0"}):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                normalize(dict(generate(1)[0], **mutation))

    def test_ipv6_documentation_range_and_timezone_boundary(self):
        self.assertEqual(normalize(dict(generate(1)[0], source_ip="2001:db8::1"))["SrcIpAddr"], "2001:db8::1")
        self.assertEqual(timestamp("2026-01-01T00:30:00+01:00"), "2025-12-31T23:30:00.000Z")

    def test_duplicates_mixed_batches_and_oversized_runs_fail_before_network(self):
        for source in ([generate(1)[0]] * 2, generate(1) + generate(1, seed="other"), [], generate(1) * 101):
            with self.subTest(size=len(source)), self.assertRaises(ValueError):
                batches(source)
        for count in (0, 101, True):
            with self.assertRaises(ValueError):
                generate(count)


class TestTransport(unittest.TestCase):
    def send(self, events=None, **kwargs):
        return upload(generate(24) if events is None else events, ENDPOINT, DCR,
                      "synthetic-token", approved=True, **kwargs)

    def test_batch_byte_limits_and_all_events_survive_roundtrip(self):
        result = batches(generate(60))
        self.assertTrue(all(len(payload) <= MAX_BATCH_BYTES for payload in result))
        self.assertLessEqual(len(result) * 3, MAX_REQUESTS)
        self.assertEqual([e for payload in result for e in json.loads(payload)], normalize_many(generate(60)))

    def test_no_approval_bad_endpoint_or_bad_event_performs_no_request(self):
        post = Mock()
        with self.assertRaises(IngestionError):
            upload(generate(), ENDPOINT, DCR, "synthetic-token", post=post)
        for endpoint in ("http://synthetic.westeurope-1.ingest.monitor.azure.com", ENDPOINT + "/path",
                         ENDPOINT + "@evil.example", ENDPOINT + ".evil.example", ENDPOINT + ":443",
                         ENDPOINT + "?target=elsewhere", "https://x.northeurope-1.ingest.monitor.azure.com"):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                upload(generate(), endpoint, DCR, "synthetic-token", approved=True, post=post)
        with self.assertRaises(ValueError):
            self.send(events=[dict(generate(1)[0], source_ip="8.8.8.8")], post=post)
        post.assert_not_called()

    def test_throttle_retry_and_rate_limit_return_only_aggregate_receipt(self):
        post = Mock(side_effect=[Reply(429, "2"), Reply(204), Reply(204)])
        sleep = Mock()
        result = self.send(post=post, sleep=sleep, monotonic=lambda: 0)
        self.assertEqual(result["api_accepted_events"], 24)
        self.assertEqual(result["requests"], result["batches"] + 1)
        self.assertFalse(result["destination_query_verified"])
        self.assertIn(unittest.mock.call(2), sleep.call_args_list)
        self.assertIn(unittest.mock.call(1), sleep.call_args_list)

    def test_byte_and_request_budgets_are_checked_before_any_post(self):
        for setting, limit in (("MAX_RUN_BYTES", 100), ("MAX_REQUESTS", 1)):
            post = Mock()
            with self.subTest(setting=setting), patch("ingestion.client." + setting, limit), self.assertRaises(IngestionError):
                self.send(post=post)
            post.assert_not_called()

    def test_finite_retries_and_no_retry_on_authorization_or_redirect(self):
        for status, count in ((503, 3), (401, 1), (403, 1), (400, 1), (302, 1), (200, 1)):
            post = Mock(return_value=Reply(status))
            with self.subTest(status=status), self.assertRaises(IngestionError):
                self.send(post=post, sleep=lambda _: None)
            self.assertEqual(post.call_count, count)

    def test_retry_after_is_honored_or_stops_instead_of_retrying_too_early(self):
        self.assertEqual(retry_delay("Thu, 01 Jan 1970 00:00:05 GMT", 1, wall_time=lambda: 0), 5)
        for value in ("11", "tomorrow", "999999999999999999999999"):
            post = Mock(return_value=Reply(429, value))
            with self.subTest(value=value), self.assertRaises(IngestionError):
                self.send(post=post, sleep=lambda _: None)
            self.assertEqual(post.call_count, 1)

    def test_transport_error_redacts_tokens_payloads_and_response_details(self):
        post = Mock(side_effect=RuntimeError("sensitive-token raw telemetry"))
        with self.assertRaises(IngestionError) as error:
            self.send(post=post)
        self.assertNotIn("sensitive", str(error.exception))
        self.assertEqual(post.call_count, 1)

    def test_http_transport_disables_redirects_and_sets_timeout(self):
        response = Mock(status=204, headers={})
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = response
        with patch("ingestion.client.urllib.request.build_opener", return_value=opener) as build:
            self.assertEqual(rest_post(destination(ENDPOINT, DCR), "synthetic-token", b"[]").status, 204)
        self.assertEqual(type(build.call_args.args[0]).__name__, "NoRedirect")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 20)


class TestIngestionConfiguration(unittest.TestCase):
    def test_source_dcr_table_types_are_consistent_and_no_workspace_settings_modified(self):
        table, dcr = configuration(WORKSPACE)
        self.assertEqual(set(table["properties"]), {"schema", "plan"})
        self.assertEqual(dcr["kind"], "Direct")
        self.assertNotIn("dataCollectionEndpointId", dcr["properties"])
        self.assertEqual(table["properties"]["schema"]["columns"],
                         dcr["properties"]["streamDeclarations"]["Custom-SentinelOpsAuth"]["columns"])
        self.assertEqual(dcr["properties"]["destinations"]["logAnalytics"][0]["workspaceResourceId"], WORKSPACE)

    def test_other_workspace_and_schema_drift_fail_closed(self):
        with self.assertRaises(ValueError):
            configuration(WORKSPACE.replace("law-sentinelops-mxdr-euw", "other-workspace"))
        from ingestion.config import ROOT
        original = (ROOT / "infrastructure/ingestion/table.json").read_text()
        changed = json.loads(original)
        changed["properties"]["schema"]["columns"][0]["type"] = "string"
        with patch("pathlib.Path.read_text", return_value=json.dumps(changed)), self.assertRaises(ValueError):
            configuration(WORKSPACE)
