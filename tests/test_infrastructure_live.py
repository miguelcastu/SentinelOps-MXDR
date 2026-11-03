"""No-network tests of exact GET-only infrastructure verification boundaries."""
import copy
import io
import json
import os
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from infrastructure.preview import LEGACY_RULE, model
from scripts.verify_infrastructure import (
    COMPILER_EVIDENCE, ReadOnlyClient, compiler_evidence, load_compiler_evidence,
    main, paths, verify,
)


class FakeClient:
    def __init__(self):
        resources = model()
        self.workspace = resources['workspace']['id']
        self.calls = []
        self.routes = paths(self.workspace)
        self.responses = {}
        for key in ('workspace', 'machine', 'dcr', 'extension', 'association'):
            entry = resources[key]
            self.responses[self.routes[key]] = dict(copy.deepcopy(entry['body']), id=entry['id'], type=entry['type'])
        self.responses[self.routes['workspace']]['properties']['customerId'] = '33333333-3333-4333-8333-333333333333'
        self.responses[self.routes['machine']].update(
            location='westeurope', identity={'type': 'SystemAssigned'},
            properties={'status': 'Disconnected', 'osType': 'linux'})
        self.responses[self.routes['dcr']]['properties']['destinations']['logAnalytics'][0]['workspaceId'] = '33333333-3333-4333-8333-333333333333'
        self.responses[self.routes['extension']]['properties']['typeHandlerVersion'] = '1.45.1'
        rules = []
        for key, entry in resources.items():
            if key.startswith('AZ-DET-'):
                rules.append(dict(copy.deepcopy(entry['body']), id=entry['id'],
                                  name=entry['id'].rsplit('/', 1)[1], type=entry['type']))
        rules.append({'id': self.workspace + '/providers/Microsoft.SecurityInsights/alertRules/existing-fusion',
                      'name': 'existing-fusion', 'kind': 'Fusion', 'properties': {'enabled': True}})
        self.responses[self.routes['rules']] = {'value': rules}

    def request(self, method, path):
        if method != 'GET' or path not in self.responses:
            raise AssertionError('Unexpected method/route')
        self.calls.append((method, path))
        return copy.deepcopy(self.responses[path])


