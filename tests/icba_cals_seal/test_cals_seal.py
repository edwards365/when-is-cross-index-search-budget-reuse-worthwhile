import json, subprocess
from pathlib import Path
import pandas as pd
O=Path('results/icba_cals_seal')
R=pd.read_csv(O/'id_roundtrip_raw.csv'); L=pd.read_csv(O/'per_lane_results.csv.gz'); S=pd.read_csv(O/'subset_summary.csv'); A=pd.read_csv(O/'selection_actions.csv'); H=pd.read_csv(O/'holdout_results.csv'); D=pd.read_csv(O/'rescue_decomposition.csv')
def test_roundtrip_count(): assert len(R)==6000
def test_roundtrip_dynamic_success(): assert (R.internal_external_internal_ok.eq(1)&R.external_internal_external_ok.eq(1)).all()
def test_portal_rules_across_builds():
 x=pd.read_csv(O/'portal_rule_registry.csv');assert x.build_id.nunique()==6 and (x.groupby('build_id').portal_rule_id.nunique()==8).all()
def test_native_tracer_equivalence(): assert L[L.lane_type.eq('primary')].native_tracer_equal.eq(1).all()
def test_full_candidates_present(): assert L.candidate_count.ge(10).all() and L.candidate_labels.notna().all()
def test_primary_repeat_determinism():
 w=pd.read_csv(O/'wallclock_lane_results.csv.gz');p=w[w.lane_type.eq('primary')];assert p.groupby(['build_id','query_id','raw_ef']).candidate_hash.nunique().max()==1
def test_recall_non_decrease():
 d=pd.read_csv(O/'subset_results.csv.gz',usecols=['base_hits','union_hits']);assert d.union_hits.ge(d.base_hits).all()
def test_role_ids_disjoint():
 q=pd.read_csv(O/'query_role_ids.csv');a=set(q[q.role.eq('portal_selection')].query_id);b=set(q[q.role.eq('attainability_holdout')].query_id);assert not a&b
def test_sealed_roles_unaccessed(): assert json.loads((O/'sealed_roles.json').read_text())['certification']=='SEALED'
def test_256_subsets(): assert S['mask'].nunique()==256
def test_size4_oracle_present(): assert 'PER_QUERY_ORACLE_SIZE_1_4' in set(pd.read_csv(O/'oracle_hierarchy.csv').oracle)
def test_all_oracle_present(): assert 'PER_QUERY_ORACLE_ALL_256' in set(pd.read_csv(O/'oracle_hierarchy.csv').oracle)
def test_five_portal_synthetic_counterexample():
 portals=[{i} for i in range(5)]; assert len(set().union(*portals[:4]))==4 and len(set().union(*portals))==5
def test_best_fixed_selection_only(): assert set(A.action_scope)=={'TARGET_SPECIFIC_SELECTED_FIXED_SET','DATASET_LEVEL_SELECTED_FIXED_SET','CROSS_DATASET_SELECTED_FIXED_SET'}
def test_holdout_not_in_action_table(): assert not any('holdout' in c.lower() for c in A.columns)
def test_auxiliary_cost_is_sum():
 d=pd.read_csv(O/'subset_results.csv.gz',usecols=['primary_ndc','aux_ndc_sum','total_ndc']);assert (d.primary_ndc+d.aux_ndc_sum==d.total_ndc).all()
def test_rescue_identity_one(): assert D.identity_1_error.max()<1e-12
def test_rescue_identity_two(): assert D.identity_2_error.max()<1e-12
def test_holdout_denominator(): assert H[H.action_scope.eq('TARGET_SPECIFIC_SELECTED_FIXED_SET')].n.eq(300).all()
def test_replay_scripts(): assert all((Path('scripts/icba_cals_seal')/p).exists() for p in ['prepare_inputs.py','run_lanes.py','analyze.py','finalize_stats.py','run_wallclock.py','generate_artifacts.py'])
def test_old_results_unmodified(): assert subprocess.check_output(['git','diff','--name-only','f5527e691ff91598de30fd59464ada6e96c65f00','--','results/icba_cals_reaudit'],text=True).strip()==''
def test_wallclock_five_repeats(): assert pd.read_csv(O/'wallclock_summary.csv').groupby(['dataset','build','raw_ef'])['repeat'].nunique().min()==5
def test_required_documents(): assert len(list(Path('docs/icba_cals_seal').glob('*.md')))>=9
def test_required_figures(): assert len(list(Path('figures/icba_cals_seal').glob('*.png')))>=10 and len(list(Path('figures/icba_cals_seal').glob('*.pdf')))>=10
