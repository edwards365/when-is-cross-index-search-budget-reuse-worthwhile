"""P2 deterministic checks. Run:
LD_LIBRARY_PATH=/home/wlk/miniconda3/lib PYTHONPATH=scripts/graph_anns_phase2/p2 \
  .venv/bin/python tests/graph_anns_phase2_p2/test_p2.py
"""
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "graph_anns_phase2_p2"
checks = []
def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")

# ---- max-over-source
summ = pd.read_csv(OUT / "max_over_source_summary.csv")
check("four_cells", len(summ) == 4)
hn = summ[summ.implementation == "hnswlib"]
fa = summ[summ.implementation == "faiss"]
check("mos_risk_far_below_2pct", (summ["mean_risk_abstain_variant"] < 0.02).all())
check("mos_beats_naive_by_10x", (summ["mean_risk_abstain_variant"] * 10 <
                                 pd.to_numeric(summ["mean_naive_over_sources"], errors="coerce")).all())
check("naive_matches_registered_main_results",
      abs(float(hn[hn.dataset == "sift_100k"]["mean_naive_over_sources"].iloc[0]) - 0.2237) < 0.001 and
      abs(float(hn[hn.dataset == "arxiv_nomic_100k"]["mean_naive_over_sources"].iloc[0]) - 0.1838) < 0.001 and
      abs(float(fa[fa.dataset == "sift_100k"]["mean_naive_over_sources"].iloc[0]) - 0.2367) < 0.001 and
      abs(float(fa[fa.dataset == "arxiv_nomic_100k"]["mean_naive_over_sources"].iloc[0]) - 0.1793) < 0.001)
check("distcomp_estimable_only_hnswlib",
      pd.to_numeric(hn["mean_distcomp_abstain_variant"], errors="coerce").notna().all() and
      (fa["mean_distcomp_abstain_variant"].astype(str) == "NOT_ESTIMABLE").all())
hn_dc = pd.to_numeric(hn["mean_distcomp_abstain_variant"], errors="coerce")
check("distcomp_between_1_and_2", ((hn_dc > 1.0) & (hn_dc < 2.0)).all())
check("loo_risk_all_below_5pct",
      summ["loo_risk_max"].max() < 0.05)

ks = pd.read_csv(OUT / "max_over_k_sources.csv")
check("k_curve_monotone_decreasing",
      all(g.sort_values("k_sources")["mean_risk"].is_monotonic_decreasing
          for _, g in ks.groupby(["dataset", "implementation"])))
check("k1_matches_naive",
      (abs(ks[ks.k_sources == 1]["mean_risk"].values -
           summ["mean_naive_over_sources"].values) < 0.02).all())

# ---- six-method table
for ds in ("sift_100k", "arxiv_nomic_100k"):
    t = pd.read_csv(OUT / f"six_method_table_{ds}.csv")
    check(f"{ds}_24_targets", len(t) == 24)
    check(f"{ds}_M4_never_certifies", (~t["M4_certified"]).all())
    check(f"{ds}_M4b_screen_then_fail", (~t["M4b_certified"]).all() and (t["M4b_chosen_ef"].notna() | (t["M4b_fail_reason"] == "NO_FEASIBLE_ACTION_ON_SELECTION")).all())
    check(f"{ds}_M2_dominates_M5_risk", (t["M2_overall_unsafe_execution"] <= t["M5_max_action_risk"] + 1e-12).all())
    check(f"{ds}_M2_much_cheaper_than_M5", (t["M2_distcomp"] < 0.5 * t["M5_distcomp"]).all())
    check(f"{ds}_oracle_risk_equals_endpoint_mass",
          (abs(t["M6_oracle_risk"] - t["M6_infeasible_rate"]) < 1e-9).all())
    check(f"{ds}_M3_certify_prob_range",
          (t["M3_certify_prob"] >= 0).all() and (t["M3_certify_prob"] <= 1).all())

# ---- five-condition table
s = json.loads((OUT / "five_condition_summary.json").read_text())
check("48_targets", s["targets"] == 48)
check("zero_complete_instances", s["complete_positive_instances"] == 0)
check("margin_is_first_failure", s["first_failed_condition_counts"] == {"c3_margin": 48})

man = json.loads((OUT / "decision_manifest.json").read_text())
check("manifest_label", man["final_label"] == "P2_CONSTRUCTIVE_TABLE_MARGIN_FAILS_POOLING_WINS")

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
