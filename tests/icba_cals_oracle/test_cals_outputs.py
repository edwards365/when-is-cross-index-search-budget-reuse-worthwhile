from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).parents[2]
OUT=ROOT/"results/icba_cals_oracle"
def test_lane_rows_exist():
    files=list(OUT.glob("lane_rows_*100k-b*.csv")); assert len(files)==6
def test_lane_row_count():
    assert sum(len(pd.read_csv(p)) for p in OUT.glob("lane_rows_*100k-b*.csv"))==72000
def test_mechanical_flags():
    d=pd.read_csv(OUT/"per_lane_results.csv")
    for c in ["primary_recomputed_equal","primary_subset_union","union_recall_ge_primary","alternate_repeat_equal"]: assert d[c].eq(1).all()
def test_union_never_below_primary():
    d=pd.read_csv(OUT/"per_lane_results.csv"); assert d["union_recall"].ge(d["primary_recall"]).all()
def test_role_firewall():
    d=pd.read_csv(OUT/"query_role_audit.csv"); assert d["overlap_with_other_roles"].eq(0).all(); assert set(d.query("role in ['certification_reserved','evaluation_reserved','future_confirmation']")["truth_access"])=={"SEALED"}
def test_portals_fixed_rule():
    d=pd.read_csv(OUT/"portal_registry.csv"); assert d["portal_type"].eq("FIXED_RULE").all()
def test_build_cluster_seed():
    d=pd.read_csv(OUT/"build_cluster_bootstrap.csv"); assert d["seed"].eq(991).all(); assert d["n_builds"].le(3).all()
def test_mechanical_invariants_pass():
    d=pd.read_csv(OUT/"mechanical_invariants.csv"); assert d["status"].eq("PASS").all()
def test_no_fixed_portal_safety_gate():
    d=pd.read_csv(OUT/"rescue_matrix.csv"); fixed=d[d["portal_id"].astype(str)!="ORACLE_PER_QUERY"]; assert not fixed["fixed_safe_at_5pct"].astype(bool).any()
def test_oracle_non_deployable():
    m=json.loads((OUT/"manifest_snapshot.json").read_text()); assert m["oracle_non_deployable"] is True
def test_symbolic_cost_only():
    d=pd.read_csv(OUT/"break_even.csv"); assert d["break_even"].eq("SYMBOLIC_COST_ONLY").all()
def test_figures_and_checksums():
    assert len(list((ROOT/"figures/icba_cals_oracle").glob("*.png")))>=8; assert (OUT/"checksums.sha256").exists()
