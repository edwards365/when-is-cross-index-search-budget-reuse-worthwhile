"""Derive conditional lifecycle models from new, typed measurement receipts.

No measured numeric component can be supplied in the request. This is not the
saved-paper reconstruction and never launches a search, timer, or old analyzer.
"""
import argparse
import csv
import hashlib
import json
import math
import statistics
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROLES = ('source_design', 'target_selection', 'target_certification', 'target_evaluation')
ORIGINALS = {
    'analyze_tcp_fresh_lifecycle_v1.py': '703b2195d6a8eea58a2e7c247f6de653546958a07560aeb99c30216028f89010',
    'lifecycle_campaign_v1.py': 'c0d1dd46d99fea2a32e4ba47a01274dfa61b32fd2cec38ca71e8d1c528809ab8',
    'minimal_route_20261004_v1.py': '80754ec63f7a6073512227609c00a0657eb08cc32fe50410715cbf4487aa7be1',
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''): h.update(b)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
        raise ValueError('Nonnegative finite measured component required')
    return value


def threshold(B, D):
    """E3 threshold, refining its initial-region label to positive integer visits."""
    B, D = Decimal(str(B)), Decimal(str(D))
    if D > 0: return max(1, int((B / D).to_integral_value(rounding=ROUND_FLOOR)) + 1)
    if B < 0 and D == 0: return 1
    if B < 0 and D < 0 and B/D > 1: return 'finite_initial_region_only'
    return None


def last_initial_round(B, D):
    B, D = Decimal(str(B)), Decimal(str(D))
    if B < 0 and D < 0:
        last = int((B/D).to_integral_value(rounding=ROUND_CEILING))-1
        return last if last >= 1 else None
    return None


def contrast(B, D, requests=8000):
    return {'upfront_net_ns': B, 'saving_per_complete_round_ns': D,
            'first_round_net_ns': B-D, 'strict_complete_round': threshold(B, D),
            'last_strict_initial_round': last_initial_round(B, D),
            'nonpositive_saving': D <= 0,
            'per_request_net_overhead_erasing_saving_ns': D/requests if D > 0 else None,
            'fixed_extra_100_seconds_strict_round': threshold(B+100e9, D)}


class Reader:
    def __init__(self): self.provenance = {}

    def file(self, path, pin, label):
        path = Path(path).resolve(strict=True)
        if digest(path) != pin: raise ValueError('Payload SHA: '+label)
        self.provenance[label] = {'sha256': pin, 'bytes': path.stat().st_size}
        return path

    def receipt(self, ref, status, label):
        if set(ref) != {'directory', 'sha256'}: raise ValueError('Receipt reference must contain directory and SHA only')
        root = Path(ref['directory']).resolve(strict=True)
        if (root/'failure.json').exists(): raise ValueError('Failed parent: '+label)
        p = self.file(root/'completed.json', ref['sha256'], label+'/completed')
        r = load(p)
        if r['status'] != status: raise ValueError('New typed status: '+label)
        if (root/'start.json').exists(): self.file(root/'start.json', digest(root/'start.json'), label+'/start')
        return root, r

    def operational(self, ref, kind, label, cfg_sha):
        root, r = self.receipt(ref, 'NEW_OPERATIONAL_BOUNDARY_MEASUREMENT_COMPLETE', label)
        if r['kind'] != kind or load(root/'start.json')['config_sha256'] != cfg_sha:
            raise ValueError('Operational kind/config')
        rel = Path(r['measured']['measured_record'])
        p = (root/rel).resolve(strict=True)
        if not p.is_relative_to(root): raise ValueError('Operational path escape')
        self.file(p, r['measured']['record_sha256'], label+'/measured')
        return root, load(p)


def one(rows, **match):
    selected = [r for r in rows if all(r.get(k) == v for k, v in match.items())]
    if len(selected) != 1: raise ValueError('Unique row required: '+repr(match))
    return selected[0]


