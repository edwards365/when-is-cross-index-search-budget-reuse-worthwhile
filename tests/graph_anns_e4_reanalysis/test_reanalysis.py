import json,pathlib,pandas as pd,numpy as np
r=pathlib.Path(__file__).resolve().parents[2]
p=pd.read_csv(r/'results/graph_anns_e4_reanalysis/oracle_transport_directed_pairs.csv');q=pd.read_csv(r/'results/graph_anns_e4_reanalysis/query_role_mapping.csv');m=json.loads((r/'manifests/graph_anns_e4_semantic_reanalysis_decision.json').read_text())
def test_01_diag_budget(): assert (p[p.diagonal].mean_abs_budget_difference.fillna(0)==0).all()
def test_02_diag_ndc(): assert (p[p.diagonal].absolute_ndc_transport_cost.fillna(0)==0).all()
def test_03_under(): assert (p.under_budget_rate>0).any()
def test_04_over(): assert (p.over_budget_rate>0).any()
def test_05_endpoint(): assert (p.source_fallback_rate>0).any()
def test_06_raw_nonmono(): assert pd.read_csv(r/'results/graph_anns_e4_reanalysis/h1_within_order.csv').raw_nonmonotonicity.ge(0).all()
def test_07_split(): assert set(q[q.local_query_id<250].role)=={'target_sentinel'} and set(q[q.local_query_id>=250].role)=={'confirmatory_evaluation'}
def test_08_bonf(): assert pd.read_csv(r/'results/graph_anns_e4_reanalysis/per_target_cp_audit.csv').cp_ucb_bonferroni_48.ge(pd.read_csv(r/'results/graph_anns_e4_reanalysis/per_target_cp_audit.csv').cp_ucb_95).all()
def test_09_seedblock(): assert set(pd.read_csv(r/'results/graph_anns_e4_reanalysis/seed_block_bootstrap.csv').unit)=={'seed_block_keep_three_orders'}
def test_10_cross(): assert len(pd.read_csv(r/'results/graph_anns_e4_reanalysis/crossed_seed_query_bootstrap.csv'))==4
def test_11_los(): assert pd.read_csv(r/'results/graph_anns_e4_reanalysis/leave_one_seed_out.csv').pairs.gt(0).all()
def test_12_loo(): assert pd.read_csv(r/'results/graph_anns_e4_reanalysis/leave_one_order_out.csv').pairs.gt(0).all()
def test_13_regret(): assert (pd.read_csv(r/'results/graph_anns_e4_reanalysis/ndc_regret_definitions.csv').ratio_of_means!=pd.read_csv(r/'results/graph_anns_e4_reanalysis/ndc_regret_definitions.csv').mean_of_ratios).all()
def test_14_unsafe(): assert set(p.point_classification).issubset({'DIAGONAL_REFERENCE','UNSAFE_TRANSPORT','SAFE_BUT_CONSERVATIVE','PORTABLE_WITHIN_TOLERANCE','SOURCE_ENDPOINT_INFEASIBLE','TARGET_ENDPOINT_INFEASIBLE'})
def test_15_pairs(): assert p[~p.diagonal].groupby('dataset').size().eq(552).all()
def test_16_sources(): assert p[~p.diagonal].groupby('dataset').source_build.nunique().eq(24).all()
def test_17_firewall(): assert not m['future_replication_accessed'] and not m['validation_dev_accessed'] and not m['formal_test_accessed']
def test_18_original(): assert not m['original_e4_modified']
