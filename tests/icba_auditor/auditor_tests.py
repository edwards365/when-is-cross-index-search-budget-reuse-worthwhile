from pathlib import Path
import json
import pandas as pd
R=Path('/home/wlk/projects/navigation-aware-resistance-hnsw/results/icba_auditor')
def test_required_outputs():
    for n in ['input_inventory.csv','action_registry.csv','endpoint_audit.csv','certification_results.csv','decision_results.csv','decision_regret.csv','cost_break_even.csv','tail_cost.csv','baseline_comparison.csv','unified_gate_table.csv']:
        assert (R/n).exists()
def test_action_freeze():
    d=pd.read_csv(R/'action_registry.csv'); assert set(d.action)=={'REUSE_SOURCE_POLICY','CONSERVATIVE_REUSE','TARGET_RECALIBRATION','TARGET_REPROFILE_OR_RETRAIN','FULL_RETRAINING','FIXED_SAFE_FALLBACK','REJECT_ABSTAIN'}
def test_cp_direction():
    d=pd.read_csv(R/'certification_results.csv'); assert ((d.cp_upper>=0)&(d.cp_upper<=1)).all()
def test_decision_manifest():
    d=json.loads(Path('/home/wlk/projects/navigation-aware-resistance-hnsw/manifests/icba_auditor_decision.json').read_text()); assert not d['future_confirm_accessed']; assert d['decision']=='ICBA_UNIFIED_METHOD_NOT_READY_FOR_PROSPECTIVE_CONFIRMATION'
def test_no_sealed_access():
    d=json.loads(Path('/home/wlk/projects/navigation-aware-resistance-hnsw/manifests/icba_auditor_decision.json').read_text()); assert d['sealed_roles_accessed'] is False
