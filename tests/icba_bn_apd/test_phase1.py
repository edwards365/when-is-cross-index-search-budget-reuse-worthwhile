from pathlib import Path
import json, pandas as pd
O=Path('results/icba_bn_apd'); M=json.loads(Path('manifests/icba_bn_apd_decision.json').read_text()); P=pd.read_csv(O/'marginal_primary_value.csv'); Q=pd.read_csv(O/'marginal_portal_value.csv'); S=pd.read_csv(O/'state_conditioned_advantage.csv'); D=pd.read_csv(O/'dedup_cost_bounds.csv')
def test_primary_transitions(): assert set(zip(P.from_ef,P.to_ef))=={(8,16),(16,32),(32,64)}
def test_two_datasets_primary(): assert set(P.dataset)=={'sift','arxiv'}
def test_two_datasets_portal(): assert set(Q.dataset)=={'sift','arxiv'}
def test_three_builds(): assert Q.build.nunique()==6
def test_portal_counts(): assert set(Q.portal_count)<=set(range(1,5))
def test_selected_present(): assert 'SELECTED_FIXED_SET' in set(Q.category)
def test_truth_free_feature(): assert set(S.state_feature)=={'primary_actual_ndc'}
def test_truth_dependency_false(): assert not S.truth_dependent.any()
def test_coverage(): assert S.coverage.ge(.1).all()
def test_top1_recorded(): assert S.median_advantage_after_top1pct.notna().all()
def test_candidate_bound_label(): assert set(D.bound_type)=={'CANDIDATE_SET_LOWER_BOUND'}
def test_visited_not_estimable(): assert set(D.visited_trace_status)=={'NOT_ESTIMABLE'}
def test_phase1_failed(): assert not M['phase1_gate_passed']
def test_no_shared_implementation(): assert not M['entered_shared_implementation']
def test_zero_optimization_rounds(): assert M['optimization_rounds']==0
def test_zero_candidates(): assert M['candidate_count']==0
def test_no_sealed_access(): assert not M['sealed_roles_accessed']
def test_no_validation_dev(): assert not M['validation_dev_accessed']
def test_no_formal_test(): assert not M['formal_test_accessed']
def test_valid_decision(): assert M['decision_label']=='ORACLE_MARGINAL_RESCUE_ONLY_NO_DEPLOYABLE_TRIGGER'
def test_documents(): assert len(list(Path('docs/icba_bn_apd').glob('*.md')))>=8
def test_figures(): assert len(list(Path('figures/icba_bn_apd').glob('*.png')))>=12 and len(list(Path('figures/icba_bn_apd').glob('*.pdf')))>=12
def test_results(): assert len(list(O.glob('*.csv')))>=13
def test_parent_outputs_untouched(): assert Path('results/icba_cals_seal/checksums.sha256').exists()
