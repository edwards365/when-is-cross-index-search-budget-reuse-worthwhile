import json,pathlib,numpy as np,pandas as pd
R=pathlib.Path(__file__).resolve().parents[2];O=R/'results/graph_anns_e4_seal'
inv=pd.read_csv(O/'input_inventory.csv');h1=pd.read_csv(O/'h1_crossed_cluster_inference.csv');h2=pd.read_csv(O/'h2_transport_summary.csv');ci=pd.read_csv(O/'h2_crossed_cluster_inference.csv');comp=pd.read_csv(O/'transport_event_composition.csv');cp=pd.read_csv(O/'simultaneous_certification.csv');rob=pd.read_csv(O/'h2_robustness.csv')
def test_01_frozen_rows(): assert len(inv)==96 and inv.query_count.sum()==48_000
def test_02_build_unique(): assert inv.drop_duplicates('build_id').groupby(['dataset','seed','insertion_order']).size().eq(1).all()
def test_03_pair_count(): assert h2.pairs.eq(552).all()
def test_04_roles(): assert set(inv.query_role)=={'sentinel','evaluation'} and inv.groupby(['build_id','query_role']).size().eq(1).all()
def test_05_grid(): assert set(inv.budget_grid)=={'10|20|40|80|120|200'}
def test_06_endpoint_direction(): assert h2.source_endpoint.ge(0).all() and h2.target_endpoint.ge(0).all()
def test_07_censor_direction(): assert h2.right_censored.ge(h2.source_endpoint).all()
def test_08_event_complete(): assert np.allclose(comp[['SOURCE_ENDPOINT_INFEASIBLE','TARGET_ENDPOINT_INFEASIBLE','RIGHT_CENSORED','UNSAFE_UNDER_BUDGET','SAFE_EXACT','SAFE_OVER_BUDGET']].sum(axis=1),1)
def test_09_new_ci_contains_point():
 assert ((h1.disagreement>=h1.disagreement_ci_low)&(h1.disagreement<=h1.disagreement_ci_high)).all()
 assert ((ci.risk_increment>=ci.risk_ci_low)&(ci.risk_increment<=ci.risk_ci_high)).all()
def test_10_pair_not_iid(): assert ci.resampling.str.contains('shared pair structure').all()
def test_11_within_seed_order(): assert set(h1.estimand_id)=={'H1-B','H1-C'} and h1[h1.estimand_id=='H1-B'].disagreement.gt(0).all()
def test_12_within_order_seed(): assert h1[h1.estimand_id=='H1-C'].absolute_difference.gt(0).all()
def test_13_random_subset(): assert rob[rob.analysis=='random_only'].groupby('dataset').size().eq(1).all()
def test_14_loso_complete(): assert rob[rob.analysis=='leave_one_seed'].groupby('dataset').size().eq(8).all()
def test_15_rom_formula(): assert np.allclose(h2.ratio_of_means,[.194472095841,.148793063699])
def test_16_mor_formula(): assert np.allclose(h2.mean_of_ratios,[.238654828075,.170647409958]) and not np.allclose(h2.ratio_of_means,h2.mean_of_ratios)
def test_17_unsafe_not_gain(): assert h2.absolute_ndc_difference.gt(0).all()
def test_18_bonferroni_alpha(): assert cp.simultaneous_cp.ge(cp.ordinary_cp).all()
def test_19_cp_direction(): assert cp.sort_values(['dataset','failures']).groupby('dataset').simultaneous_cp.apply(lambda x:x.is_monotonic_increasing).all()
def test_20_manifest_firewall():
 m=json.loads((R/'manifests/graph_anns_e4_seal_decision.json').read_text());assert not m['future_replication_accessed'] and not m['validation_dev_accessed'] and not m['formal_test_accessed']
