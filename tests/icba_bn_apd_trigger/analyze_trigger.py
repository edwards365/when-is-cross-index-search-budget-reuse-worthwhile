from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
OUT = ROOT / 'results/icba_bn_apd_trigger'

traces = pd.concat([pd.read_csv(p) for p in sorted(OUT.glob('trace_*_*.csv'))], ignore_index=True)
assert len(traces) == 12000
assert traces.native_tracer_equal.eq(1).all()
assert not traces.duplicated(['query_id', 'build_id', 'raw_ef']).any()
traces['dataset'] = traces.build_id.str.split('_').str[0]
traces['build'] = traces.build_id
traces['split'] = np.where(traces.query_id < 250, 'proposal', 'validation')

d = pd.read_csv(ROOT / 'results/icba_cals_seal/subset_results.csv.gz')
acts = pd.read_csv(ROOT / 'results/icba_cals_seal/selection_actions.csv')
target = acts[acts.action_scope.eq('TARGET_SPECIFIC_SELECTED_FIXED_SET')]
base = d[d['mask'].eq(0)].copy()
base['recall'] = base.union_hits / 10
cont = []
for (ds, build, q), g in base.groupby(['dataset', 'build', 'query_id']):
    g = g.sort_values('raw_ef').drop_duplicates('raw_ef')
    for e0, e1 in [(8, 16), (16, 32), (32, 64)]:
        a, z = g[g.raw_ef.eq(e0)], g[g.raw_ef.eq(e1)]
        if a.empty or z.empty: continue
        a, z = a.iloc[0], z.iloc[0]
        dc = z.total_ndc - a.total_ndc
        cont.append(dict(dataset=ds, build=build, query_id=q, raw_ef=e0,
                         continue_value=((z.union_hits-a.union_hits)/10)/dc if dc > 0 else np.nan))
cont = pd.DataFrame(cont)

outcomes = []
for _, a in target[target.raw_ef.isin([8, 16, 32])].iterrows():
    p = d[(d.dataset.eq(a.dataset)) & (d.build.eq(a.build)) &
          (d.raw_ef.eq(a.raw_ef)) & (d['mask'].eq(a['mask']))].copy()
    p['portal_value'] = ((p.union_hits-p.base_hits)/10) / p.aux_ndc_sum.replace(0, np.nan)
    p = p.merge(cont[(cont.dataset.eq(a.dataset)) & (cont.build.eq(a.build)) &
                     (cont.raw_ef.eq(a.raw_ef))], on=['dataset','build','query_id','raw_ef'])
    p['advantage'] = p.portal_value - p.continue_value
    outcomes.append(p[['dataset','build','query_id','raw_ef','portal_value','continue_value','advantage']])
outcomes = pd.concat(outcomes, ignore_index=True)
joined = traces.merge(outcomes, left_on=['dataset','build_id','query_id','raw_ef'],
                      right_on=['dataset','build','query_id','raw_ef'], how='inner')
assert len(joined) == 9000

# Quantile thresholds are frozen from the proposal half only, then applied unchanged to validation.
thresholds = []
for (ds, build, ef), g in joined[joined.split.eq('proposal')].groupby(['dataset','build_id','raw_ef']):
    thresholds.append(dict(dataset=ds, build_id=build, raw_ef=ef,
                           duplicate_q50=g.duplicate_ratio.median(),
                           frontier_ratio_q50=g.frontier_kth_ratio.replace([np.inf,-np.inf],np.nan).median()))
thresholds = pd.DataFrame(thresholds)
joined = joined.merge(thresholds, on=['dataset','build_id','raw_ef'])

rules = {
    'STAGNATION_W4': joined.kth_improvement_w4 <= 0,
    'STAGNATION_W8': joined.kth_improvement_w8 <= 0,
    'STAGNATION_W16': joined.kth_improvement_w16 <= 0,
    'LOW_YIELD_010_W8': joined.candidate_yield_w8 <= .10,
    'LOW_YIELD_025_W8': joined.candidate_yield_w8 <= .25,
    'LOW_YIELD_050_W8': joined.candidate_yield_w8 <= .50,
    'HIGH_DUPLICATION_Q50': joined.duplicate_ratio >= joined.duplicate_q50,
    'HIGH_FRONTIER_RATIO_Q50': joined.frontier_kth_ratio >= joined.frontier_ratio_q50,
}
rows = []
for name, mask in rules.items():
    for (split, ds, build, ef), g in joined[mask].groupby(['split','dataset','build_id','raw_ef']):
        cutoff = g.advantage.quantile(.99) if len(g) else np.nan
        trimmed = g[g.advantage <= cutoff]
        rows.append(dict(rule=name, split=split, dataset=ds, build=build, raw_ef=ef,
                         n=len(g), coverage=len(g)/250, median_advantage=g.advantage.median(),
                         median_after_top1pct=trimmed.advantage.median(),
                         mean_advantage=g.advantage.mean()))
summary = pd.DataFrame(rows)
summary.to_csv(OUT/'trigger_rule_results.csv', index=False)
thresholds.to_csv(OUT/'proposal_thresholds.csv', index=False)
joined.to_csv(OUT/'trace_outcome_join.csv.gz', index=False, compression='gzip')

validation = summary[summary.split.eq('validation')]
gate_rows = []
for rule, g in validation.groupby('rule'):
    by_ds = {}
    for ds, x in g.groupby('dataset'):
        positive_builds = x.groupby('build').median_after_top1pct.max().gt(0).sum()
        by_ds[ds] = bool(positive_builds >= 2 and x.coverage.max() >= .10)
    gate_rows.append(dict(rule=rule, sift_pass=by_ds.get('sift',False),
                          arxiv_pass=by_ds.get('arxiv',False), both_pass=all(by_ds.get(x,False) for x in ['sift','arxiv'])))
gates = pd.DataFrame(gate_rows)
gates.to_csv(OUT/'trigger_gate.csv', index=False)
passed = gates.both_pass.any()
decision = ('OBSERVABLE_TRIGGER_SIGNAL_SUPPORTED_AUTHORIZE_SHARED_FRONTIER_SMOKE'
            if passed else 'OBSERVABLE_TRIGGER_NOT_SUPPORTED_CLOSE_BN_APD_ROUTE')
(ROOT/'manifests/icba_bn_apd_trigger_decision.json').write_text(json.dumps({
    'decision': decision, 'evidence_level': 'EXPLORATORY_DEVELOPMENT_OBSERVABLE_TRIGGER_GATE',
    'instrumentation_rows': int(len(traces)), 'analysis_rows': int(len(joined)),
    'native_tracer_mismatches': int((~traces.native_tracer_equal.astype(bool)).sum()),
    'passed_rule_count': int(gates.both_pass.sum()), 'sealed_access': False,
    'independent_confirmation': False
}, indent=2) + '\n')
print(decision)
print(gates.to_string(index=False))