class TestInfrastructureLiveBoundary(unittest.TestCase):
    def test_exact_six_gets_allow_stopped_arc_and_preserve_two_unknowns(self):
        client = FakeClient()
        result = verify(client, client.workspace, LEGACY_RULE, COMPILER_EVIDENCE)
        self.assertEqual(len(client.calls), 6)
        self.assertEqual({method for method, _ in client.calls}, {'GET'})
        self.assertEqual(result['counts'], {'Matching': 17, 'Drift': 0, 'Missing': 0, 'Unknown': 2})
        self.assertEqual(result['owned_machine_connectivity'], 'Disconnected')
        self.assertEqual(result['analytics_inventory_count'], 13)
        self.assertEqual(result['managed_rules_disabled'], 12)
        self.assertTrue(result['compiled_to_live_contracts_match'])
        self.assertFalse(result['deployment_executed'])
        self.assertFalse(result['telemetry_ingestion_verified'])
        for value in (client.workspace, LEGACY_RULE, '33333333-3333-4333-8333-333333333333'):
            self.assertNotIn(value, json.dumps(result))
        untouched = [r for r in result['resources'] if r['state'] == 'Unknown']
        self.assertEqual({r['target'] for r in untouched}, {'sentinel', 'diagnostic-export'})

    def test_drift_and_missing_target_fail_matching_without_exposing_values(self):
        client = FakeClient()
        client.responses[client.routes['workspace']]['properties']['workspaceCapping']['dailyQuotaGb'] = 999.123
        listing = client.responses[client.routes['rules']]['value']
        listing[:] = [r for r in listing if not r['properties'].get('displayName', '').startswith('AZ-DET-007')]
        listing[0]['properties']['enabled'] = True
        result = verify(client, client.workspace, LEGACY_RULE, COMPILER_EVIDENCE)
        self.assertEqual(result['counts'], {'Matching': 14, 'Drift': 2, 'Missing': 1, 'Unknown': 2})
        self.assertFalse(result['compiled_to_live_contracts_match'])
        self.assertNotIn('999.123', json.dumps(result))
        self.assertTrue(all(r['proposed_operation'] == 'none' for r in result['resources']))

    def test_wrong_destination_duplicate_rule_and_incomplete_inventory_stop(self):
        for variation in ('destination', 'duplicate', 'pagination', 'wrong-id'):
            with self.subTest(variation=variation):
                client = FakeClient()
                if variation == 'destination':
                    client.responses[client.routes['dcr']]['properties']['destinations']['logAnalytics'][0]['workspaceId'] = '44444444-4444-4444-8444-444444444444'
                    report = verify(client, client.workspace, LEGACY_RULE, COMPILER_EVIDENCE)
                    self.assertFalse(report['compiled_to_live_contracts_match'])
                    self.assertEqual(report['counts']['Drift'], 1)
                    continue
                if variation == 'duplicate':
                    listing = client.responses[client.routes['rules']]['value']
                    listing.append(copy.deepcopy(listing[0]))
                elif variation == 'pagination':
                    client.responses[client.routes['rules']]['nextLink'] = 'PRIVATE-UNFOLLOWED-URL'
                else:
                    client.responses[client.routes['association']]['id'] += '-another'
                with self.assertRaises(ValueError):
                    verify(client, client.workspace, LEGACY_RULE, COMPILER_EVIDENCE)

    def test_transport_refuses_writes_and_unapproved_routes_before_network(self):
        fake = FakeClient()
        with patch('scripts.verify_infrastructure.az_json', return_value={'accessToken': 'PRIVATE-NOT-A-REAL-TOKEN'}):
            client = ReadOnlyClient(fake.workspace)
        with patch('scripts.verify_infrastructure.urllib.request.build_opener') as network:
            for method in ('POST', 'PUT', 'PATCH', 'DELETE', 'HEAD'):
                with self.assertRaises(ValueError):
                    client.request(method, fake.routes['workspace'])
            with self.assertRaises(ValueError):
                client.request('GET', fake.routes['workspace'], body={})
            with self.assertRaises(ValueError):
                client.request('GET', fake.workspace + '/providers/Microsoft.SecurityInsights/incidents?api-version=2025-09-01')
            network.assert_not_called()

    def test_transport_errors_discard_private_azure_error_body(self):
        fake = FakeClient()
        secret = 'PRIVATE-TELEMETRY-AND-IDENTIFIERS'
        error = urllib.error.HTTPError('https://management.azure.com/private', 403, 'Forbidden', {},
                                       io.BytesIO(json.dumps({'error': {'code': 'AuthorizationFailed', 'message': secret}}).encode()))
        with patch('scripts.verify_infrastructure.az_json', return_value={'accessToken': secret}):
            client = ReadOnlyClient(fake.workspace)
        with patch('scripts.verify_infrastructure.urllib.request.build_opener') as network:
            network.return_value.open.side_effect = error
            with self.assertRaisesRegex(ValueError, 'HTTP 403, AuthorizationFailed') as caught:
                client.request('GET', fake.routes['workspace'])
        self.assertNotIn(secret, str(caught.exception))

    def test_failed_compiler_evidence_blocks_authentication(self):
        for change in ({'compiler_sha256_verified': False}, {'compiler_sha256_verified': 1}, {'foundation_writes': 1}):
            with self.assertRaises(ValueError):
                compiler_evidence(COMPILER_EVIDENCE | change)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'compiler.json'
            path.write_text('{}', encoding='utf-8')
            with patch.dict(os.environ, {'SENTINELOPS_COMPILE_REPORT': str(path)}), patch('scripts.verify_infrastructure.context') as login:
                with self.assertRaises(ValueError):
                    main()
                login.assert_not_called()

    def test_main_emits_only_sanitized_report_and_fails_on_observed_drift(self):
        client = FakeClient()
        with patch('scripts.verify_infrastructure.load_compiler_evidence', return_value=COMPILER_EVIDENCE), \
             patch('scripts.verify_infrastructure.context', return_value=client.workspace), \
             patch.dict(os.environ, {'SENTINEL_RULE_ID': LEGACY_RULE}), \
             patch('scripts.verify_infrastructure.ReadOnlyClient', return_value=client):
            output = io.StringIO()
            with redirect_stdout(output):
                main()
            text = output.getvalue()
            self.assertTrue(text.startswith('INFRASTRUCTURE_EVIDENCE='))
            self.assertNotIn(client.workspace, text)
            self.assertNotIn(LEGACY_RULE, text)
            client.responses[client.routes['workspace']]['properties']['retentionInDays'] = 365
            with redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                main()
