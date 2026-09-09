from pathlib import Path
import json
import numpy as np, pandas as pd

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"results/graph_anns_faiss_external_validity"
def r(n):return pd.read_csv(OUT/n)

def test_registered_build_count(): assert r("build_registry.csv").groupby("dataset").size().eq(24).all()
def test_directed_pair_count(): assert r("h2_risk_cost_summary.csv").pairs.eq(552).all()
def test_confirmatory_query_count(): assert r("h2_risk_cost_summary.csv").queries_per_pair.eq(750).all()
def test_role_counts(): assert set(r("query_role_audit.csv").groupby("role").count()["dataset"])=={2}
def test_role_sizes(): assert dict(r("query_role_audit.csv").groupby("role")["count"].first())=={"confirmatory_evaluation":750,"future_replication":200,"grid_design":200,"runtime_measurement":100}
def test_native_reload_equivalence(): assert r("native_tracer_equivalence.csv").native_reload_topk_equal.all()
def test_id_mapping(): assert r("native_tracer_equivalence.csv").id_mapping_errors.eq(0).all()
def test_h1_positive(): assert r("h1_category_variation.csv").category_variation_rate.gt(0).all()
def test_h1_mixed_is_bounded(): assert r("h1_category_variation.csv").mixed_feasible_censored_rate.between(0,1).all()
def test_h1_counts_partition():
 x=r("h1_category_variation.csv"); assert (x.all_feasible_count+x.all_censored_count <= x.query_count).all()
def test_numeric_bottom_not_imputed(): assert r("h1_numeric_dispersion.csv").jointly_feasible_mean_abs_diff.notna().all()
def test_absolute_reference_increment_identity():
 x=r("h2_risk_cost_summary.csv");assert np.allclose(x.absolute_transport_risk-x.source_reference_risk,x.incremental_transport_risk)
def test_event_partition(): assert np.allclose(r("h2_event_composition.csv").composition_sum,1)
def test_event_rows_expected(): assert len(r("h2_event_composition.csv"))==1104
def test_bootstrap_registered():
 x=r("bootstrap_intervals.csv");assert x.bootstrap.eq(5000).all() and x.seed.eq(991).all()
def test_risk_ci_positive(): assert r("bootstrap_intervals.csv").risk_ci_low.gt(0).all()
def test_rom_ci_positive(): assert r("bootstrap_intervals.csv").rom_ci_low.gt(0).all()
def test_lobo_positive():
 x=r("leave_one_build_out.csv");assert x.risk_increment.gt(0).all() and x.safe_rom_ndc_tax.gt(0).all()
def test_lobo_count(): assert r("leave_one_build_out.csv").groupby("dataset").size().eq(24).all()
def test_top1pct_deletion_positive():
 x=r("contribution_deletion.csv");assert x.risk_increment.gt(0).all() and x.safe_rom_ndc_tax.gt(0).all()
def test_no_raw_nonmonotonicity_hidden(): assert r("endpoint_audit.csv").raw_nonmonotone_rate.eq(0).all()
def test_cross_implementation_positive():
 x=r("cross_implementation_comparison.csv");assert x[["incremental_transport_risk","hnswlib_risk_increment","safe_rom_ndc_tax","hnswlib_rom_ndc_tax"]].gt(0).all().all()
def test_all_gates(): assert r("gate_table.csv").mechanism_gate.all()
def test_manifest_scope_and_sealed_access():
 m=json.loads((ROOT/"manifests/graph_anns_faiss_external_validity_decision.json").read_text());assert m["scope_label"]=="REGISTERED_HNSW_IMPLEMENTATIONS" and not m["validation_dev_accessed"] and not m["formal_test_accessed"] and not m["future_replication_vectors_accessed"] and not m["hdf5_test_member_accessed"]
def test_ten_figure_pairs():
 p=ROOT/"figures/graph_anns_faiss_external_validity";assert len(list(p.glob("*.png")))==10 and len(list(p.glob("*.pdf")))==10
