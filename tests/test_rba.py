"""Risk behavior, causal joins, saturation, decay, baseline boundaries and offline safety."""
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from ingestion.events import generate
from rba.adapters import authentication, azure_activity, make_signal
from rba.demo import AS_OF, admin, attack, auth, dataset, original, scenarios
from rba.engine import correlate, score_at
from rba.model import baseline_match, baselines, instant, load_policy
from rba.render import dashboard, write_report


class TestRiskCorrelation(unittest.TestCase):
    def test_default_scenario_combines_weak_signals_into_one_explainable_finding(self):
        value = correlate(dataset())
        self.assertEqual(value['counts'],dict(input=18,unique=16,duplicates=2,outside_lookback=0,entities=3,findings=1))
        finding = value['findings'][0]
        self.assertEqual(finding['entity_id'],'synthetic-user-00')
        self.assertEqual(finding['priority'],'High')
        self.assertGreater(finding['first_score'],60)
        self.assertEqual(len(finding['chain_event_ids']),7)
        self.assertEqual(set(finding['techniques']),{'T1110','T1098.003','T1685.002','T1059.001'})
        self.assertTrue(all(c['signal_confidence']<=.55 for c in value['entities'][0]['peak']['contributions']))
        self.assertFalse(finding['sentinel_incident_created'])

    def test_positive_benign_and_edge_scenarios_have_expected_findings(self):
        for case in scenarios():
            with self.subTest(case=case['scenario']):
                self.assertEqual(correlate(case['dataset'])['counts']['findings'],case['expected_findings'])

    def test_order_independence_and_replay_envelopes_preserve_score_id_and_digest(self):
        data=dataset();forward=correlate(data)
        data['events'].reverse();backward=correlate(data)
        self.assertEqual(forward,backward)
        no_duplicate=correlate(dataset(attack()))
        replay=correlate(dataset([dict(attack()[0],event_id=original('new-envelope'))]+attack()))
        self.assertEqual(no_duplicate['dataset_sha256'],replay['dataset_sha256'])
        self.assertEqual(no_duplicate['findings'],replay['findings'])

    def test_configuration_changes_are_fingerprinted_in_finding_identity(self):
        data=dataset(attack());before=correlate(data)
        policy=load_policy();policy['half_life_minutes']=60
        with patch('rba.engine.load_policy',return_value=policy):after=correlate(data)
        self.assertEqual(before['dataset_sha256'],after['dataset_sha256'])
        self.assertNotEqual(before['configuration_sha256'],after['configuration_sha256'])
        self.assertNotEqual(before['findings'][0]['finding_id'],after['findings'][0]['finding_id'])

    def test_conflicting_ids_are_rejected_instead_of_silently_selecting_a_payload(self):
        event=attack()[0]
        for conflict in (dict(event,actor='synthetic-user-03'),
                         dict(event,event_id=original('new-envelope'),host='lab-auth-09')):
            with self.assertRaises(ValueError):
                correlate(dataset([event,conflict]))

    def test_distinct_real_occurrences_at_same_time_are_not_heuristically_deduplicated(self):
        event=attack()[0]
        other=dict(event,event_id=original('another-envelope'),source_event_id=original('another-original'))
        self.assertEqual(correlate(dataset([event,other]))['counts']['unique'],2)

    def test_half_life_decay_is_exact_before_caps_and_old_risk_expires(self):
        policy=load_policy();event=attack()[4]
        first=score_at([event],instant(event['time']),policy,[])
        later=score_at([event],instant(event['time'])+timedelta(minutes=30),policy,[])
        self.assertAlmostEqual(first['score']/2,later['score'],places=4)
        expired=score_at([event],instant(event['time'])+timedelta(minutes=60,seconds=1),policy,[])
        self.assertEqual(expired['score'],0)

    def test_current_risk_can_expire_without_erasing_the_historical_finding(self):
        value=correlate(dataset(attack()),'2026-10-18T14:00:00Z')
        self.assertEqual(value['entities'][0]['current']['score'],0)
        self.assertEqual(value['counts']['findings'],1)
        self.assertGreater(value['entities'][0]['peak']['score'],60)

    def test_failure_flood_is_bounded_and_cannot_create_a_correlated_finding(self):
        start=instant('2026-10-18T12:00:00Z')
        events=[make_signal('synthetic-authentication',original('flood-'+str(i)),
                           (start+timedelta(seconds=i)).isoformat(),'authentication_failure',
                           'synthetic-user-00',host='lab-auth-00',source_ip='192.0.2.10') for i in range(500)]
        value=correlate(dataset(events))
        self.assertLessEqual(value['entities'][0]['peak']['score'],12)
        self.assertEqual(value['counts']['findings'],0)

    def test_contribution_ledger_reconciles_to_score_after_caps_and_bonus(self):
        for entity in correlate(dataset())['entities']:
            for snapshot in (entity['current'],entity['peak']):
                self.assertAlmostEqual(sum(c['points'] for c in snapshot['contributions'])+snapshot['sequence_bonus'],snapshot['score'],places=3)
                self.assertLessEqual(snapshot['score'],100)

    def test_global_saturation_allocates_points_without_exceeding_one_hundred(self):
        events=attack()
        for kind,rule in load_policy()['signals'].items():
            events.extend(make_signal(rule['source'],original(f'cap-{kind}-{i}'),'2026-10-18T12:12:00Z',kind,
                'synthetic-user-00',host='lab-auth-00',source_ip='192.0.2.10',
                resource='lab-resource-workspace-01' if rule['source']=='azure-activity' else None) for i in range(5))
        entity=correlate(dataset(events))['entities'][0]
        self.assertEqual(entity['peak']['score'],100)
        self.assertAlmostEqual(sum(c['points'] for c in entity['peak']['contributions'])+entity['peak']['sequence_bonus'],100,places=3)

    def test_wrong_order_scope_host_and_shared_ip_cannot_create_causal_join(self):
        for case in scenarios():
            if case['scenario'] in ('wrong-stage-order','unrelated-resource-scope','unrelated-endpoint-host','shared-ip-different-actors'):
                value=correlate(case['dataset'])
                self.assertTrue(all(not e['current']['eligible'] for e in value['entities']))

    def test_equal_stage_timestamps_and_long_sequences_do_not_prove_order(self):
        events=attack();events[5]['time']=events[4]['time']
        self.assertEqual(correlate(dataset(events))['counts']['findings'],0)
        events=attack();events[-1]['time']='2026-10-18T12:40:00Z'
        data=dataset(events);data['as_of']='2026-10-18T12:41:00Z'
        self.assertEqual(correlate(data)['counts']['findings'],0)

    def test_unknown_or_stale_health_limits_confidence_without_hiding_the_signal(self):
        data=dataset(attack());limited=correlate(data)
        self.assertEqual(limited['findings'][0]['confidence'],'Low')
        self.assertIn('synthetic-endpoint',limited['findings'][0]['health_limitations'])
        data['health']['states']={s:'Healthy' for s in data['health']['states']}
        known=correlate(data)
        self.assertEqual(known['findings'][0]['confidence'],'Medium')
        self.assertEqual(limited['findings'][0]['first_score'],known['findings'][0]['first_score'])
        data['health']['observed_at']='2026-10-18T11:00:00Z'
        self.assertEqual(correlate(data)['findings'][0]['confidence'],'Low')

    def test_actor_counts_and_input_sizes_are_bounded_and_future_events_rejected(self):
        for events in ([attack()[0]]*501,[dict(attack()[0],time='2026-10-18T12:21:00Z')],
                       [dict(attack()[0],actor=f'synthetic-user-{i:02}',event_id=original(f'a{i}'),source_event_id=original(f'o{i}')) for i in range(33)]):
            with self.assertRaises(ValueError):
                correlate(dataset(events))
        old=dict(attack()[0],time='2026-10-18T08:19:59Z')
        self.assertEqual(correlate(dataset([old]))['counts']['outside_lookback'],1)


