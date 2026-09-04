import pandas as pd
from pathlib import Path
R=pd.read_csv("results/icba_cals_reaudit/rescue_matrix.csv")
def test_all_256_subsets(): assert R["mask"].nunique()==256
def test_both_datasets(): assert set(R.dataset)=={"SIFT-100K","Arxiv-Nomic-100K"}
def test_positive_gain(): assert R.n_positive_hit_gain.max()>0
def test_outputs_exist(): assert Path("results/icba_cals_reaudit/oracle_hierarchy.csv").exists()
def test_efs(): assert set(R.raw_ef)=={8,16,32,64}
def test_builds(): assert R.build.nunique()==3
def test_rows(): assert len(R)==6144
def test_recall_bounds(): assert ((R.union_mean_recall>=0)&(R.union_mean_recall<=1)).all()
def test_risk_bounds(): assert ((R.union_risk>=0)&(R.union_risk<=1)).all()
def test_subset_nonnegative(): assert (R.n_positive_hit_gain>=0).all()
def test_threshold_nonnegative(): assert (R.n_threshold_rescues>=0).all()
def test_primary_failures(): assert (R.n_primary_failures>=0).all()
def test_subset_labels_present(): assert R.portal_set.notna().all()
def test_oracle_status():
 o=pd.read_csv("results/icba_cals_reaudit/oracle_hierarchy.csv"); assert "NON_DEPLOYABLE_PER_QUERY_ORACLE" in set(o.oracle_status)
def test_summary(): assert Path("results/icba_cals_reaudit/semantic_summary.csv").exists()
def test_manifest(): assert Path("manifests/icba_cals_reaudit_decision.json").exists()
def test_holdout_sift(): assert Path("results/icba_cals_reaudit/attainability_holdout_100k.fbin").exists()
def test_holdout_arxiv(): assert Path("results/icba_cals_reaudit/attainability_holdout_arxiv100k.fbin").exists()
def test_docs(): assert len(list(Path("docs/icba_cals_reaudit").glob("*.md")))>=8
def test_figures(): assert len(list(Path("figures/icba_cals_reaudit").glob("*.png")))>=8
