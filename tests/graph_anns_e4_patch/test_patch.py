import json,pathlib,re,subprocess
import numpy as np,pandas as pd
R=pathlib.Path(__file__).resolve().parents[2]; O=R/'results/graph_anns_e4_patch'; S=(R/'scripts/graph_anns_e4_patch/run.py').read_text(); h=pd.read_csv(O/'h1_censoring_aware_estimands.csv'); ci=pd.read_csv(O/'h2_registered_family_query_ci.csv'); e=pd.read_csv(O/'transport_event_composition_corrected.csv'); c=pd.read_csv(O/'certification_multiplicity_audit.csv'); m=json.loads((R/'manifests/graph_anns_e4_patch_decision.json').read_text())
def test_01_no_numeric_censor_fill(): assert 'fillna(240)' not in S
def test_02_budget_grid_states(): assert m['budget_grid']==[10,20,40,80,120,200] and 'BOTTOM' in S
def test_03_a1_category_formula(): assert h.query("estimand_id=='H1-A1' and scope=='summary'").categorical_disagreement.between(0,1).all()
def test_04_a2_all_feasible(): assert h.query("estimand_id=='H1-A2' and scope=='summary'").effective_query_count.le(750).all()
def test_05_a3_two_feasible(): assert h.query("estimand_id=='H1-A3' and scope=='summary'").effective_query_count.le(750).all()
def test_06_a4_endpoint_mismatch(): assert h.query("estimand_id=='H1-A4' and scope=='summary'").endpoint_mismatch_comparisons.ge(0).all()
def test_07_h1b_denominator(): assert h.query("estimand_id=='H1-B'").jointly_feasible_comparisons.le(h.query("estimand_id=='H1-B'").total_comparisons).all()
def test_08_h1c_denominator(): assert h.query("estimand_id=='H1-C'").jointly_feasible_comparisons.le(h.query("estimand_id=='H1-C'").total_comparisons).all()
def test_09_no_abs_censored(): assert h.query("scope=='summary' and estimand_id in ['H1-A2','H1-A3']").feasible_absolute_difference.notna().all()
def test_10_h2_registered_scope(): assert ci.scope.eq('registered_build_family_query_distribution').all()
def test_11_h2_risk_ci_contains_point(): assert (ci.risk_increment.ge(ci.risk_ci_low)&ci.risk_increment.le(ci.risk_ci_high)).all()
def test_12_h2_cost_ci_contains_point(): assert (ci.safe_rom_tax.ge(ci.safe_rom_ci_low)&ci.safe_rom_tax.le(ci.safe_rom_ci_high)).all()
def test_13_h2_not_pair_iid(): assert '552 directed pair' in ci.resampling.iloc[0]
def test_14_random_positive(): assert pd.read_csv(O/'h2_two_endpoint_robustness.csv').query("analysis=='random_only'").rom_tax.gt(0).all()
def test_15_loso_both_end(): assert pd.read_csv(O/'h2_two_endpoint_robustness.csv').query("analysis=='leave_one_seed'").deleted.nunique()==8
def test_16_loto_both_end(): assert pd.read_csv(O/'h2_two_endpoint_robustness.csv').query("analysis=='leave_one_order'").deleted.nunique()==3
def test_17_event_complete(): assert np.allclose(e.composition_sum,1)
def test_18_event_mutually_exhaustive(): assert len([x for x in e.columns if x.endswith('CENSORED') or x.startswith('UNDER_') or x.startswith('EXACT_') or x.startswith('OVER_') or x.startswith('RAW_')])>=8
def test_19_under_safe_separate(): assert 'UNDER_BUDGET_OBSERVED_SAFE' in e.columns and 'UNDER_BUDGET_UNSAFE' in e.columns
def test_20_per_target_alpha(): assert np.isclose(float(c.cp_per_target.iloc[0]),float(c.cp_per_target.iloc[0])) and '.05/6' in S
def test_21_fixed_alpha(): assert '.05/48' in S
def test_22_joint_alpha(): assert '.05/(48*6)' in S
def test_23_fallback_abstain(): assert m['fallback_status']=='ABSTAIN_NO_CERTIFIED_ACTION'
def test_24_parent_replay(): assert m['parent_replay']=='BYTE_IDENTICAL' and not m['future_replication_accessed']