def action_metrics(hits, ndc, walls, decisions, baseline_rows, builds, grid, np):
    g, a, n = hits.shape
    if (g, a) != (len(builds), len(grid)) or ndc.shape != hits.shape: raise ValueError('Response axes')
    if np.any(hits < 0) or np.any(hits > 10) or np.any(ndc <= 0): raise ValueError('Metric range')
    stable = np.logical_and.accumulate((hits == 10)[:, ::-1, :], axis=1)[:, ::-1, :]
    labels = np.where(stable.any(axis=1), stable.argmax(axis=1), a)
    result = []
    for t, b in enumerate(builds):
        wall = walls[b]
        if wall.shape != (7, a, n) or not np.isfinite(wall).all() or np.any(wall <= 0): raise ValueError('Balanced positive timing cells')
        dec = one(decisions, target_build=b)['decision']
        if dec not in ('TCP', 'ENDPOINT'): raise ValueError('Undeployable target has no endpoint substitution')
        candidate = np.minimum(np.delete(labels, t, axis=0).max(axis=0), a-1)
        selected = candidate if dec == 'TCP' else np.full(n, a-1)
        q = np.arange(n)
        raw = hits[t, selected, q] < 10
        union = np.logical_or(hits[t, candidate, q] < 10, hits[t, -1] < 10)
        row = {'target_build': b, 'decision': dec,
               'candidate_service_ns': float(wall[:, candidate, q].mean()),
               'endpoint_service_ns': float(wall[:, -1, :].mean()),
               'TCP_service_ns': float(wall[:, selected, q].mean()),
               'raw_selected_failures': int(raw.sum()),
               'declared_selected_failures': int((union if dec == 'TCP' else hits[t, -1] < 10).sum()),
               'selected_mean_ndc': float(ndc[t, selected, q].mean()), 'baseline_services': {}}
        for m in ('endpoint2400', 'fixed1600', 'TG500', 'TG1000'):
            br = one(baseline_rows, target=b, method=m)
            if br['coverage'] not in (0, 1): raise ValueError('Baseline coverage')
            if not br['coverage']: continue
            ix = br['deployed_index']
            if not isinstance(ix, int) or not 0 <= ix < a: raise ValueError('Baseline action')
            row['baseline_services'][m] = {'mean_ns': float(wall[:, ix, :].mean()),
                'raw_failures': int((hits[t, ix] < 10).sum()), 'mean_ndc': float(ndc[t, ix].mean())}
        result.append(row)
    return result


