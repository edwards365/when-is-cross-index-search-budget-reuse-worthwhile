from pathlib import Path
import json
import pandas as pd

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
OUT=ROOT/'results/icba_bn_apd_trigger'

def test_instrumentation_row_count():
    files=list(OUT.glob('trace_*_*.csv'))
    assert len(files)==12
    assert sum(len(pd.read_csv(p)) for p in files)==12000

def test_native_equivalence():
    assert all(pd.read_csv(p).native_tracer_equal.eq(1).all() for p in OUT.glob('trace_*_*.csv'))

def test_truth_free_trace_schema():
    forbidden={'recall','truth','hit','risk','label','advantage'}
    for p in OUT.glob('trace_*_*.csv'):
        cols={c.lower() for c in pd.read_csv(p,nrows=0).columns}
        assert not any(any(word in c for word in forbidden) for c in cols)

def test_roles_are_development_only():
    m=json.loads((ROOT/'manifests/icba_bn_apd_trigger_preregistration.json').read_text())
    assert m['query_role']=='bn_apd_replay_development'
    assert not m['independent_confirmation'] and not m['sealed_roles_accessed']

def test_fixed_split_and_no_overlap():
    joined=pd.read_csv(OUT/'trace_outcome_join.csv.gz')
    assert joined.loc[joined['split'].eq('proposal'),'query_id'].max()<250
    assert joined.loc[joined['split'].eq('validation'),'query_id'].min()>=250

def test_decision_vocabulary():
    d=json.loads((ROOT/'manifests/icba_bn_apd_trigger_decision.json').read_text())
    assert d['decision'] in {'OBSERVABLE_TRIGGER_SIGNAL_SUPPORTED_AUTHORIZE_SHARED_FRONTIER_SMOKE','OBSERVABLE_TRIGGER_NOT_SUPPORTED_CLOSE_BN_APD_ROUTE'}
