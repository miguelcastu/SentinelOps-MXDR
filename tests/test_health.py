"""Health behavior, false-alarm prevention, readonly collection and report privacy."""
import copy
import io
import json
import os
import tempfile
import unittest
from datetime import datetime
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from platform_health.collect import collect, deployment_checks
from platform_health.demo import NOW, baseline, scenarios
from platform_health.engine import report as evaluate_report
from platform_health.logs import COLUMNS, observation
from platform_health.render import dashboard, write_report
from scripts.validate_detection import DETECTIONS, validate_rule

WORKSPACE = "/subscriptions/11111111-1111-4111-8111-111111111111/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"
FIRST_ID = "22222222-2222-4222-8222-222222222222"


def report(snapshot, now=NOW):
    return evaluate_report(snapshot, now)


def cloud_rules():
    return {"value": [dict(validate_rule(detection=key), name=identifier, id=WORKSPACE +
        "/providers/Microsoft.SecurityInsights/alertRules/" + identifier) for key, identifier in
        (("AZ-DET-001", FIRST_ID), ("AZ-DET-002", DETECTIONS["AZ-DET-002"]["resource_uuid"]))]}


class TestHealthEvaluation(unittest.TestCase):
    def test_all_safe_fault_scenarios_classify_as_expected(self):
        self.assertEqual(len(scenarios()), 11)
        for case in scenarios():
            value = report(case["snapshot"])
            target = next((s for s in value["sources"] if s["source_id"] == case["target"]), None)
            target = target or next(c for c in value["checks"] if c["id"] == case["target"])
            with self.subTest(scenario=case["scenario"]):
                self.assertEqual(target["state"], case["expected"])

    def test_quiet_event_source_never_missing_and_zero_ratios_are_unknown(self):
        case = next(c for c in scenarios() if c["scenario"] == "quiet-activity-is-unknown")
        source = report(case["snapshot"])["sources"][0]
        self.assertEqual((source["state"], source["reason"]), ("Unknown", "quiet_event_source"))
        self.assertIsNone(source["validity_ratio"])
        self.assertIsNone(source["uniqueness_ratio"])

    def test_unapproved_batch_has_no_implicit_heartbeat_and_deadline_is_honored(self):
        snapshot = baseline()
        empty = next(c for c in scenarios() if c["scenario"] == "missing-approved-batch")["snapshot"]["sources"][1]
        snapshot["sources"][1] = copy.deepcopy(empty)
        snapshot["sources"][1].update(expected_events=None, expected_by=None)
        self.assertEqual(report(snapshot)["sources"][1]["reason"], "no_active_batch")
        snapshot["sources"][1].update(expected_events=24, expected_by="2026-10-18T12:05:00Z")
        self.assertEqual(report(snapshot)["sources"][1]["reason"], "waiting_batch")
        self.assertEqual(report(snapshot, "2026-10-18T12:05:00Z")["sources"][1]["state"], "Missing")

    def test_stale_evidence_and_errors_cannot_be_reported_healthy(self):
        snapshot = baseline()
        self.assertEqual(report(snapshot, "2026-10-18T12:16:00Z")["sources"][0]["reason"], "stale_snapshot")
        self.assertTrue(all(c["state"] == "Unknown" for c in report(snapshot, "2026-10-18T12:16:00Z")["checks"]))
        for state in ("error", "partial", "not_authorized", "not_collected"):
            snapshot["sources"][0]["query_status"] = state
            value = report(snapshot)["sources"][0]
            self.assertEqual(value["state"], "Unknown")
            self.assertIsNone(value["total_events"])

    def test_evaluator_defaults_to_current_time_rather_than_trusting_snapshot_time(self):
        with patch('platform_health.engine.datetime') as clock:
            clock.now.return_value = datetime.fromisoformat('2026-10-18T12:16:00+00:00')
            clock.fromisoformat.side_effect = datetime.fromisoformat
            self.assertEqual(evaluate_report(baseline())['sources'][0]['reason'], 'stale_snapshot')

    def test_latency_threshold_is_source_specific_and_inclusive(self):
        snapshot = baseline()
        snapshot["sources"][0]["latency_p95_seconds"] = 900
        self.assertEqual(report(snapshot)["sources"][0]["state"], "Healthy")
        snapshot["sources"][0]["latency_p95_seconds"] = 901
        self.assertEqual(report(snapshot)["sources"][0]["state"], "Delayed")
        snapshot["sources"][1]["latency_p95_seconds"] = 301
        self.assertEqual(report(snapshot)["sources"][1]["state"], "Delayed")

    def test_old_last_seen_is_insufficient_evidence_without_a_heartbeat(self):
        snapshot = baseline()
        source = snapshot["sources"][0]
        source.update(window_start="2026-10-18T10:00:00Z", last_seen="2026-10-18T10:30:00Z")
        self.assertEqual(report(snapshot)["sources"][0]["reason"], "stale_last_seen")

    def test_clock_skew_and_negative_latency_are_visible_quality_failures(self):
        snapshot = baseline()
        snapshot["sources"][0]["negative_latency_events"] = 1
        self.assertEqual(report(snapshot)["sources"][0]["reason"], "clock_inconsistent")
        self.assertEqual(report(baseline(), "2026-10-18T11:58:00Z")["sources"][0]["state"], "Misconfigured")

    def test_invalid_counts_unknown_fields_naive_time_and_unbounded_windows_fail_closed(self):
        mutations = ({"total_events": True}, {"distinct_events": 999}, {"billable_bytes": -1},
                     {"latency_p95_seconds": float('nan')}, {"raw_caller": "private-user"},
                     {"observed_at": "2026-10-18T12:00:00"}, {"window_start": "2026-10-16T00:00:00Z"},
                     {"hourly_volume": [{"start": "2026-10-18T11:00:00Z", "events": 999}]})
        for mutation in mutations:
            snapshot = baseline()
            snapshot["sources"][0].update(mutation)
            with self.subTest(mutation=list(mutation)), self.assertRaises(ValueError):
                report(snapshot)

    def test_config_agreement_does_not_claim_active_coverage_or_invoice(self):
        value = report(baseline())
        self.assertEqual(value["rules"]["active"], 0)
        self.assertEqual(value["rules"]["intentionally_disabled"], 2)
        self.assertFalse(value["limits"]["runtime_health_verified"])
        self.assertFalse(value["cost"]["invoice_verified"])
        self.assertEqual(value["cost"]["observed_billable_bytes"], 9600)
        snapshot = baseline()
        snapshot["sources"][1]["query_status"] = "not_collected"
        cost = report(snapshot)["cost"]
        self.assertFalse(cost["complete"])
        self.assertEqual(cost["known_sources"], 1)

    def test_duplicate_or_uninventoried_sources_and_inconsistent_rule_counts_rejected(self):
        for mutate in (lambda s:s['sources'].append(s['sources'][0]),
                       lambda s:s['sources'][0].update(source_id='unapproved-source'),
                       lambda s:s['rules'].update(active=3)):
            snapshot = baseline()
            mutate(snapshot)
            with self.assertRaises(ValueError):
                report(snapshot)