class TestRiskContractsAndBaseline(unittest.TestCase):
    def test_baseline_requires_exact_actor_kind_source_resource_and_bounded_time(self):
        entries=baselines(load_policy());event=attack(1)[4]
        self.assertIsNotNone(baseline_match(event,entries))
        for key,val in (('actor','synthetic-user-00'),('kind','policy_change'),('resource','lab-resource-workspace-03'),
                        ('time','2026-10-18T12:20:01Z')):
            self.assertIsNone(baseline_match(dict(event,**{key:val}),entries))
        self.assertIsNotNone(baseline_match(dict(event,time='2026-10-18T12:20:00Z'),entries))

    def test_baselines_do_not_exclude_all_activity_of_a_maintenance_actor(self):
        events=attack(1)
        for event in events:
            if event['resource']:event['resource']='lab-resource-workspace-03'
        self.assertEqual(correlate(dataset(events))['counts']['findings'],1)

    def test_unsupported_real_or_freeform_telemetry_is_rejected(self):
        mutations=({'synthetic':False},{'synthetic':1},{'source_ip':'8.8.8.8'},{'actor':'real.user@example.test'},
                   {'kind':'run-command'},{'source':'arbitrary-connector'},{'command_line':'private content'},
                   {'time':'2026-10-18T12:00:00'},{'source_ip':'192.0.2.0/24'},{'approved_change':True})
        for change in mutations:
            with self.subTest(field=list(change)),self.assertRaises(ValueError):
                correlate(dataset([dict(attack()[0],**change)]))

    def test_existing_authentication_contract_and_explicit_azure_alias_mapping(self):
        normalized=authentication(generate(1,'2026-10-18T12:00:00Z','risk-test')[0])
        self.assertEqual(normalized['actor'],'synthetic-user-00')
        self.assertEqual(admin(6,'rbac_assignment')['actor'],normalized['actor'])
        raw={'Synthetic':True,'EventDataId':original('azure'),'TimeGenerated':'2026-10-18T12:00:00Z',
             'OperationNameValue':'Microsoft.Authorization/roleAssignments/write','ActivityStatusValue':'Start',
             'Caller':'synthetic-principal-00','CallerIpAddress':'192.0.2.10','ResourceId':'lab-resource-workspace-01'}
        self.assertIsNone(azure_activity(raw))
        raw['ActivityStatusValue']='FAILED'
        self.assertEqual(azure_activity(raw)['kind'],'administrative_failure')
        raw['Caller']='unknown-principal'
        with self.assertRaises(ValueError):azure_activity(raw)

    def test_equivalent_utc_offsets_and_documentation_ipv6_are_canonicalized(self):
        event=attack()[0]
        one=correlate(dataset([dict(event,source_ip='2001:db8::1')]))
        two=correlate(dataset([dict(event,time='2026-10-18T14:00:00+02:00',source_ip='2001:0db8:0:0:0:0:0:1')]))
        self.assertEqual(one,two)


