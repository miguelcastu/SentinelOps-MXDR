"""Fixed-scope drift, destructive-change refusal and real Bicep contract checks."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from infrastructure.preview import (
    LEGACY_RULE, SUBSCRIPTION, compare, compile_templates, guard_changes,
    model, snapshot, validate_compiled,
)


class TestInfrastructurePreview(unittest.TestCase):
    def test_absent_evidence_is_unknown_not_a_clean_deployment(self):
        result = compare()
        self.assertEqual(result['counts']['Unknown'], 19)
        self.assertFalse(result['safe_to_deploy'])
        self.assertFalse(result['arm_what_if_executed'])
        self.assertEqual(result['azure_requests'], 0)

    def test_matching_synthetic_snapshot_stays_explicitly_synthetic_and_private(self):
        report = compare(snapshot())
        self.assertEqual(report['counts']['Matching'], 19)
        self.assertEqual(report['input_evidence'], 'synthetic')
        self.assertFalse(report['input_provenance_verified'])
        for private in (SUBSCRIPTION, LEGACY_RULE, '/subscriptions/'):
            self.assertNotIn(private, json.dumps(report))

    def test_enabled_rule_and_workspace_cost_drift_are_reported_without_mutation(self):
        data = snapshot()
        by_name = {r['target']: r for r in data['resources']}
        by_name['AZ-DET-002']['body']['properties']['enabled'] = True
        by_name['workspace']['body']['properties']['workspaceCapping']['dailyQuotaGb'] = 20.0
        before = copy.deepcopy(data)
        report = compare(data)
        changed = {r['target']: r for r in report['resources'] if r['state'] == 'Drift'}
        self.assertEqual(set(changed), {'AZ-DET-002', 'workspace'})
        self.assertIn('properties.enabled', changed['AZ-DET-002']['changed_paths'])
        self.assertIn('properties.workspaceCapping.dailyQuotaGb', changed['workspace']['changed_paths'])
        self.assertEqual(data, before)
        self.assertTrue(all(r['proposed_operation'] == 'none' for r in report['resources']))

    def test_missing_resource_is_not_a_create_proposal(self):
        data = snapshot()
        data['resources'] = [r for r in data['resources'] if r['target'] != 'dcr']
        report = compare(data)
        row = next(r for r in report['resources'] if r['target'] == 'dcr')
        self.assertEqual(row['state'], 'Missing')
        self.assertEqual(row['proposed_operation'], 'none')
        self.assertFalse(report['safe_to_deploy'])

    def test_unknown_duplicate_wrong_scope_and_resource_type_stop(self):
        for alteration in ('duplicate', 'unknown', 'scope', 'type'):
            with self.subTest(alteration=alteration):
                data = snapshot()
                if alteration == 'duplicate':
                    data['resources'].append(copy.deepcopy(data['resources'][0]))
                elif alteration == 'unknown':
                    data['resources'][0]['target'] = 'another-workspace'
                elif alteration == 'scope':
                    data['resources'][0]['id'] = data['resources'][0]['id'].replace('rg-sentinelops-mxdr', 'other-group')
                else:
                    data['resources'][0]['type'] = 'Microsoft.Compute/virtualMachines'
                with self.assertRaises(ValueError):
                    compare(data)

    def test_ama_extra_destination_and_unreviewed_severity_are_drift(self):
        for alteration in ('destination', 'severity'):
            data = snapshot()
            body = next(r['body'] for r in data['resources'] if r['target'] == 'dcr')
            if alteration == 'destination':
                body['properties']['destinations']['logAnalytics'].append({'name': 'other', 'workspaceResourceId': '/other'})
            else:
                body['properties']['dataSources']['syslog'][0]['logLevels'].append('Info')
            result = compare(data)
            self.assertEqual(next(r['state'] for r in result['resources'] if r['target'] == 'dcr'), 'Drift')

    def test_readonly_workspace_id_requires_independent_matching_metadata(self):
        data = snapshot()
        workspace = next(r for r in data['resources'] if r['target'] == 'workspace')
        workspace['body']['properties']['customerId'] = '33333333-3333-4333-8333-333333333333'
        dcr = next(r for r in data['resources'] if r['target'] == 'dcr')
        destination = dcr['body']['properties']['destinations']['logAnalytics'][0]
        destination['workspaceId'] = workspace['body']['properties']['customerId']
        self.assertEqual(compare(data)['counts']['Matching'], 19)
        destination['workspaceId'] = '44444444-4444-4444-8444-444444444444'
        self.assertEqual(next(r['state'] for r in compare(data)['resources'] if r['target'] == 'dcr'), 'Drift')

    def test_change_review_rejects_deletion_creation_foundation_changes_and_activation(self):
        fixed = model()
        for operation in ('Create', 'Delete', 'Replace', 'Deploy', 'Unsupported'):
            with self.assertRaises(ValueError):
                guard_changes([{'target': 'dcr', 'change_type': operation, 'after': fixed['dcr']['body']}])
        for target in ('workspace', 'sentinel', 'diagnostic-export', 'machine'):
            with self.assertRaises(ValueError):
                guard_changes([{'target': target, 'change_type': 'Modify', 'after': fixed[target]['body']}])
        body = copy.deepcopy(fixed['AZ-DET-001']['body'])
        body['properties']['enabled'] = True
        with self.assertRaises(ValueError):
            guard_changes([{'target': 'AZ-DET-001', 'change_type': 'Modify', 'after': body}])

    def test_change_review_accepts_only_exact_fixed_body_and_is_never_deployment_approval(self):
        fixed = model()
        review = guard_changes([{'target': 'AZ-DET-002', 'change_type': 'Modify', 'after': fixed['AZ-DET-002']['body']}])
        self.assertEqual(review['reviewable_changes'], 1)
        self.assertFalse(review['safe_to_deploy'])
        body = copy.deepcopy(fixed['extension']['body'])
        body['properties']['settings'] = {'commandToExecute': 'unreviewed'}
        with self.assertRaises(ValueError):
            guard_changes([{'target': 'extension', 'change_type': 'Modify', 'after': body}])


class TestActualBicepCompilation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        candidates = [root / '.local/tools/bicep-v0.48.1.exe', root / '.local/tools/bicep-v0.48.1']
        executable = next((p for p in candidates if p.is_file()), None)
        if executable is None:
            raise unittest.SkipTest('Pinned compiler absent; run the explicit Bicep validation step')
        cls.directory = tempfile.TemporaryDirectory(prefix='sentinelops-bicep-')
        cls.report = compile_templates(executable, Path(cls.directory.name))
        cls.templates = {n: json.loads((Path(cls.directory.name) / (n + '.json')).read_text(encoding='utf-8'))
                         for n in ('main', 'ama', 'disabled-rules', 'diagnostic-export')}

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_real_compiler_matches_all_fixed_resources(self):
        self.assertEqual(self.report['template_count'], 4)
        self.assertEqual(self.report['disabled_rule_definitions'], 12)
        self.assertEqual(self.report['foundation_writes'], 0)
        self.assertTrue(self.report['compiler_sha256_verified'])

    def test_compiled_foundation_creation_unsupported_collection_or_enabled_rule_stop(self):
        for alteration in ('foundation', 'collection', 'enabled'):
            templates = copy.deepcopy(self.templates)
            if alteration == 'foundation':
                templates['main']['resources'].append({'type': 'Microsoft.Compute/virtualMachines'})
            elif alteration == 'collection':
                templates['ama']['resources'][0]['properties']['dataSources']['syslog'][0]['facilityNames'].append('*')
            else:
                templates['disabled-rules']['variables']['$fxv#0']['properties']['enabled'] = True
            with self.assertRaises(ValueError):
                validate_compiled(templates)
