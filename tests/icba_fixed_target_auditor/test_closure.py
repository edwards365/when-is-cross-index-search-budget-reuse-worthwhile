from pathlib import Path
import json
import pandas as pd

ROOT=Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
R=ROOT/"results/icba_fixed_target_auditor"
M=ROOT/"manifests"

def test_recovery_decision(): assert json.loads((M/"icba_fixed_target_auditor_data_recovery.json").read_text())["decision"]=="FINITE_GRID_DATA_RECOVERED_NOT_12_LEVEL"
def test_checksums_all_match(): assert pd.read_csv(R/"checksum_replay.csv")["match"].all()
def test_81_runs(): assert pd.read_csv(R/"grid_inventory.csv").run_id.nunique()==81
def test_common_grid(): assert set([10,20,40,80,120,200]).issubset(set.intersection(*[set(map(int,x.split(";"))) for x in pd.read_csv(R/"grid_inventory.csv").ef_grid]))
def test_six_policies(): assert len(pd.read_csv(R/"source_policy_registry.csv"))==6
def test_policy_ef(): assert set(pd.read_csv(R/"source_policy_registry.csv").raw_ef)=={120}
def test_role_overlap():
 d=pd.read_csv(R/"query_overlap_matrix.csv"); assert (d[d.role_a!=d.role_b].overlap==0).all()
def test_sixty_fold_decisions(): assert len(pd.read_csv(R/"crossfit_decisions.csv"))==60
def test_one_action_per_decision(): assert pd.read_csv(R/"crossfit_decisions.csv").deployed_action.notna().all()
def test_no_unsafe_acceptance(): assert pd.read_csv(R/"evaluation_results.csv").unsafe_acceptance.sum()==0
def test_nontrivial_actions(): assert (pd.read_csv(R/"crossfit_decisions.csv").deployed_action!="A6").sum()==36
def test_abstentions(): assert (pd.read_csv(R/"crossfit_decisions.csv").deployed_action=="A6").sum()==24
def test_fallback_not_automatically_safe(): assert set(pd.read_csv(R/"fallback_candidate_registry.csv").status_before_certification)=={"FALLBACK_CANDIDATE"}
def test_alpha_split(): assert set(pd.read_csv(R/"certification_results.csv").alpha_share)=={.025}
def test_regret_not_zero_by_construction(): assert (pd.read_csv(R/"build_cluster_bootstrap.csv").ci_low>0).all()
def test_lobo_negative_result_robust(): assert pd.read_csv(R/"lobo_results.csv").positive_regret_persists.all()
def test_no_real_break_even_claim(): assert set(pd.read_csv(R/"cost_break_even.csv").break_even)=={"SYMBOLIC_BREAK_EVEN_ONLY"}
def test_future_not_accessed(): assert not json.loads((M/"icba_fixed_target_auditor_decision.json").read_text())["future_confirm_accessed"]
def test_forbidden_not_accessed():
 d=json.loads((M/"icba_fixed_target_auditor_decision.json").read_text()); assert not d["validation_dev_accessed"] and not d["formal_test_accessed"]
def test_final_label(): assert json.loads((M/"icba_fixed_target_auditor_decision.json").read_text())["decision"]=="ICBA_DECISION_REGRET_NOT_IMPROVED"
