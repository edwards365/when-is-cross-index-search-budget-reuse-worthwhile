import os,json,pandas as pd,numpy as np
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));R=ROOT+'/results/icba_decision_regret'
def test_01_paired_bootstrap():assert (pd.read_csv(R+'/oracle_paired_bootstrap.csv').bootstrap==5000).all()
def test_02_pooled_p95_counterexample():assert np.quantile([1,1,1,100],.95)!=np.mean([np.quantile([1,1],.95),np.quantile([1,100],.95)])
def test_03_risk_ucb():assert (pd.read_csv(R+'/oracle_risk_bounds.csv').binomial_ucb<.05).all()
def test_04_selection_eval():assert set(pd.read_csv(R+'/oracle_H4c_strict_replay.csv').heldout_cycle)==set(range(4))
def test_05_cert59():
 d=pd.read_csv(ROOT+'/results/active_recovery_headroom_reaudit/active_sentinel_plan_results.csv.gz');assert (~d[d.n_certification<59].certifiable).all()
def test_06_strict_eligibility():assert set(pd.read_csv(R+'/oracle_H4c_strict_replay.csv').selection_rule)=={'design_risk_ucb'}
def test_07_decomposition():assert pd.read_csv(R+'/decision_regret_summary.csv').decomposition_max_error.max()<1e-8
def test_08_accuracy_regret():
 y=np.array([0,1]);p1=np.array([1,1]);p2=np.array([0,0]);gaps=np.array([1.,100.]);assert (p1==y).mean()==(p2==y).mean()==.5;assert ((p1!=y)*gaps).mean()!=((p2!=y)*gaps).mean()
def test_09_confusion():assert {'cost_weight','mean_regret'}<=set(pd.read_csv(R+'/cost_weighted_confusion.csv').columns)
def test_10_near_optimal():assert pd.read_csv(R+'/near_optimal_action_rates.csv').near_5pct.between(0,1).all()
def test_11_fallback():
 d=pd.read_csv(R+'/action_level_replay.csv.gz');assert (d.loc[~d.certified_safe,'selected_action']=='FIXED:999').all()
def test_12_query_ids():assert pd.read_csv(R+'/candidate_query_costs.csv.gz',nrows=1000).query_id.notna().all()
def test_13_cluster_unit():assert pd.read_csv(R+'/oracle_build_level.csv').target_build.nunique()==18
def test_14_scope():assert json.load(open(ROOT+'/manifests/icba_decision_regret_decision.json'))['evidence_level']=='EXPLORATORY_FIXED_TARGET_DECISION_AUDIT'
def test_15_oracle_isolation():assert json.load(open(ROOT+'/manifests/icba_decision_regret_decision.json'))['independent_confirmation_authorized'] is False
def test_16_validation():assert not json.load(open(ROOT+'/manifests/icba_decision_regret_decision.json'))['validation_dev_accessed']
def test_17_formal():assert not json.load(open(ROOT+'/manifests/icba_decision_regret_decision.json'))['formal_test_accessed']
def test_18_label():assert json.load(open(ROOT+'/manifests/icba_decision_regret_decision.json'))['label']=='ORACLE_GAP_CONFIRMED_CURRENT_SIGNAL_FAMILY_RETIRED'