class TestHealthCollection(unittest.TestCase):
    def collect_with(self, responses, github_payload=None):
        with patch.dict(os.environ, {"SENTINEL_RULE_ID": FIRST_ID, "GH_TOKEN": "fake-token"}, clear=True), \
                patch("platform_health.collect.context", return_value=WORKSPACE), \
                patch("platform_health.collect.az_json", side_effect=responses) as az, \
                patch("platform_health.collect.github_runs", return_value=github_payload or {}):
            result = collect()
        return result, az

    def workspace(self):
        return {"id":WORKSPACE, "location":"westeurope", "properties":{
            "retentionInDays":30, "workspaceCapping":{"dailyQuotaGb":0.1}, "sku":{"name":"pergb2018"}}}

    def test_collector_uses_only_two_existing_authorized_gets_and_never_logs_raw_data(self):
        snapshot, az = self.collect_with([self.workspace(), cloud_rules()])
        value = report(snapshot, snapshot["observed_at"])
        self.assertEqual(az.call_count, 2)
        self.assertTrue(all(call.args[:3] == ("rest", "--method", "get") for call in az.call_args_list))
        self.assertTrue(all('api.loganalytics' not in str(call) and 'diagnosticSettings' not in str(call) for call in az.call_args_list))
        self.assertEqual(value["rules"],dict(expected=2,present=2,matching=2,active=0,intentionally_disabled=2))
        self.assertTrue(all(s["state"] == "Unknown" for s in value["sources"]))
        self.assertNotIn(WORKSPACE, json.dumps(value))
        self.assertNotIn(FIRST_ID, json.dumps(value))

    def test_unapproved_context_stops_before_any_requests(self):
        with patch("platform_health.collect.context", side_effect=ValueError("blocked")), \
                patch("platform_health.collect.az_json") as az:
            with self.assertRaises(ValueError):
                collect()
            az.assert_not_called()

    def test_wrong_workspace_stops_and_does_not_query_other_resources(self):
        workspace = self.workspace()
        workspace['id'] = WORKSPACE + '-unexpected'
        snapshot, az = self.collect_with([workspace])
        self.assertEqual(az.call_count, 1)
        self.assertEqual(report(snapshot, snapshot["observed_at"])["state"], "Misconfigured")

    def test_enabled_missing_duplicate_drift_or_paginated_rule_inventory_cannot_pass(self):
        for change in ("enabled", "missing", "duplicate", "query", "pagination"):
            listing = cloud_rules()
            if change == "enabled":listing['value'][0]['properties']['enabled']=True
            elif change == "missing":listing['value'].pop(0)
            elif change == "duplicate":listing['value'].append(copy.deepcopy(listing['value'][0]))
            elif change == "query":listing['value'][0]['properties']['query']='unapproved query'
            else:listing['nextLink']='https://example.invalid/next'
            snapshot, _ = self.collect_with([self.workspace(),listing])
            check = next(c for c in snapshot['checks'] if c['id']=='AZ-DET-001')
            self.assertEqual(check['state'], 'Unknown' if change=='pagination' else 'Misconfigured')

    def test_read_errors_remain_unknown_and_do_not_leak_exception_details(self):
        snapshot, _ = self.collect_with([ValueError("private-token"), ValueError("private-identity")])
        text = json.dumps(report(snapshot, snapshot["observed_at"]))
        self.assertNotIn('private-', text)
        self.assertTrue(all(c['state']=='Unknown' for c in snapshot['checks']))

    def test_latest_workflow_status_not_historical_failure_controls_deployment_check(self):
        run = {'path':'.github/workflows/deploy-sentinel.yml@main','head_branch':'main','event':'push','run_number':1,
               'status':'completed','conclusion':'failure'}
        checks = deployment_checks({'workflow_runs':[run,dict(run,run_number=2,conclusion='success')]})
        self.assertEqual(next(c for c in checks if c['id']=='deploy-sentinel.yml')['state'],'Healthy')
        checks = deployment_checks({'workflow_runs':[run,dict(run,run_number=2,status='in_progress')]})
        self.assertEqual(next(c for c in checks if c['id']=='deploy-sentinel.yml')['state'],'Unknown')


