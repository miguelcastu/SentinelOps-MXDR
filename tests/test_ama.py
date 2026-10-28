"""Meaningful boundaries of the fixed low-volume AMA source contract."""
import copy
import unittest
from ama.plan import resources, validate_dcr, public_plan
from ama.pilot import messages, MAX_BYTES

WORKSPACE = "/subscriptions/11111111-1111-4111-8111-111111111111/resourceGroups/rg-sentinelops-mxdr/providers/Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw"


class TestAMABoundaries(unittest.TestCase):
    def test_broad_facility_severity_stream_or_extra_destination_is_rejected(self):
        for mutation in (lambda b: b["properties"]["dataSources"]["syslog"][0].update(facilityNames=["*"]),
                         lambda b: b["properties"]["dataSources"]["syslog"][0].update(logLevels=["Info"]),
                         lambda b: b["properties"]["dataFlows"][0].update(streams=["Microsoft-Perf"]),
                         lambda b: b["properties"]["destinations"]["logAnalytics"].append({"name": "other", "workspaceResourceId": "other"})):
            value = copy.deepcopy(resources(WORKSPACE)["dcr"])
            mutation(value)
            with self.assertRaises(ValueError):
                validate_dcr(value, WORKSPACE)

    def test_valid_plan_targets_one_owned_machine_and_existing_workspace(self):
        value = resources(WORKSPACE)
        validate_dcr(value["dcr"], WORKSPACE)
        self.assertTrue(value["machine_id"].endswith("/Microsoft.HybridCompute/machines/lab-sentinelops-linux-01"))
        self.assertEqual(value["association"]["properties"]["dataCollectionRuleId"], value["dcr_id"])
        self.assertEqual(value["extension"]["properties"]["publisher"], "Microsoft.Azure.Monitor")
        self.assertFalse(public_plan()["azure_changes_executed"])

    def test_other_resource_group_workspace_or_arbitrary_input_is_rejected(self):
        for value in (WORKSPACE.replace("rg-sentinelops-mxdr", "other"), WORKSPACE.replace("law-sentinelops-mxdr-euw", "other"),
                      WORKSPACE.replace("11111111-1111-4111-8111-111111111111", "-" * 36), "https://example.com", "", None):
            with self.assertRaises(ValueError):
                resources(value)

    def test_pilot_is_finite_unique_and_rejects_log_or_shell_injection(self):
        batch = messages("a" * 48)
        self.assertEqual(len(batch), 10)
        self.assertEqual(len(set(batch)), 10)
        self.assertLessEqual(sum(len((message + "\n").encode()) for message in batch), MAX_BYTES)
        for run_id in ("short", "a" * 49, "pilot-id\nsecond-line", "$(whoami)", "pilot;command", None):
            with self.assertRaises(ValueError):
                messages(run_id)
