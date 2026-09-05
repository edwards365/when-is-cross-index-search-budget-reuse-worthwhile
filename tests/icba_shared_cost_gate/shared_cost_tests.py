from pathlib import Path
import json
import pandas as pd

R=Path('/home/wlk/projects/navigation-aware-resistance-hnsw/results/icba_shared_cost_gate')
def test_outputs():
    for n in ['quality_feasibility.csv','critical_compression.csv','candidate_overlap_bounds.csv','compression_margin.csv','bootstrap_results.csv','lobo_results.csv','unified_gate_table.csv']:
        assert (R/n).exists()
def test_kappa_and_margin():
    c=pd.read_csv(R/'critical_compression.csv'); m=pd.read_csv(R/'compression_margin.csv')
    assert c[c.metric.eq('kappa_cost')]['median'].gt(0).all()
    assert m.compression_margin.notna().all()
def test_shared_cost_not_estimable():
    assert pd.read_csv(R/'candidate_overlap_bounds.csv').semantics.str.contains('NOT_ESTIMABLE').all()
def test_gate_and_decision():
    g=pd.read_csv(R/'unified_gate_table.csv'); assert not g[g.gate.eq('required_compression_le_050')].passed.iloc[0]
    d=json.loads(Path('/home/wlk/projects/navigation-aware-resistance-hnsw/manifests/icba_shared_cost_gate_decision.json').read_text()); assert d['decision']=='SHARED_COST_ONLY_ORACLE_BOUND_NO_IMPLEMENTATION'
def test_no_sealed_access():
    d=json.loads(Path('/home/wlk/projects/navigation-aware-resistance-hnsw/manifests/icba_shared_cost_gate_decision.json').read_text()); assert d['sealed_roles_accessed'] is False