class TestHealthEvidenceAndRendering(unittest.TestCase):
    def test_live_drift_writes_report_and_returns_failure_instead_of_silent_success(self):
        from platform_health.__main__ import main
        collector = TestHealthCollection()
        workspace = collector.workspace()
        workspace['properties']['retentionInDays'] = 90
        snapshot, _ = collector.collect_with([workspace, cloud_rules()])
        with tempfile.TemporaryDirectory() as directory, patch('sys.argv',['health','--collect-ci','--output',directory]), \
                patch('platform_health.collect.collect',return_value=snapshot), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(),2)
            self.assertEqual(json.loads(output.getvalue())['state'],'Misconfigured')
            self.assertTrue((Path(directory)/'report.json').exists())

    def test_logs_adapter_accepts_only_one_fixed_aggregate_and_rejects_partial_raw_results(self):
        response = {'tables':[{'columns':[{'name':c} for c in COLUMNS],
                              'rows':[[3,3,3,0,0,0,'2026-10-18T11:58:00Z',480,0]]}]}
        result = observation(response,'azure-activity',NOW,'2026-10-18T11:00:00Z',NOW)
        snapshot=baseline();snapshot['sources'][0]=result
        self.assertEqual(report(snapshot)['sources'][0]['state'],'Healthy')
        for invalid in (dict(response,error={'code':'PartialError'}),{'tables':[]},
                        {'tables':[{'columns':[{'name':'Caller'}],'rows':[['private-identity']]}]}):
            with self.assertRaises(ValueError):
                observation(invalid,'azure-activity',NOW,'2026-10-18T11:00:00Z',NOW)

    def test_reports_are_standalone_escape_values_and_contain_no_external_assets(self):
        value=report(baseline())
        value['sources'][0]['explanation']='<script>alert("unsafe")</script>'
        text=dashboard(value)
        self.assertIn('&lt;script&gt;',text)
        self.assertNotIn('<script>alert(',text)
        self.assertNotIn('src="http',text)
        self.assertIn('id="state"',text)
        with tempfile.TemporaryDirectory() as directory:
            write_report(value,directory)
            self.assertEqual({p.name for p in Path(directory).iterdir()},{'report.json','report.md','dashboard.html'})

    def test_default_demo_never_authenticates_or_touches_network(self):
        from platform_health.__main__ import main
        with tempfile.TemporaryDirectory() as directory, patch('sys.argv',['health','--output',directory]), \
                patch('platform_health.collect.collect') as cloud, patch('urllib.request.OpenerDirector.open') as network, \
                redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(),0)
            self.assertEqual(json.loads(output.getvalue())['fault_scenarios'],11)
            cloud.assert_not_called();network.assert_not_called()

    def test_imported_snapshot_cannot_label_itself_azure_verified_and_is_rechecked_for_staleness(self):
        from platform_health.__main__ import main
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'snapshot.json';snapshot=baseline();snapshot['evidence']='azure-control-plane'
            path.write_text(json.dumps(snapshot))
            with patch('sys.argv',['health','--snapshot',str(path),'--as-of','2026-10-18T12:16:00Z','--output',directory]), redirect_stdout(io.StringIO()):
                self.assertEqual(main(),0)
            value=json.loads((Path(directory)/'report.json').read_text())
            self.assertEqual(value['evidence'],'external-aggregate')
            self.assertEqual(value['sources'][0]['reason'],'stale_snapshot')
