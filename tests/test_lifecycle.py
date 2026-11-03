"""Safety boundaries of the isolated real-scheduler acceptance implementation."""
import copy
import json
import unittest
from unittest.mock import patch

from lifecycle.contract import TITLE, RULE_UUID, close_body, fingerprint, parameters, rule, validate_incident
from scripts.run_lifecycle import disabled, observe


class LifecycleBoundaries(unittest.TestCase):
    def test_no_arbitrary_query_target_or_unbounded_lifetime(self):
        value = rule("1234567890", "2026-11-03T18:00:00Z")
        self.assertFalse(value["properties"]["enabled"])
        self.assertIn("2026-11-03T18:20:00Z", value["properties"]["query"])
        self.assertEqual(parameters(value), ("1234567890", "2026-11-03T18:00:00Z"))
        self.assertNotIn("AzureActivity", value["properties"]["query"])
        self.assertEqual(len(fingerprint()), 64)
        for bad in ["'; union *", "123", "9" * 21]:
            with self.assertRaises(ValueError):
                rule(bad, "2026-11-03T18:00:00Z")
        for key, changed in [("query", "union *"), ("severity", "High"), ("incidentConfiguration", {"createIncident": False})]:
            edited = copy.deepcopy(value)
            edited["properties"][key] = changed
            with self.assertRaises(ValueError):
                parameters(edited)

    def incident(self):
        return {"id": "/lab/providers/Microsoft.SecurityInsights/incidents/11111111-1111-4111-8111-111111111111", "name": "11111111-1111-4111-8111-111111111111", "etag": '"v1"', "properties": {
            "title": TITLE, "relatedAnalyticRuleIds": ["/lab/rule/" + RULE_UUID],
            "additionalData": {"alertsCount": 1}, "status": "New", "severity": "Informational", "firstActivityTimeUtc": "2026-11-03T18:00:00Z"}}

    def test_classification_rejects_unrelated_ambiguous_or_alertless_incidents(self):
        original = self.incident()
        body = close_body(original, "/lab/rule/" + RULE_UUID)
        self.assertEqual(body["etag"], '"v1"')
        self.assertEqual(body["properties"]["classification"], "BenignPositive")
        self.assertEqual(original["properties"]["status"], "New")
        for mutation in [lambda x: x["properties"].update(title="Other incident"),
                         lambda x: x["properties"].update(relatedAnalyticRuleIds=["/other"]),
                         lambda x: x["properties"].update(relatedAnalyticRuleIds=["/lab/rule/"+RULE_UUID,"/other"]),
                         lambda x: x["properties"].update(additionalData={"alertsCount": 0}),
                         lambda x: x.pop("etag")]:
            edited = copy.deepcopy(original)
            mutation(edited)
            with self.assertRaises(ValueError):
                close_body(edited, "/lab/rule/" + RULE_UUID)

    def test_polling_stops_on_matching_actual_alert_and_is_bounded_on_absence(self):
        class Client:
            def __init__(self, present):
                self.present = present
                self.gets = 0
            def request(inner, method, path, body=None):
                if method == "GET":
                    if "/rule/" in path:
                        return rule("1234567890", "2026-11-03T18:00:00Z")
                    inner.gets += 1
                    return {"value": [self.incident()] if inner.present else []}
                return {"value": [{"properties": {"alertDisplayName": TITLE}}]}
        present = Client(True)
        report = observe(present, "/lab", "/lab/rule/" + RULE_UUID, sleep=lambda _: None)
        self.assertTrue(report["scheduled_rule_link_verified"])
        self.assertEqual(present.gets, 1)
        absent = Client(False)
        with patch("builtins.print"):
            with self.assertRaises(ValueError):
                observe(absent, "/lab", "/lab/rule/" + RULE_UUID, sleep=lambda _: None)
        self.assertEqual(absent.gets, 24)

    def test_cleanup_uses_etag_and_does_not_touch_other_rules(self):
        body = rule("1234567890", "2026-11-03T18:00:00Z", True)
        body.update(id="/lab/fixed", etag='"v1"')
        class Client:
            puts = []
            def request(inner, method, path, request=None, missing_ok=False):
                self.assertEqual(path, "/lab/fixed?api-version=2025-09-01")
                if method == "PUT":
                    inner.puts.append(request)
                    body["properties"]["enabled"] = False
                return copy.deepcopy(body)
        client = Client()
        self.assertTrue(disabled(client, "/lab/fixed"))
        self.assertEqual(client.puts[0]["etag"], '"v1"')
        self.assertFalse(client.puts[0]["properties"]["enabled"])
        self.assertTrue(disabled(client, "/lab/fixed"))
        self.assertEqual(len(client.puts), 1)
