"""Safety boundaries of the isolated real-scheduler acceptance implementation."""
import copy
import json
import unittest
from unittest.mock import patch

from lifecycle.contract import TITLE, RULE_UUID, close_body, fingerprint, parameters, rule, validate_incident
from scripts.run_lifecycle import disabled, observe, recovery_current, execute


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
                self.assertEqual(method, 'GET', 'CI observation must not require detailed alert POST access')
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

    def test_incident_alert_count_is_bounded_and_not_a_boolean(self):
        for count in [True, 0, -1, 6, '1', None]:
            value=self.incident()
            value['properties']['additionalData']['alertsCount']=count
            with self.assertRaises(ValueError):
                validate_incident(value,'/lab/rule/'+RULE_UUID)

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

    def test_recovery_is_bound_to_one_prior_disabled_alertless_test(self):
        import hashlib
        value = rule("1234567890", "2026-11-03T18:00:00Z")
        value.update(id="/lab/fixed", etag='"v1"')
        class Client:
            def request(inner, method, path, body=None):
                self.assertEqual(method, "GET")
                return {"value": []} if '/incidents?' in path else copy.deepcopy(value)
        digest = hashlib.sha256(value["properties"]["query"].encode()).hexdigest()
        with patch.dict('os.environ', {'SENTINEL_LIFECYCLE_RECOVERY_REFERENCE': '0'*64}):
            with self.assertRaises(ValueError):
                recovery_current(Client(), '/lab', '/lab/fixed')
        with patch.dict('os.environ', {'SENTINEL_LIFECYCLE_RECOVERY_REFERENCE': digest}):
            self.assertEqual(recovery_current(Client(), '/lab', '/lab/fixed'), value)
            value['properties']['enabled'] = True
            with self.assertRaises(ValueError):
                recovery_current(Client(), '/lab', '/lab/fixed')

    def test_query_execution_gate_has_no_table_or_wildcard_data_permission(self):
        from lifecycle.contract import QUERY_ACTIONS
        self.assertEqual(QUERY_ACTIONS, ['Microsoft.OperationalInsights/workspaces/query/read'])
        self.assertFalse(any('query/*/' in a or '/tables/' in a for a in QUERY_ACTIONS))

    def test_cleanup_waits_for_readback_without_repeating_mutation(self):
        value = rule("1234567890", "2026-11-03T18:00:00Z", True)
        value.update(id='/lab/fixed', etag='"v1"')
        class Client:
            puts = 0
            gets = 0
            def request(inner, method, path, request=None, missing_ok=False):
                if method == 'PUT':
                    inner.puts += 1
                    return None
                inner.gets += 1
                result = copy.deepcopy(value)
                result['properties']['enabled'] = inner.gets < 3
                return result
        client = Client()
        with patch('scripts.run_lifecycle.time.sleep') as delay:
            self.assertTrue(disabled(client, '/lab/fixed'))
        self.assertEqual(client.puts, 1)
        self.assertEqual(client.gets, 3)
        delay.assert_called_once_with(3)

    def test_rejected_enable_always_leaves_test_disabled_and_does_not_touch_baseline(self):
        workspace='/lab'
        target=workspace+'/providers/Microsoft.SecurityInsights/alertRules/'+RULE_UUID
        baseline=[{'name':f'rule-{n}', 'kind':'Scheduled', 'properties':{'enabled':False}} for n in range(12)]
        baseline.append({'name':'fusion', 'kind':'Fusion','properties':{'enabled':True}})
        class Client:
            current=None
            writes=[]
            reads=[]
            def request(inner, method, path, body=None, missing_ok=False):
                if method=='PUT':
                    self.assertTrue(path.startswith(target+'?'))
                    inner.writes.append(copy.deepcopy(body))
                    if body['properties']['enabled']:
                        raise ValueError('Lifecycle Azure PUT rejected: HTTP 401, Unauthorized; no wider permission fallback')
                    inner.current=copy.deepcopy(body)|{'id':target,'etag':'"v1"'}
                    return copy.deepcopy(inner.current)
                inner.reads.append(path)
                if path.startswith(target+'?'): return copy.deepcopy(inner.current)
                if '/alertRules?' in path: return {'value':copy.deepcopy(baseline)}
                return {'properties':{'sku':{'name':'pergb2018'},'retentionInDays':30,'workspaceCapping':{'dailyQuotaGb':.1}}}
        client=Client()
        with patch.dict('os.environ',{'GITHUB_RUN_ATTEMPT':'1','GITHUB_RUN_ID':'1234567890'}),patch('builtins.print'):
            with self.assertRaisesRegex(ValueError,'HTTP 401, Unauthorized'):
                execute(client,workspace,'start')
        self.assertFalse(client.current['properties']['enabled'])
        self.assertEqual([b['properties']['enabled'] for b in client.writes],[False,True])
        self.assertGreaterEqual(sum(p.startswith(target+'?') for p in client.reads),4)
        self.assertTrue(all(r['properties']['enabled'] is False for r in baseline[:12]))