class TestRiskReports(unittest.TestCase):
    def test_cli_is_offline_and_reproducible_with_safe_artifacts(self):
        from rba.__main__ import main
        with tempfile.TemporaryDirectory() as directory,patch('sys.argv',['rba','--output',directory]), \
                patch('socket.create_connection') as network,patch('subprocess.run') as shell,redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(),0)
            summary=json.loads(output.getvalue())
            self.assertEqual(summary['counts']['findings'],1)
            self.assertEqual(summary['scenario_checks'],9)
            network.assert_not_called();shell.assert_not_called()
            self.assertEqual({p.name for p in Path(directory).iterdir()},{'report.json','investigation.md','dashboard.html','dataset.synthetic.json'})

    def test_dashboard_escapes_script_termination_and_replays_only_precomputed_scores(self):
        value=correlate(dataset());value['customer']='</script><script>alert(1)</script>'
        text=dashboard(value)
        self.assertNotIn('</script><script>alert(1)',text)
        self.assertIn('\\u003c/script\\u003e',text)
        self.assertIn('type="range"',text)
        self.assertNotIn('src="https:',text)

    def test_finding_ids_are_deterministic_without_claiming_cross_run_case_storage(self):
        first=correlate(dataset());again=correlate(dataset())
        self.assertEqual(first['findings'],again['findings'])
        self.assertEqual(first['limits'],dict(network_calls=0,azure_changes=0,sentinel_incidents_created=0,live_telemetry_validated=False))
