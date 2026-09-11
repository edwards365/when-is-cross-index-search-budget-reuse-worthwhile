#!/usr/bin/env python
"""P5: verify every number quoted in paper_revision_patch.md against the P2-P4 artifacts.
Exit nonzero on any mismatch."""
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RES = REPO / "results"
checks = []


def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")


summ = pd.read_csv(RES / "graph_anns_phase2_p2/max_over_source_summary.csv")
hn = summ[summ.implementation == "hnswlib"]
check("pooling risk < 1%", (summ["mean_risk_abstain_variant"] < 0.01).all())
check("distcomp 1.34-1.45", abs(hn["mean_distcomp_abstain_variant"].astype(float).mean() - 1.397) < 0.06)

t = {ds: pd.read_csv(RES / f"graph_anns_phase2_p2/six_method_table_{ds}.csv")
     for ds in ("sift_100k", "arxiv_nomic_100k")}
check("M1 21.89/18.06",
      abs(t["sift_100k"].M1_naive_k1_risk.mean() - 0.2189) < 5e-4 and
      abs(t["arxiv_nomic_100k"].M1_naive_k1_risk.mean() - 0.1806) < 5e-4)
check("M2 overall 0.18/0.08 incl abstention",
      abs(t["sift_100k"].M2_overall_unsafe_execution.mean() * 100 - 0.18) < 0.05 and
      abs(t["arxiv_nomic_100k"].M2_overall_unsafe_execution.mean() * 100 - 0.08) < 0.05)
check("abstention 2.38/2.67",
      abs(t["sift_100k"].M2_maxsource_abstain_rate.mean() * 100 - 2.38) < 0.05 and
      abs(t["arxiv_nomic_100k"].M2_maxsource_abstain_rate.mean() * 100 - 2.67) < 0.05)
check("M3 certify 70.8/37.5",
      abs(t["sift_100k"].M3_certified.mean() * 100 - 70.8) < 0.1 and
      abs(t["arxiv_nomic_100k"].M3_certified.mean() * 100 - 37.5) < 0.1)
check("M4/M4b zero certify", (t["sift_100k"].M4_certified.mean() == 0 and
                              t["arxiv_nomic_100k"].M4_certified.mean() == 0 and
                              t["sift_100k"].M4b_certified.mean() == 0 and
                              t["arxiv_nomic_100k"].M4b_certified.mean() == 0))
m4b = pd.concat([t[ds].M4b_chosen_ef.dropna() for ds in t])
check("M4b ef 120 x8 / 200 x16 per dataset",
      all((g == 120).sum() == 8 and (g == 200).sum() == 16 for _, g in
          pd.concat([t[ds][["dataset", "M4b_chosen_ef"]].dropna() for ds in t])
          .groupby("dataset")["M4b_chosen_ef"]))
check("M5 0.80/1.26 at 4.09/5.14x",
      abs(t["sift_100k"].M5_max_action_risk.mean() * 100 - 0.80) < 0.05 and
      abs(t["arxiv_nomic_100k"].M5_max_action_risk.mean() * 100 - 1.26) < 0.05 and
      abs(t["sift_100k"].M5_distcomp.mean() - 4.09) < 0.02 and
      abs(t["arxiv_nomic_100k"].M5_distcomp.mean() - 5.14) < 0.02)

fc = pd.read_csv(RES / "graph_anns_phase2_p3/contract_ablation.csv").set_index(["dataset", "regime"])
check("ablation 68.3->34.1 / 63.2->30.8",
      abs(fc.loc[("sift_100k", "D0C"), "min_safe_action_variation"] * 100 - 68.3) < 0.1 and
      abs(fc.loc[("sift_100k", "D1"), "min_safe_action_variation"] * 100 - 34.1) < 0.1 and
      abs(fc.loc[("arxiv_nomic_100k", "D0C"), "min_safe_action_variation"] * 100 - 63.2) < 0.1 and
      abs(fc.loc[("arxiv_nomic_100k", "D1"), "min_safe_action_variation"] * 100 - 30.8) < 0.1)
me = pd.read_csv(RES / "graph_anns_phase2_p3/chain_marginal_effects.csv").set_index(["dataset", "chain_step"])
check("chain ratios 0.80/0.93, 4.73/1.86",
      abs(me.loc[("sift_100k", "order_pinning_D0C_to_D1"), "build_time_ratio_vs_prev"] - 0.80) < 0.01 and
      abs(me.loc[("arxiv_nomic_100k", "order_pinning_D0C_to_D1"), "build_time_ratio_vs_prev"] - 0.93) < 0.01 and
      abs(me.loc[("sift_100k", "single_threading_D2_to_D3"), "build_time_ratio_vs_prev"] - 4.73) < 0.01 and
      abs(me.loc[("arxiv_nomic_100k", "single_threading_D2_to_D3"), "build_time_ratio_vs_prev"] - 1.86) < 0.01)

gs = pd.read_csv(RES / "graph_anns_phase2_p4/grid_sensitivity.csv")
check("grid range 10.3-23.8", gs.mean_family_transport_risk.min() > 0.102 and
      gs.mean_family_transport_risk.max() < 0.239)

em = pd.read_csv(RES / "graph_anns_phase2_p4/economics_matrix.csv")
check("matrix 36 cells", len(em) == 36)

fcv = pd.read_csv(RES / "graph_anns_phase2_p2/five_condition_summary.json")
import json
fcv = json.loads((RES / "graph_anns_phase2_p2/five_condition_summary.json").read_text())
check("48 targets margin fails", fcv["targets"] == 48 and
      fcv["first_failed_condition_counts"] == {"c3_margin": 48})

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} number-traceability checks passed")
if failed:
    raise SystemExit(1)
