from pathlib import Path
import json
import pandas as pd

R=Path('/home/wlk/projects/navigation-aware-resistance-hnsw/results/icba_bn_apd_route_closure')
def test_semantic_schema():
    d=pd.read_csv(R/'trace_schema_repair.csv'); assert set(d.repaired_name)=={'ef_heap_lower_bound','frontier_lower_bound_ratio','lower_bound_improvement_w4','lower_bound_improvement_w8','lower_bound_improvement_w16'}
def test_lobo_and_coverage():
    assert len(pd.read_csv(R/'trigger_lobo.csv'))>0
    assert {'coverage_pass','cell_pass','failure_reason'} <= set(pd.read_csv(R/'trigger_coverage_audit.csv').columns)
def test_fixed_split_closed():
    d=pd.read_csv(R/'fixed_split_eligibility.csv'); assert not d.fixed_split_pass.any(); assert (d.positive_builds==0).all()
def test_cost_bound_not_shared_cost():
    d=pd.read_csv(R/'dedup_cost_lower_bound.csv'); assert d.shared_frontier_cost.eq('NOT_ESTIMABLE').all()
def test_decision():
    d=json.loads(Path('/home/wlk/projects/navigation-aware-resistance-hnsw/manifests/icba_bn_apd_route_closure_decision.json').read_text()); assert d['decision']=='BN_APD_ROUTE_CLOSED_NO_GLOBAL_FIXED_SPLIT'
