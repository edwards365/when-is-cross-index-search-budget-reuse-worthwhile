#!/usr/bin/env python
"""P2/B3: Theorem-2 five-condition instance table. For each of the 48 hnswlib targets,
mark each condition SATISFIED/FAILED with the evidence value, using (a) the P2 six-method
replay outputs and (b) the stored per-target CP audit (graph_anns_e4_reanalysis/
per_target_cp_audit.csv, full-750 evidence) and deployment decisions
(graph_anns_e4_hotfix/deployment_decision_corrected.csv) as cross-references.

Conditions (paper Theorem 2):
 (i) endpoint feasibility: exists action with risk <= delta - 2*gamma
(ii) action-relevant identifiability on the registered class
(iii) positive margin for a USEFUL (non-max-cost) action
(iv) independent target evidence (selection/certification/evaluation role disjointness)
 (v) valid fallback or abstention
A COMPLETE positive instance requires all five; otherwise the first failed condition is
reported. Output: results/graph_anns_phase2_p2/five_condition_instances.csv
"""
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p2"

DELTA = 0.05


def main():
    cp = pd.read_csv(REPO / "results/graph_anns_e4_reanalysis/per_target_cp_audit.csv")
    dep = pd.read_csv(REPO / "results/graph_anns_e4_hotfix/deployment_decision_corrected.csv")
    rows = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        t = pd.read_csv(OUT / f"six_method_table_{dataset}.csv")
        for _, r in t.iterrows():
            tb = r["target"]
            cprow = cp[(cp["dataset"] == dataset) & (cp["target_build"] == tb)]
            deprow = dep[(dep["dataset"] == dataset) & (dep["target_build"] == tb)]
            max_risk = r["M5_max_action_risk"]
            gamma = 0.01
            c1 = "SATISFIED" if max_risk <= DELTA - 2 * gamma else "FAILED"
            c1_ev = f"max-action risk {max_risk:.4f} vs delta-2gamma {DELTA-2*gamma:.2f}"
            # (ii) identifiability: stored simultaneous Bonferroni-48 certification exists
            c2_ev = (f"per-target CP ucb {float(cprow['cp_ucb_95'].iloc[0]):.4f}, "
                     f"Bonferroni-48 {float(cprow['cp_ucb_bonferroni_48'].iloc[0]):.4f}")
            c2 = "SATISFIED" if bool(cprow["per_target_certified"].iloc[0]) else "PARTIAL"
            # (iii) margin for a useful action: M4/M4b outcomes on the 6-action grid
            if r["M4b_certified"]:
                c3, c3_ev = "SATISFIED", f"cert-aware screening certified ef={r['M4b_chosen_ef']}"
            elif r["M4b_abstain"]:
                c3 = "FAILED"
                c3_ev = ("certification-aware screening found no action with CP-UB <= "
                         "P0(94)=0.0073 threshold; min-cost screened actions sit inside the "
                         "margin band (M4a zero-failure violations)")
            else:
                c3 = "FAILED"
                c3_ev = f"zero-failure certification violated ({r['M4_fail_reason']})"
            # (iv) independent evidence: role split 375/94/281 disjoint by construction
            c4, c4_ev = "SATISFIED", "selection/certification/evaluation roles disjoint (375/94/281, seed 991)"
            # (v) fallback: stored deployment decision on the same target
            if len(deprow):
                dv = deprow["deploy_decision"].iloc[0]
                c5_ev = f"stored decision: {dv}"
                c5 = "SATISFIED" if dv in ("DEPLOY_CERTIFIED_CANDIDATE", "ABSTAIN_NO_CERTIFIED_ACTION",
                                           "DEPLOY_CERTIFIED_FALLBACK") else "PARTIAL"
            else:
                c5, c5_ev = "PARTIAL", "no stored decision row"
            conds = {"c1_feasibility": (c1, c1_ev), "c2_identifiability": (c2, c2_ev),
                     "c3_margin": (c3, c3_ev), "c4_independent_evidence": (c4, c4_ev),
                     "c5_fallback": (c5, c5_ev)}
            first_fail = next((k for k, (st, _) in conds.items() if st == "FAILED"), None)
            complete = all(st != "FAILED" for st, _ in conds.values()) and \
                not any(st == "PARTIAL" for st, _ in conds.values())
            row = {"dataset": dataset, "target": tb,
                   **{k: f"{st}" for k, (st, _) in conds.items()},
                   **{k + "_evidence": ev for k, (_, ev) in conds.items()},
                   "complete_positive_instance": complete,
                   "first_failed_condition": first_fail or "NONE"}
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "five_condition_instances.csv", index=False)
    summary = {
        "targets": len(df),
        "complete_positive_instances": int(df["complete_positive_instance"].sum()),
        "first_failed_condition_counts": df["first_failed_condition"].value_counts().to_dict(),
        "verdict": ("NO_COMPLETE_POSITIVE_INSTANCE_ON_REGISTERED_GRID" 
                    if df["complete_positive_instance"].sum() == 0 else "POSITIVE_INSTANCES_EXIST"),
    }
    (OUT / "five_condition_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