def model_dataset(name, metrics, truth, profiles, graph, reloads, role_ns, decision_ns, cache_ns, q=1000):
    """Original component equations; inputs are internal validated receipt values."""
    builds = [r['target_build'] for r in metrics]
    truth_role = {r: finite(truth['roles'][r]['query_read_ns'])+finite(truth['roles'][r]['exact_search_ns']) for r in ROLES}
    components = {'exact_base_acquisition_ns': finite(truth['exact_base_acquisition_ns']),
        'design_selection_cert_truth_ns': sum(truth_role[r] for r in ROLES[:-1]),
        'design_selection_cert_profile_ns': sum(finite(profiles[r]['whole_unit_ns']) for r in ROLES[:-1]),
        'role_firewall_ns_allocated_half': finite(role_ns)/2,
        'decision_compute_ns_allocated_half': finite(decision_ns)/2}
    F = sum(components.values())
    units = {u['build']: u for u in profiles['target_evaluation']['profiles']}
    source = {b: max(0., finite(units[b]['elapsed_ns_operational_including_native_reload'])-finite(reloads[b]))/q for b in builds}
    truth_per = truth_role['target_evaluation']/q
    export_per = (finite(profiles['target_evaluation']['query_read_ns'])+finite(profiles['target_evaluation']['query_export_fsync_ns']))/q
    tcp = [r for r in metrics if r['decision'] == 'TCP']
    union = {b for r in tcp for b in builds if b != r['target_build']}
    acquisition = {b: truth_per+export_per+sum(source[s] for s in builds if s != b) for b in builds}
    endpoint = sum(r['endpoint_service_ns'] for r in metrics)
    service = {'TCP': sum(r['TCP_service_ns'] for r in metrics), 'cache_exact': len(builds)*cache_ns}
    service['TCP_deduplicated'] = service['TCP']
    for m in ('endpoint2400', 'fixed1600', 'TG500', 'TG1000'):
        if all(m in r['baseline_services'] for r in metrics): service[m] = sum(r['baseline_services'][m]['mean_ns'] for r in metrics)
    setup = {'TCP': (F, sum(acquisition[r['target_build']] for r in tcp)),
        'TCP_deduplicated': (F, truth_per+export_per+sum(source[b] for b in union) if tcp else 0),
        'endpoint2400': (0, 0), 'cache_exact': (components['exact_base_acquisition_ns'], truth_per)}
    for m in ('fixed1600', 'TG500', 'TG1000'):
        roles = ['target_certification'] if m == 'fixed1600' else ['target_selection', 'target_certification']
        factor = .5 if m == 'TG500' else 1.
        proxy = factor*sum(truth_role[r]+finite(profiles[r]['whole_unit_ns']) for r in roles)
        setup[m] = (components['exact_base_acquisition_ns']+proxy, 0)
    graph_complete = all('whole_unit_ns' in graph[b] and graph[b].get('operational_unit_measured') is True for b in builds)
    graph_total = sum(finite(graph[b]['whole_unit_ns']) for b in builds) if graph_complete else None
    targets = []
    for r in metrics:
        b = r['target_build']; saving = r['endpoint_service_ns']-r['TCP_service_ns']
        row = dict(r, dataset=name, acquisition_ns_per_distinct_query=acquisition[b],
                   source_profile_ns_per_distinct_query=source[b], median_reload_ns=reloads[b])
        if graph_complete:
            common = graph_total+sum(reloads.values()); endpoint_upfront = graph[b]['whole_unit_ns']+reloads[b]
            for key, upfront in (('allocated_one_eighth', (F+common)/len(builds)), ('standalone_pays_all_graphs', F+common)):
                row[key] = contrast(upfront-endpoint_upfront+q*acquisition[b], q*saving, q)
                if r['decision'] != 'TCP': row[key]['strict_complete_round'] = None
        else: row['standalone_status'] = 'NOT_ESTIMABLE_WHOLE_GRAPH_UNIT_TIME_ABSENT'
        targets.append(row)
    D = q*(endpoint-service['TCP'])
    campaigns = {key: contrast(F+q*acq, D, len(builds)*q) for key, acq in (
        ('per_target_TCP_only', setup['TCP'][1]), ('per_target_all_targets', sum(acquisition.values())),
        ('cross_target_deduplicated', setup['TCP_deduplicated'][1]))}
    ledgers = []
    for m in service:
        f, a = setup[m]
        ledgers.append(dict(dataset=name, method=m, fixed_ns=f, acquisition_per_distinct_ns=a,
            eight_target_service_ns_per_query=service[m], **contrast(f+q*a, q*(endpoint-service[m]), len(builds)*q)))
    paired = []
    for comparator in ('endpoint2400', 'fixed1600', 'TG500', 'TG1000', 'cache_exact'):
        if comparator not in service: continue
        for method in ('TCP', 'TCP_deduplicated'):
            for Q in (100, 1000, 10000):
                B = setup[method][0]-setup[comparator][0]+Q*(setup[method][1]-setup[comparator][1])
                D = Q*(service[comparator]-service[method])
                for extra in (0, 1e9, 10e9, 100e9):
                    for V in (1, 2, 10, 50, 100):
                        paired.append({'dataset': name, 'method': method, 'comparator': comparator, 'Q': Q, 'V': V,
                            'fixed_extra_net_ns': extra, 'net_cost_ns': B+extra-V*D,
                            'strict_complete_round': threshold(B+extra, D), 'modeled_extrapolation': Q != q})
        paired.append({'dataset': name, 'method': 'existing_all_required_assets', 'comparator': comparator, 'Q': q, 'V': 1,
            'fixed_extra_net_ns': 0, 'net_cost_ns': q*(service['TCP']-service[comparator]),
            'strict_complete_round': threshold(0, q*(service[comparator]-service['TCP'])), 'modeled_extrapolation': False})
    return {'dataset': name, 'fixed_components': components, 'targets': targets, 'campaigns': campaigns,
        'component_ledger': ledgers, 'paired_scenarios': paired, 'source_union_graphs': len(union),
        'excluded_incomplete_coverage_methods': [m for m in ('endpoint2400', 'fixed1600', 'TG500', 'TG1000') if m not in service],
        'common_graphs_cancelled_by_identity': builds, 'standalone_graph_timing_available': graph_complete,
        'graph_component_subtotals_ns': {b: sum(finite(graph[b][k]) for k in ('train_read_ns', 'membership_and_order_ns', 'graph_init_ns', 'graph_insert_ns', 'serialize_fsync_ns')) for b in builds},
        'fixed_setup_interpretation': 'original operational allocation, not minimum unavoidable deployment expenditure',
        'alternative_proxy': 'TG/fixed use measured full-grid role allocation, not exact chosen-action acquisition',
        'unknown_net_costs': ['control', 'TG decision time', 'cache insertion/transport', 'network/maintenance'],
        'unknown_net_costs_assumed_zero': False,
        'model_boundary': 'Identified component contrast; add unknown signed U. No empirical finite bound on U.'}


