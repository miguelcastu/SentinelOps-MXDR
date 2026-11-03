"""AMA maintenance is not a missing-data alarm or an invented health proof."""
import copy
import json
from pathlib import Path
import unittest

from platform_health.ama import pilot_observation
from platform_health.demo import NOW, ama_observation, ama_scenarios, baseline, scenarios
from platform_health.engine import policies, report


ROOT = Path(__file__).resolve().parents[1]


def ama_result(observation, as_of=NOW):
    snapshot = baseline()
    snapshot["sources"][2] = observation
    return report(snapshot, as_of)["sources"][2]


class TestAMAHealth(unittest.TestCase):
    def test_inventory_and_policy_are_coordinated_and_old_scenarios_remain(self):
        policy, inventory = policies()
        self.assertEqual(set(policy["sources"]), {"azure-activity", "synthetic-authentication", "ama-linux-syslog"})
        self.assertEqual([s["id"] for s in inventory], ["azure-activity", "synthetic-authentication", "ama-linux-syslog"])
        self.assertEqual(len(scenarios()), 11)
        self.assertEqual(len(ama_scenarios()), 5)
        for case in ama_scenarios():
            with self.subTest(scenario=case["scenario"]):
                value = report(case["snapshot"], NOW)["sources"][2]
                self.assertEqual(value["state"], case["expected"])

    def test_fresh_planned_shutdown_is_unknown_even_if_metrics_are_complete(self):
        for metrics in (False, True):
            value = ama_result(ama_observation(complete_metrics=metrics))
            self.assertEqual((value["state"], value["reason"]), ("Unknown", "planned_maintenance"))
            self.assertTrue(value["operational_evidence_fresh"])

    def test_running_requires_complete_fresh_health_metrics(self):
        running = ama_observation(machine_state="running", complete_metrics=True)
        self.assertEqual(ama_result(running)["state"], "Healthy")
        running["query_status"] = "partial"
        self.assertEqual(ama_result(running)["state"], "Unknown")
        running["query_status"] = "success"
        running["latency_p95_seconds"] = None
        self.assertEqual(ama_result(running)["reason"], "missing_metrics")

    def test_static_inventory_cannot_imply_fresh_machine_state(self):
        running = ama_observation(machine_state="running", complete_metrics=True)
        running["operation_context"] = None
        value = ama_result(running)
        self.assertEqual((value["state"], value["reason"]), ("Unknown", "operation_unknown"))
        self.assertFalse(value["operational_evidence_fresh"])

    def test_stale_maintenance_context_cannot_suppress_unknown_current_state(self):
        stopped = ama_observation(complete_metrics=True)
        stopped["operation_context"]["observed_at"] = "2026-10-18T11:44:59Z"
        value = ama_result(stopped)
        self.assertEqual((value["state"], value["reason"]), ("Unknown", "stale_operation_context"))
        self.assertFalse(value["operational_evidence_fresh"])

    def test_future_machine_observation_is_clock_problem_not_healthy_maintenance(self):
        stopped = ama_observation()
        stopped["operation_context"]["observed_at"] = "2026-10-18T12:02:00Z"
        self.assertEqual(ama_result(stopped)["reason"], "clock_inconsistent")

    def test_machine_context_cannot_be_attached_to_an_unrelated_source(self):
        snapshot = baseline()
        snapshot["sources"][0]["operation_context"] = copy.deepcopy(snapshot["sources"][2]["operation_context"])
        with self.assertRaises(ValueError):
            report(snapshot, NOW)

    def test_recorded_pilot_does_not_invent_schema_latency_or_zero_query_counts(self):
        pilot = json.loads((ROOT / "evidence/local-linux-ama/ingestion.sanitized.json").read_text(encoding="utf-8"))
        shutdown = json.loads((ROOT / "evidence/local-linux-ama/shutdown.sanitized.json").read_text(encoding="utf-8"))
        observation = pilot_observation(pilot, shutdown)
        value = ama_result(observation, shutdown["observed_utc"])
        self.assertEqual(value["reason"], "planned_maintenance")
        self.assertEqual(value["query_status"], "not_collected")
        self.assertEqual(value["pilot_evidence"]["total_events"], 10)
        self.assertEqual(value["pilot_evidence"]["distinct_events"], 10)
        self.assertEqual(value["pilot_evidence"]["billable_bytes"], 2600)
        self.assertEqual(value["pilot_evidence"]["query_attempts"], 2)
        self.assertFalse(value["telemetry_metrics_complete"])
        for field in ("total_events", "distinct_events", "schema_errors", "mapping_errors", "latency_p95_seconds", "billable_bytes", "validity_ratio"):
            self.assertIsNone(value[field])
        self.assertEqual(ama_result(observation, "2026-11-03T12:00:00Z")["reason"], "stale_operation_context")

    def test_fresh_running_pilot_counts_alone_are_not_a_healthy_source(self):
        observation = copy.deepcopy(ama_scenarios()[1]["snapshot"]["sources"][2])
        result = ama_result(observation)
        self.assertEqual((result["state"], result["reason"]), ("Unknown", "pilot_metrics_only"))
        self.assertIsNone(result["schema_errors"])
        self.assertIsNone(result["latency_p95_seconds"])

    def test_pilot_adapter_rejects_wrong_machine_or_extra_raw_data(self):
        pilot = json.loads((ROOT / "evidence/local-linux-ama/ingestion.sanitized.json").read_text(encoding="utf-8"))
        shutdown = json.loads((ROOT / "evidence/local-linux-ama/shutdown.sanitized.json").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            pilot_observation(pilot, dict(shutdown, machine="other-machine"))
        with self.assertRaises(ValueError):
            pilot_observation(dict(pilot, raw_messages=["private log"]), shutdown)
        observation = pilot_observation(pilot, shutdown)
        observation["pilot_evidence"]["complete_health_metrics"] = True
        with self.assertRaises(ValueError):
            ama_result(observation, shutdown["observed_utc"])

    def test_no_ama_batch_or_continuous_heartbeat_is_silently_authorized(self):
        observation = ama_observation(machine_state="running", complete_metrics=True)
        observation.update(expected_events=10, expected_by=NOW)
        with self.assertRaises(ValueError):
            ama_result(observation)

    def test_unmeasured_ama_cost_keeps_coverage_partial_and_rba_source_names_separate(self):
        result = report(baseline(), NOW)
        self.assertEqual(result["coverage"]["inventoried_sources"], 3)
        self.assertEqual(result["coverage"]["inventory_cloud_sources"], 2)
        self.assertEqual(result["coverage"]["queried_sources"], 2)
        self.assertFalse(result["cost"]["complete"])
        self.assertEqual(result["cost"]["observed_billable_bytes"], 9600)
        from rba.model import SOURCES
        self.assertNotIn("ama-linux-syslog", SOURCES)


if __name__ == "__main__":
    unittest.main()
