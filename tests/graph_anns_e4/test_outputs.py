import hashlib, json
from pathlib import Path
import pandas as pd

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')

def test_decision_and_matrix_complete():
    d=json.loads((ROOT/'manifests/graph_anns_e4_confirmatory_decision.json').read_text())
    assert d['label']=='E4_STRONG_CONFIRMATION_TWO_DATASETS'
    assert d['builds']==d['builds_succeeded']==48
    assert set(d['dataset_gates'].values())=={'STRONG_SUPPORT'}

def test_roles_and_firewall():
    r=pd.read_csv(ROOT/'results/graph_anns_e4/role_overlap.csv')
    assert not ((~r.allowed.astype(bool)) & (r.overlap>0)).any()
    d=json.loads((ROOT/'manifests/graph_anns_e4_confirmatory_decision.json').read_text())
    assert not d['future_replication_accessed']
    assert not d['validation_dev_accessed']
    assert not d['formal_test_accessed']

def test_build_and_budget_counts():
    b=pd.read_csv(ROOT/'results/graph_anns_e4/build_manifest.csv')
    assert len(b)==48
    assert (b.groupby('dataset').size()==24).all()
    q=pd.read_parquet(ROOT/'results/graph_anns_e4/per_query_budget_response.parquet')
    assert len(q)==48000
    assert q.groupby(['dataset','build_id']).size().eq(1000).all()

def test_cluster_intervals_and_robustness():
    g=pd.read_csv(ROOT/'results/graph_anns_e4/unified_gate_table.csv')
    assert (g.dataset_gate=='STRONG_SUPPORT').all()
    assert (g.ndc_regret_ci_low>.01).all()
    l=pd.read_csv(ROOT/'results/graph_anns_e4/leave_one_build_out.csv')
    assert l.direction_positive.astype(bool).all()
    t=pd.read_csv(ROOT/'results/graph_anns_e4/top1pct_robustness.csv')
    assert t.direction_preserved.astype(bool).all()

def test_figures_and_checksums():
    assert len(list((ROOT/'figures/graph_anns_e4').glob('*.png')))==8
    assert len(list((ROOT/'figures/graph_anns_e4').glob('*.pdf')))==8
    for line in (ROOT/'results/graph_anns_e4/checksums.sha256').read_text().splitlines():
        expected,rel=line.split('  ',1);h=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest();assert h==expected
