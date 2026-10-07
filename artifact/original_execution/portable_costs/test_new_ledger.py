"""Synthetic algebra and typed-receipt tests; no paper measurements executed."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import new_ledger as L


def typed_chain(root):
    """All producer receipt schemas, synthetic payloads, original role dimensions."""
    builds = ['b'+str(i) for i in range(8)]; grid = list(range(11)); cfg = {'build_ids': builds, 'action_grid': grid, 'profile_datasets': {}, 'expected_arrays': {}}
    request = {'datasets': {}}; decisions = []; evaluations = []; baselines = []; baseline_eval = []
    op_sha = L.digest(L.HERE/'operational_config.json')
    def write(p, obj):
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(obj), encoding='utf-8')
    def seal(name, obj, start=None):
        d = root/name; write(d/'completed.json', obj)
        if start is not None: write(d/'start.json', start)
        return {'directory': str(d), 'sha256': L.digest(d/'completed.json')}
    def measured(name, kind, record):
        d = root/name; p = d/'ops/final.json'; write(p, record)
        return seal(name, {'status': 'NEW_OPERATIONAL_BOUNDARY_MEASUREMENT_COMPLETE', 'kind': kind,
            'measured': {'measured_record': 'ops/final.json', 'record_sha256': L.digest(p)}}, {'config_sha256': op_sha})
    request['roles'] = measured('roles', 'roles', {'status': 'PASS_NEW_ROLE_AND_CONTENT_FIREWALL_BEFORE_OUTCOME', 'membership_sha256': 'membership', 'wall_seconds': 1})
    for prefix in ('sift', 'arxiv'):
        name = prefix+'-synthetic'; spec = {'graphs': {}, 'reloads': {}, 'profiles': {}, 'arrays': {}, 'timings': {}}
        request['datasets'][prefix] = spec
        cfg['profile_datasets'][prefix] = {'name': name, 'roles': {}, 'graphs': {b: {'sha256': b} for b in builds}}
        spec['prepared'] = seal(prefix+'/prepared', {'status': 'NEW_ROLE_BASE_QUERY_PREPARATION_COMPLETED', 'membership_sha256': 'membership'})
        tr = root/prefix/'truth'; tr.mkdir(parents=True)
        truth = {'status': 'NEW_EXACT_TRUTH_MATCHES_FROZEN_BYTES', 'dataset': prefix, 'exact_base_acquisition_ns': 1000, 'roles': {}}
        for ri, role in enumerate(L.ROLES):
            n = 1000 if ri == 3 else 500; ids = np.arange(n)+ri*1000
            truthpath = tr/(prefix+'_'+role+'.npz'); truthpath.write_bytes(('synthetic truth '+role).encode())
            truthpin = L.digest(truthpath); truth['roles'][role] = {'query_read_ns': 100, 'exact_search_ns': 900, 'output_sha256': truthpin}
            prof = root/prefix/role/'profiles'; (prof/'data').mkdir(parents=True)
            qbin = prof/'data/queries.qbin'; qbin.write_bytes(('synthetic queries '+role).encode())
            rolecfg = {'truth_sha256': truthpin, 'qbin_sha256': L.digest(qbin), 'profiles': {}}
            for b in builds:
                csv = prof/'data'/(b+'.csv'); csv.write_text('synthetic native payload '+b)
                rolecfg['profiles'][b] = {'sha256': L.digest(csv)}
            cfg['profile_datasets'][prefix]['roles'][role] = rolecfg
            record = {'status': 'NATIVE_PROFILES_COMPLETE_AUDIT_PENDING', 'dataset': name, 'role': role,
                'role_receipt_sha256': spec['prepared']['sha256'], 'truth_sha256': truthpin, 'whole_unit_ns': 2000,
                'query_read_ns': 100, 'query_export_fsync_ns': 100,
                'profiles': [{'build': b, 'actual_exit_code': 0, 'elapsed_ns_operational_including_native_reload': 200} for b in builds]}
            spec['profiles'][role] = measured(prefix+'/'+role+'/profiles', 'profiles', record)
            ar = root/prefix/role/'arrays'; ar.mkdir()
            array = ar/(prefix+'_'+role+'.npz')
            np.savez_compressed(array, query_ids=ids, build_ids=np.asarray(builds), action_grid=np.asarray(grid),
                hits=np.full((8, 11, n), 10, dtype=np.int16), ndc=np.full((8, 11, n), 3, dtype=np.uint64))
            pin = {'sha256': L.digest(array), 'bytes': array.stat().st_size}; cfg['expected_arrays'][prefix+'_'+role] = pin
            spec['arrays'][role] = seal(prefix+'/'+role+'/arrays', dict(status='NEW_ARRAY_MATCHES_FROZEN_BYTES', dataset=prefix, role=role,
                profile_origin='new_original_operational_boundary', profile_receipt_sha256=spec['profiles'][role]['sha256'], **pin))
        spec['truth'] = seal(prefix+'/truth', truth, {'preparation_receipt_sha256': spec['prepared']['sha256']})
        for i, b in enumerate(builds):
            graph = {'status': 'NEW_GRAPH_MATCHES_FROZEN_BYTES', 'index_sha256': b, 'whole_unit_ns': 100,
                'operational_unit_measured': True, **{k: 10 for k in ('train_read_ns', 'membership_and_order_ns', 'graph_init_ns', 'graph_insert_ns', 'serialize_fsync_ns')}}
            spec['graphs'][b] = seal(prefix+'/'+b+'/graph', graph, {'prepared_receipt_sha256': spec['prepared']['sha256']})
            spec['reloads'][b] = [seal(prefix+'/'+b+'/reload'+str(rep), {'status': 'NEW_FRESH_PROCESS_RELOAD_COMPLETE', 'dataset': prefix, 'build': b,
                'index_sha256': b, 'rep': rep, 'load_index_ns': 100}, {'graph_receipt_sha256': spec['graphs'][b]['sha256']}) for rep in range(3)]
            dec = 'TCP' if i < 4 else 'ENDPOINT'
            decisions.append({'dataset': name, 'target_build': b, 'decision': dec})
            evaluations.append({'dataset': name, 'target_build': b, 'decision': dec, 'eval_selected_failures_descriptive': 0, 'eval_mean_selected_ndc': 3})
            for m in ('endpoint2400', 'fixed1600', 'TG500', 'TG1000'):
                baselines.append({'dataset': name, 'target': b, 'method': m, 'coverage': 1, 'deployed_index': 10})
                baseline_eval.append({'dataset': name, 'target': b, 'method': m, 'raw_failures': 0, 'mean_ndc': 3})
    rolelinks = lambda role: {p: {'receipt_sha256': s['arrays'][role]['sha256']} for p, s in request['datasets'].items()}
    pc = L.digest(L.HERE.parent/'portable_policy/config.json'); bc = L.digest(L.HERE.parent/'portable_baselines/config.json')
    request['decision_measurement'] = measured('decision', 'decision', {'status': 'DECISIONS_LOCKED_BEFORE_EVALUATION_ARRAY_READ', 'rows': decisions, 'decision_compute_ns_including_audited_array_read': 1000})
    request['policy_lock'] = seal('lock', {'status': 'NEW_QUALIFICATION_LOCKED_BEFORE_EVALUATION_READ', 'rows': decisions, 'config_sha256': pc, 'new_input_receipts': rolelinks('target_certification')})
    request['policy_evaluation'] = seal('evaluate', {'status': 'NEW_LOCKED_POLICY_EVALUATION_COMPLETE', 'rows': evaluations, 'config_sha256': pc,
        'new_input_receipts': rolelinks('target_evaluation'), 'prior_lock_sha256': request['policy_lock']['sha256']})
    request['baseline_lock'] = seal('baseline-lock', {'status': 'NEW_BASELINES_LOCKED_BEFORE_EVALUATION_READ', 'rows': baselines, 'config_sha256': bc,
        'new_input_receipts': {r: rolelinks(r) for r in ('target_selection', 'target_certification')}})
    request['baseline_evaluation'] = seal('baseline-evaluate', {'status': 'NEW_LOCKED_BASELINES_EVALUATION_COMPLETE', 'rows': baseline_eval,
        'config_sha256': bc, 'new_input_receipts': {'target_evaluation': rolelinks('target_evaluation')}, 'prior_lock_sha256': request['baseline_lock']['sha256']})
    for prefix, spec in request['datasets'].items():
        for b in builds:
            ti = root/prefix/b/'timing'; ti.mkdir()
            raw = ti/'timed.csv'; raw.write_text('synthetic timing')
            arr = ti/(prefix+'_'+b+'.npz'); np.savez_compressed(arr, query_ids=np.arange(1000)+3000, action_grid=np.asarray(grid), wall_ns=np.ones((7, 11, 1000))*5)
            spec['timings'][b] = seal(prefix+'/'+b+'/timing', {'status': 'NEW_TIMING_ROWS_VALIDATED', 'dataset': prefix, 'build': b, 'actual_exit_code': 0,
                'raw_csv_sha256': L.digest(raw), 'array_sha256': L.digest(arr)}, {'config_sha256': L.digest(L.HERE.parent/'portable_timing/config.json'),
                'prior_lock_sha256': request['policy_lock']['sha256'], 'profile_receipt_sha256': spec['profiles']['target_evaluation']['sha256'],
                'graph_sha256': b, 'qbin_sha256': cfg['profile_datasets'][prefix]['roles']['target_evaluation']['qbin_sha256']})
    cache = root/'cache/records'; cache.mkdir(parents=True); table = cache/'cache_lookup_summary.csv'
    table.write_text('dataset,capacity_queries,visits,order,hit_rate,repetitions,mean_batch_lookup_ns\n'
        'sift-synthetic,1000,100,cyclic,1,7,1\narxiv-synthetic,1000,100,cyclic,1,7,1\n')
    request['cache'] = seal('cache', {'status': 'NEW_CACHE_STAGE_COMPLETED', 'files': {table.name: {'sha256': L.digest(table), 'bytes': table.stat().st_size}}})
    return request, cfg


def inputs():
    builds = ['b'+str(i) for i in range(8)]
    metrics = []
    for i, b in enumerate(builds):
        metrics.append({'target_build': b, 'decision': 'TCP' if i < 4 else 'ENDPOINT',
            'endpoint_service_ns': 100, 'TCP_service_ns': 50 if i < 4 else 100,
            'baseline_services': {m: {'mean_ns': n} for m, n in [('endpoint2400', 100), ('fixed1600', 80), ('TG500', 70), ('TG1000', 60)]}})
    truth = {'exact_base_acquisition_ns': 1000, 'roles': {r: {'query_read_ns': 100, 'exact_search_ns': 900} for r in L.ROLES}}
    profiles = {r: {'whole_unit_ns': 2000, 'query_read_ns': 100, 'query_export_fsync_ns': 100,
        'profiles': [{'build': b, 'elapsed_ns_operational_including_native_reload': 200} for b in builds]} for r in L.ROLES}
    graph = {b: {'whole_unit_ns': 100, 'operational_unit_measured': True,
        **{k: 10 for k in ('train_read_ns', 'membership_and_order_ns', 'graph_init_ns', 'graph_insert_ns', 'serialize_fsync_ns')}} for b in builds}
    return ('synthetic', metrics, truth, profiles, graph, {b: 100 for b in builds}, 1000, 1000, 1)


class LedgerTests(unittest.TestCase):
    def test_strict_threshold_equality(self):
        self.assertEqual(L.threshold(200, 100), 3)
        self.assertEqual(L.threshold(0, 100), 1)
        self.assertEqual(L.threshold(-200, 100), 1)

    def test_nonpositive_saving(self):
        self.assertIsNone(L.threshold(100, 0)); self.assertIsNone(L.threshold(100, -1))
        self.assertEqual(L.threshold(-100, 0), 1)
        self.assertEqual(L.threshold(-100, -1), 'finite_initial_region_only')
        self.assertIsNone(L.threshold(-1, -2))
        self.assertEqual(L.threshold(-5, -2), 'finite_initial_region_only')
        self.assertEqual(L.last_initial_round(-5, -2), 2)
        self.assertEqual(L.last_initial_round(-4, -2), 1)

    def test_zero_tcp_no_query_acquisition(self):
        a = inputs()
        for r in a[1]: r['decision'] = 'ENDPOINT'; r['TCP_service_ns'] = 100
        report = L.model_dataset(*a)
        dedup = next(r for r in report['component_ledger'] if r['method'] == 'TCP_deduplicated')
        self.assertEqual(dedup['acquisition_per_distinct_ns'], 0)
        self.assertEqual(report['source_union_graphs'], 0)

    def test_components_and_paired_scenarios(self):
        r = L.model_dataset(*inputs())
        self.assertEqual(sum(r['fixed_components'].values()), 11000)
        self.assertEqual(r['source_union_graphs'], 8)
        self.assertEqual(len(r['component_ledger']), 7)
        self.assertEqual(len(r['paired_scenarios']), 605)
        self.assertEqual(r['campaigns']['per_target_TCP_only']['upfront_net_ns'], 18600)
        self.assertEqual(r['campaigns']['per_target_all_targets']['upfront_net_ns'], 26200)
        self.assertEqual(r['campaigns']['cross_target_deduplicated']['upfront_net_ns'], 13000)
        self.assertEqual(r['campaigns']['per_target_TCP_only']['saving_per_complete_round_ns'], 200000)

    def test_graphs_cancel_only_in_campaign(self):
        a = inputs(); r = L.model_dataset(*a); other = copy.deepcopy(a)
        for g in other[4].values(): g['whole_unit_ns'] *= 100
        changed = L.model_dataset(*other)
        self.assertEqual(r['campaigns'], changed['campaigns'])
        self.assertNotEqual(r['targets'][0]['standalone_pays_all_graphs'], changed['targets'][0]['standalone_pays_all_graphs'])

    def test_missing_whole_timer_not_summed(self):
        a = inputs(); del a[4]['b0']['whole_unit_ns']; r = L.model_dataset(*a)
        self.assertFalse(r['standalone_graph_timing_available'])
        self.assertEqual(r['targets'][0]['standalone_status'], 'NOT_ESTIMABLE_WHOLE_GRAPH_UNIT_TIME_ABSENT')
        self.assertEqual(r['graph_component_subtotals_ns']['b0'], 50)
        self.assertEqual(len(r['campaigns']), 3)

    def test_negative_reload_proxy_clipped_original_rule(self):
        a = inputs()
        for p in a[3]['target_evaluation']['profiles']: p['elapsed_ns_operational_including_native_reload'] = 10
        r = L.model_dataset(*a)
        self.assertEqual(r['targets'][0]['source_profile_ns_per_distinct_query'], 0)

    def test_no_campaign_benefit_retained(self):
        a = inputs()
        for r in a[1]: r['TCP_service_ns'] = 110
        r = L.model_dataset(*a)
        self.assertTrue(r['campaigns']['cross_target_deduplicated']['nonpositive_saving'])
        self.assertIsNone(r['campaigns']['cross_target_deduplicated']['strict_complete_round'])

    def test_incomplete_baseline_not_zero_filled(self):
        a = inputs(); del a[1][0]['baseline_services']['TG1000']
        r = L.model_dataset(*a)
        self.assertNotIn('TG1000', [x['method'] for x in r['component_ledger']])

    def test_action_metrics_union_and_raw_distinct(self):
        builds = ['b0', 'b1']; grid = [10, 20]; hits = np.full((2, 2, 3), 10)
        hits[0, 1, 0] = 9  # target endpoint failure despite its smaller action passing
        ndc = np.ones_like(hits)*3; walls = {b: np.ones((7, 2, 3))*5 for b in builds}
        decisions = [{'target_build': b, 'decision': 'TCP'} for b in builds]
        baselines = [{'target': b, 'method': m, 'coverage': 1, 'deployed_index': 1} for b in builds for m in ('endpoint2400', 'fixed1600', 'TG500', 'TG1000')]
        r = L.action_metrics(hits, ndc, walls, decisions, baselines, builds, grid, np)
        self.assertEqual(r[0]['raw_selected_failures'], 0)
        self.assertEqual(r[0]['declared_selected_failures'], 1)

    def test_invalid_measurements(self):
        for x in (-1, float('nan'), float('inf'), True, '12'):
            with self.assertRaises(ValueError): L.finite(x)

    def test_new_receipt_hash_failure_status(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); p = root/'completed.json'; p.write_text(json.dumps({'status': 'NEW_OK'}))
            ref = {'directory': d, 'sha256': L.digest(p)}; reader = L.Reader()
            self.assertEqual(reader.receipt(ref, 'NEW_OK', 'toy')[1]['status'], 'NEW_OK')
            with self.assertRaises(ValueError): reader.receipt(ref, 'OLD_OK', 'toy')
            p.write_text('{}')
            with self.assertRaises(ValueError): reader.receipt(ref, 'NEW_OK', 'toy')
            (root/'failure.json').write_text('{}')
            with self.assertRaises(ValueError): reader.receipt(ref, 'NEW_OK', 'toy')

    def test_request_rejects_arbitrary_numeric_inputs(self):
        with self.assertRaises(ValueError): L.derive({'fixed_cost': 10}, {}, L.Reader(), np)

    def test_full_typed_synthetic_receipt_chain(self):
        with tempfile.TemporaryDirectory() as d:
            request, cfg = typed_chain(Path(d)); reader = L.Reader()
            rows = L.derive(request, cfg, reader, np)
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(len(r['targets']) == 8 and len(r['paired_scenarios']) == 605 for r in rows))
            self.assertGreater(len(reader.provenance), 200)
            # Re-hashing a changed start record cannot repair a wrong locked origin.
            timing = Path(request['datasets']['sift']['timings']['b0']['directory'])/'start.json'
            record = json.loads(timing.read_text()); record['prior_lock_sha256'] = 'wrong'
            timing.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'Timing policy/profile pairing'): L.derive(request, cfg, L.Reader(), np)


if __name__ == '__main__': unittest.main()
