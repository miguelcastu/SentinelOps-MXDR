"""Synthetic filter cases, rejected rule mutations and safe result handling."""
import copy
import json
import unittest

from scripts.validate_detection import KQL, ROOT, parse_predicates, validate_rule
from scripts.validate_live import aggregate_result, synthetic_query


class TestDetection(unittest.TestCase):
    def setUp(self):
        self.rule = validate_rule()
        self.query = KQL.read_text(encoding="utf-8")

    def test_synthetic_positive_negative_and_boundary_cases(self):
        # A limited interpreter of the parsed filters, not an offline Kusto engine.
        seconds, predicates = parse_predicates(self.query)
        fixtures = json.loads((ROOT / "tests/fixtures/az_det_001.json").read_text())
        self.assertEqual(len({case["id"] for case in fixtures}), len(fixtures))
        for case in fixtures:
            with self.subTest(case=case["id"]):
                event = {"OperationNameValue": case["operation"], "ActivityStatusValue": case["status"]}
                matches = -seconds <= case["offset"] <= 0 and all(
                    event[column].casefold() in values for column, values in predicates)
                self.assertEqual(matches, case["expected"])

    def test_reject_unsafe_or_invalid_rest_bodies(self):
        mutations = [
            ("kind", "Fusion"), ("type", "Microsoft.Compute/virtualMachines"),
            ("resources", []), ("id", "/unapproved/target"), ("name", "duplicate"),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                rule = copy.deepcopy(self.rule)
                rule[key] = value
                with self.assertRaises(ValueError):
                    validate_rule(rule)
        mutations = [
            ("enabled", True), ("enabled", 0), ("enabled", "false"),
            ("queryPeriod", "P7D"), ("queryFrequency", "PT1M"),
            ("triggerThreshold", True), ("playbook", "paid"),
            ("entityMappings", [{"entityType": "Account", "fieldMappings": []}]),
            ("incidentConfiguration", {"createIncident": 0, "groupingConfiguration": {
                "enabled": False, "reopenClosedIncident": False,
                "lookbackDuration": "PT1H", "matchingMethod": "AllEntities"}}),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                rule = copy.deepcopy(self.rule)
                rule["properties"][key] = value
                with self.assertRaises(ValueError):
                    validate_rule(rule)

    def test_missing_required_fields(self):
        for key in self.rule["properties"]:
            with self.subTest(key=key):
                rule = copy.deepcopy(self.rule)
                del rule["properties"][key]
                with self.assertRaises(ValueError):
                    validate_rule(rule)

    def test_reject_kql_source_drift(self):
        self.rule["properties"]["query"] += "\n| take 100"
        with self.assertRaises(ValueError):
            validate_rule(self.rule)

    def test_reject_unsafe_kql_even_when_json_and_source_match(self):
        queries = [
            self.query.replace("ago(1h)", "ago(24h)"),
            self.query.replace('"Success", "Succeeded"', '"Success", "Failed"'),
            self.query.replace("in~", "contains", 1),
            self.query.replace("AzureActivity", 'workspace("other").AzureActivity', 1),
            self.query + "| evaluate python()\n",
            self.query.replace("| project TimeGenerated", "| project Claims_d, TimeGenerated"),
        ]
        for query in queries:
            with self.subTest(query=query):
                self.rule["properties"]["query"] = query
                with self.assertRaises(ValueError):
                    validate_rule(self.rule, query)

    def test_synthetic_kql_uses_actual_detection_and_only_fake_inputs(self):
        query = synthetic_query()
        self.assertIn(self.query.split("\n", 1)[1].strip(), query)
        self.assertNotIn("AzureActivity", query)
        self.assertIn("| summarize Mismatches=count()", query)
        self.assertIn("join kind=leftanti", query)


class TestAggregatePrivacy(unittest.TestCase):
    @staticmethod
    def response(columns, rows):
        return {"tables": [{"columns": [{"name": name} for name in columns], "rows": rows}]}

    def test_accept_counts_including_zero(self):
        self.assertEqual(aggregate_result(self.response(["TotalEvents"], [[0]]), ["TotalEvents"]), {"TotalEvents": 0})

    def test_reject_raw_and_partial_results(self):
        invalid = [
            self.response(["Caller"], [["synthetic@example.invalid"]]),
            self.response(["TotalEvents"], [["raw data"]]),
            self.response(["TotalEvents"], [[True]]),
            self.response(["TotalEvents"], [[-1]]),
            self.response(["TotalEvents"], [[1], [2]]),
            {"error": {"code": "PartialError"}, **self.response(["TotalEvents"], [[1]])},
            {"tables": []},
        ]
        for response in invalid:
            with self.subTest(response=response):
                with self.assertRaises(ValueError):
                    aggregate_result(response, ["TotalEvents"])
