import os,json,pandas as pd
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));R=ROOT+'/results/active_recovery_headroom_reaudit'
def test_01_h2_draws(): assert (pd.read_csv(R+'/h2_randomized_summary.csv').draws==5000).all()
def test_02_unit(): assert set(pd.read_csv(R+'/h2_randomized_summary.csv').randomization_unit)=={'recovery_episode'}
def test_03_h3_datasets(): assert pd.read_csv(R+'/h3_environment_oracle_crossfit.csv').dataset.nunique()==2
def test_04_h4_datasets(): assert pd.read_csv(R+'/h4_pair_oracle_crossfit.csv').dataset.nunique()==2
def test_05_h3_heldout(): assert set(pd.read_csv(R+'/h3_environment_oracle_crossfit.csv').heldout_cycle)==set(range(4))
def test_06_h4_heldout(): assert set(pd.read_csv(R+'/h4_pair_oracle_crossfit.csv').heldout_cycle)==set(range(4))
def test_07_risk(): assert (pd.read_csv(R+'/gate_h_robustness.csv').abs_risk<=.05).all()
def test_08_ci(): assert (pd.read_csv(R+'/gate_h_robustness.csv').ci_low>.05).all()
def test_09_delete(): assert (pd.read_csv(R+'/gate_h_robustness.csv').delete_max_build_headroom>.05).all()
def test_10_p95(): assert pd.read_csv(R+'/gate_h_robustness.csv').p95_not_worse.all()
def test_11_strong(): assert pd.read_csv(R+'/gate_h_robustness.csv').gate_strong_components.all()
def test_12_cert_disjoint():
 d=pd.read_csv(R+'/active_sentinel_plan_results.csv.gz');assert (d.selection_hash!=d.certification_hash).all()
def test_13_under59():
 d=pd.read_csv(R+'/active_sentinel_plan_results.csv.gz');assert (~d[d.n_certification<59].certifiable).all()
def test_14_deploy_positive(): assert (pd.read_csv(R+'/active_sentinel_best_deployable.csv').n_selection>0).all()
def test_15_no_signal(): assert (pd.read_csv(R+'/active_sentinel_best_deployable.csv').accuracy_gain<0).all()
def test_16_theory(): assert pd.read_csv(R+'/theory_status.csv').claim.nunique()==6
def test_17_manifest(): assert json.load(open(ROOT+'/manifests/active_recovery_headroom_reaudit_decision.json'))['label']=='CORRECTED_HEADROOM_CONFIRMED_NO_DEPLOYABLE_SIGNAL'
def test_18_scope(): assert json.load(open(ROOT+'/manifests/active_recovery_headroom_reaudit_decision.json'))['scope']=='FIXED_TARGET_DESIGN_ONLY'