def derive(request, cfg, reader, np):
    required = {'roles', 'decision_measurement', 'policy_lock', 'policy_evaluation', 'baseline_lock', 'baseline_evaluation', 'cache', 'datasets'}
    if set(request) != required or set(request['datasets']) != {'sift', 'arxiv'}: raise ValueError('Receipt-only two-dataset request')
    cfg_sha = digest(HERE/'operational_config.json')
    _, roles = reader.operational(request['roles'], 'roles', 'roles', cfg_sha)
    _, decision = reader.operational(request['decision_measurement'], 'decision', 'decision', cfg_sha)
    _, lock = reader.receipt(request['policy_lock'], 'NEW_QUALIFICATION_LOCKED_BEFORE_EVALUATION_READ', 'policy-lock')
    _, evaluated = reader.receipt(request['policy_evaluation'], 'NEW_LOCKED_POLICY_EVALUATION_COMPLETE', 'policy-evaluation')
    _, bl = reader.receipt(request['baseline_lock'], 'NEW_BASELINES_LOCKED_BEFORE_EVALUATION_READ', 'baseline-lock')
    _, be = reader.receipt(request['baseline_evaluation'], 'NEW_LOCKED_BASELINES_EVALUATION_COMPLETE', 'baseline-evaluation')
    for package, records in (('portable_policy', (lock, evaluated)), ('portable_baselines', (bl, be))):
        pin = digest(HERE.parent/package/'config.json')
        if any(r['config_sha256'] != pin for r in records): raise ValueError('Policy/baseline package configuration')
    if roles['status'] != 'PASS_NEW_ROLE_AND_CONTENT_FIREWALL_BEFORE_OUTCOME' or decision['status'] != 'DECISIONS_LOCKED_BEFORE_EVALUATION_ARRAY_READ':
        raise ValueError('Original measured block completion')
    if len(lock['rows']) != 16 or len(evaluated['rows']) != 16 or len(bl['rows']) != 64 or len(be['rows']) != 64:
        raise ValueError('Complete policy/baseline coverage')
    if lock['rows'] != decision['rows'] or evaluated['prior_lock_sha256'] != request['policy_lock']['sha256'] or be['prior_lock_sha256'] != request['baseline_lock']['sha256']:
        raise ValueError('Locked decisions/evaluation linkage')
    cr, cache = reader.receipt(request['cache'], 'NEW_CACHE_STAGE_COMPLETED', 'cache')
    for rel, pin in cache['files'].items():
        p = (cr/'records'/rel).resolve(strict=True)
        if not p.is_relative_to(cr/'records'): raise ValueError('Cache path escape')
        reader.file(p, pin['sha256'], 'cache/'+rel)
        if p.stat().st_size != pin['bytes']: raise ValueError('Cache size')
    with (cr/'records/cache_lookup_summary.csv').open(encoding='utf-8', newline='') as f: cache_rows = list(csv.DictReader(f))
    results = []
    for prefix, spec in request['datasets'].items():
        if set(spec) != {'prepared', 'truth', 'graphs', 'reloads', 'profiles', 'arrays', 'timings'}: raise ValueError('Dataset receipt fields')
        ds = cfg['profile_datasets'][prefix]; name = ds['name']; builds = cfg['build_ids']; grid = cfg['action_grid']
        _, prepared = reader.receipt(spec['prepared'], 'NEW_ROLE_BASE_QUERY_PREPARATION_COMPLETED', prefix+'/prepared')
        if prepared['membership_sha256'] != roles['membership_sha256']: raise ValueError('Role-firewall/prepared membership identity')
        tr, truth = reader.receipt(spec['truth'], 'NEW_EXACT_TRUTH_MATCHES_FROZEN_BYTES', prefix+'/truth')
        if truth['dataset'] != prefix or load(tr/'start.json')['preparation_receipt_sha256'] != spec['prepared']['sha256']: raise ValueError('Truth/preparation pairing')
        if set(spec['graphs']) != set(builds) or set(spec['reloads']) != set(builds) or set(spec['timings']) != set(builds): raise ValueError('Eight graph coverage')
        if set(spec['profiles']) != set(ROLES) or set(spec['arrays']) != set(ROLES): raise ValueError('Four role coverage')
        profiles = {}; arrays = {}; role_ids = set()
        for role in ROLES:
            profdir, prof = reader.operational(spec['profiles'][role], 'profiles', prefix+'/'+role, cfg_sha)
            if prof['status'] != 'NATIVE_PROFILES_COMPLETE_AUDIT_PENDING' or (prof['dataset'], prof['role']) != (name, role) or prof['role_receipt_sha256'] != spec['prepared']['sha256']: raise ValueError('Profile role/preparation')
            if [u['build'] for u in prof['profiles']] != builds or any(u['actual_exit_code'] != 0 for u in prof['profiles']): raise ValueError('Profile native coverage/exit')
            for b in builds:
                p = ds['roles'][role]['profiles'][b]
                reader.file(profdir/'data'/(b+'.csv'), p['sha256'], prefix+'/'+role+'/'+b)
            reader.file(profdir/'data/queries.qbin', ds['roles'][role]['qbin_sha256'], prefix+'/'+role+'/qbin')
            truth_pin = ds['roles'][role]['truth_sha256']
            if prof['truth_sha256'] != truth_pin or truth['roles'][role]['output_sha256'] != truth_pin: raise ValueError('Truth/profile frozen identity')
            reader.file(tr/(prefix+'_'+role+'.npz'), truth_pin, prefix+'/'+role+'/truth')
            ar, rec = reader.receipt(spec['arrays'][role], 'NEW_ARRAY_MATCHES_FROZEN_BYTES', prefix+'/'+role+'/array')
            if rec.get('profile_receipt_sha256') != spec['profiles'][role]['sha256'] or rec.get('profile_origin') != 'new_original_operational_boundary' or (rec['dataset'], rec['role']) != (prefix, role): raise ValueError('Array/measured-profile linkage')
            pin = cfg['expected_arrays'][prefix+'_'+role]
            file = reader.file(ar/(prefix+'_'+role+'.npz'), pin['sha256'], prefix+'/'+role+'/array-payload')
            if rec['sha256'] != pin['sha256'] or rec['bytes'] != pin['bytes'] or file.stat().st_size != pin['bytes']: raise ValueError('Array metadata identity')
            with np.load(file, allow_pickle=False) as z: data = {k: z[k] for k in z.files}
            ids = set(map(int, data['query_ids']))
            if len(ids) != (1000 if role == 'target_evaluation' else 500) or role_ids & ids: raise ValueError('Disjoint role counts')
            role_ids |= ids
            if data['action_grid'].tolist() != grid or data['build_ids'].tolist() != builds: raise ValueError('Frozen axes')
            profiles[role] = prof; arrays[role] = data
            if role == 'target_certification':
                if lock['new_input_receipts'][prefix]['receipt_sha256'] != spec['arrays'][role]['sha256']: raise ValueError('Policy qualification origin')
            if role == 'target_evaluation':
                if evaluated['new_input_receipts'][prefix]['receipt_sha256'] != spec['arrays'][role]['sha256'] or be['new_input_receipts'][role][prefix]['receipt_sha256'] != spec['arrays'][role]['sha256']: raise ValueError('Evaluation origin')
            if role in ('target_selection', 'target_certification') and bl['new_input_receipts'][role][prefix]['receipt_sha256'] != spec['arrays'][role]['sha256']: raise ValueError('Baseline role origin')
        graph = {}; reloads = {}; walls = {}
        for b in builds:
            gr, graph[b] = reader.receipt(spec['graphs'][b], 'NEW_GRAPH_MATCHES_FROZEN_BYTES', prefix+'/'+b+'/graph')
            if graph[b]['index_sha256'] != ds['graphs'][b]['sha256'] or load(gr/'start.json')['prepared_receipt_sha256'] != spec['prepared']['sha256']: raise ValueError('Graph identity/preparation')
            reps = []
            for i, ref in enumerate(spec['reloads'][b]):
                rr, r = reader.receipt(ref, 'NEW_FRESH_PROCESS_RELOAD_COMPLETE', prefix+'/'+b+'/reload'+str(i))
                if (r['dataset'], r['build'], r['index_sha256']) != (prefix, b, graph[b]['index_sha256']) or load(rr/'start.json')['graph_receipt_sha256'] != spec['graphs'][b]['sha256']: raise ValueError('Reload graph binding')
                reps.append(r)
            if sorted(r['rep'] for r in reps) != [0, 1, 2]: raise ValueError('Three independent reloads')
            reloads[b] = statistics.median(finite(r['load_index_ns']) for r in reps)
            ti, timed = reader.receipt(spec['timings'][b], 'NEW_TIMING_ROWS_VALIDATED', prefix+'/'+b+'/timing')
            start = load(ti/'start.json')
            if start['config_sha256'] != digest(HERE.parent/'portable_timing/config.json'): raise ValueError('Timing package configuration')
            if (timed['dataset'], timed['build'], timed['actual_exit_code']) != (prefix, b, 0): raise ValueError('Timing identity/exit')
            if start['prior_lock_sha256'] not in (request['policy_lock']['sha256'], request['decision_measurement']['sha256']) or start['profile_receipt_sha256'] != spec['profiles']['target_evaluation']['sha256']: raise ValueError('Timing policy/profile pairing')
            if start['graph_sha256'] != graph[b]['index_sha256'] or start['qbin_sha256'] != ds['roles']['target_evaluation']['qbin_sha256']: raise ValueError('Timing graph/query pairing')
            reader.file(ti/'timed.csv', timed['raw_csv_sha256'], prefix+'/'+b+'/raw-timing')
            file = reader.file(ti/(prefix+'_'+b+'.npz'), timed['array_sha256'], prefix+'/'+b+'/timing-array')
            with np.load(file, allow_pickle=False) as z:
                if not np.array_equal(z['query_ids'], arrays['target_evaluation']['query_ids']) or z['action_grid'].tolist() != grid: raise ValueError('Timing query/grid alignment')
                walls[b] = z['wall_ns'].copy()
        decisions = [r for r in lock['rows'] if r['dataset'] == name]
        baselines = [r for r in bl['rows'] if r['dataset'] == name]
        a = arrays['target_evaluation']; metrics = action_metrics(a['hits'], a['ndc'], walls, decisions, baselines, builds, grid, np)
        for r in metrics:
            obs = one(evaluated['rows'], dataset=name, target_build=r['target_build'])
            if obs['decision'] != r['decision'] or obs['eval_selected_failures_descriptive'] != r['declared_selected_failures'] or not math.isclose(obs['eval_mean_selected_ndc'], r['selected_mean_ndc'], abs_tol=1e-8): raise ValueError('Policy evaluation recomputation')
            for m, v in r['baseline_services'].items():
                obs = one(be['rows'], dataset=name, target=r['target_build'], method=m)
                if obs['raw_failures'] != v['raw_failures'] or not math.isclose(obs['mean_ndc'], v['mean_ndc'], abs_tol=1e-8): raise ValueError('Baseline evaluation recomputation')
        cachecell = one(cache_rows, dataset=name, capacity_queries='1000', visits='100', order='cyclic')
        if float(cachecell['hit_rate']) != 1 or int(cachecell['repetitions']) != 7: raise ValueError('Full-capacity cache condition')
        results.append(model_dataset(name, metrics, truth, profiles, graph, reloads,
            finite(roles['wall_seconds'])*1e9, finite(decision['decision_compute_ns_including_audited_array_read']), finite(float(cachecell['mean_batch_lookup_ns']))))
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--authorize-new-derived-ledger', action='store_true'); a = p.parse_args()
    if not a.authorize_new_derived_ledger: p.error('Explicit derived-output opt-in required')
    out = a.output.resolve()
    if out.exists() or not out.parent.is_dir(): raise ValueError('Exclusive output path required')
    request = load(a.request)
    # Do not place outputs inside a supplied immutable measurement tree.
    def refs(obj):
        if isinstance(obj, dict):
            if set(obj) == {'directory', 'sha256'}: yield Path(obj['directory']).resolve()
            else:
                for v in obj.values(): yield from refs(v)
        elif isinstance(obj, list):
            for v in obj: yield from refs(v)
    if any(out.is_relative_to(r) or r.is_relative_to(out) for r in refs(request)): raise ValueError('Output overlaps input evidence')
    import numpy as np
    if np.__version__ != '1.26.4': raise ValueError('Pinned NumPy1.26.4 required')
    cfg = load(HERE/'operational_config.json'); reader = Reader(); out.mkdir(mode=0o700)
    try:
        result = derive(request, cfg, reader, np)
        report = {'status': 'NEW_MEASUREMENT_DERIVED_CONDITIONAL_LIFECYCLE_COMPLETE', 'schema': 'new-lifecycle-ledger-1',
            'request_sha256': digest(a.request), 'entry_sha256': digest(Path(__file__)),
            'operational_config_sha256': digest(HERE/'operational_config.json'), 'formula_source_pins': ORIGINALS,
            'datasets': result, 'input_provenance': reader.provenance, 'ANN_runs': 0, 'timing_runs': 0,
            'historical_measurements_replaced': False, 'original_e8': 'NOT_ESTIMABLE_UNCHANGED',
            'build_interference': 'NEW_MEASUREMENT_CONDITIONS_NOT_INFERRED_FROM_HISTORICAL_INTERFERENCE',
            'reload_boundary': 'fresh process, OS page cache unknown',
            'cross_component_hardware_equivalence': 'Not inferred from receipt hashes; inspect original new-run environment records',
            'confidence_intervals_computed': False, 'formal_end_to_end_timing': False}
        with (out/'lifecycle.json').open('x', encoding='utf-8') as f: json.dump(report, f, indent=2, allow_nan=False)
        with (out/'completed.json').open('x', encoding='utf-8') as f: json.dump({'status': report['status'], 'report_sha256': digest(out/'lifecycle.json')}, f)
        print(report['status'])
    except BaseException as e:
        with (out/'failure.json').open('x', encoding='utf-8') as f: json.dump({'status': 'FAILED_STOP_NO_OVERWRITE', 'error': repr(e)}, f)
        raise


if __name__ == '__main__': main()
