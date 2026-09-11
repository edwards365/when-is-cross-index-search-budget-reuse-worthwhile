#!/usr/bin/env python
"""P3: D0C/D1/D2/D3 deterministic-contract ablation from frozen artifacts.

Chain design (each adjacent pair differs in exactly one factor, descriptive only):
  D0C: random order, 8 threads, random seeds        (3 builds/dataset)
  D1 : canonical order, 8 threads, random seeds     (6)  [D0C->D1: order pinned]
  D2 : canonical order, 8 threads, fixed seed 991   (6)  [D1->D2: seed pinned]
  D3 : canonical order, 1 thread,  fixed seed 991   (3)  [D2->D3: threads pinned to 1]
Outputs: results/graph_anns_phase2_p3/{contract_ablation.csv, chain_marginal_effects.csv,
tier_identity.csv}
"""
import json
from pathlib import Path

import pandas as pd

SCRATCH = Path("/home/wlk/data500/graph_anns_iclr_phase1_scratch/phase1c")
D0C_DIR = Path("/home/wlk/data500/graph_anns_iclr_phase1_1_scratch/d0_control")
REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p3"
OUT.mkdir(parents=True, exist_ok=True)

TIER_DEF = {
    "D0C": "random order; 8 threads; random seeds",
    "D1": "canonical order; 8 threads; random seeds",
    "D2": "canonical order; 8 threads; fixed seed 991",
    "D3": "canonical order; 1 thread; fixed seed 991",
}


def tier_build_dirs(ds, tier):
    if tier == "D0C":
        return sorted((D0C_DIR / ds).glob("*seed*"))
    return sorted((SCRATCH / ds / tier).glob("*__seed*"))


def main():
    s3 = pd.read_csv(REPO / "results/graph_anns_iclr_phase1_1/deterministic_semantic_reanalysis.csv")
    rows, marg_rows, ident_rows = [], [], []
    for ds in ("sift_100k", "arxiv_nomic_100k"):
        d0 = s3[s3.dataset == ds].set_index("regime")
        for tier in ("D0C", "D1", "D2", "D3"):
            hashes, walls = [], []
            for b in tier_build_dirs(ds, tier):
                cj = b / "COMPLETE.json"
                if cj.exists():
                    d = json.loads(cj.read_text())
                    hashes.append(d["index_sha256"])
                    walls.append(d["build_wall_seconds"])
            r = d0.loc[tier]
            rows.append({
                "dataset": ds, "regime": tier, "tier_definition": TIER_DEF[tier],
                "builds": int(r["builds"]), "ordered_pairs": int(r["ordered_pairs"]),
                "min_safe_action_variation": float(r["minimum_safe_action_variation"]),
                "endpoint_state_variation": float(r["endpoint_state_variation"]),
                "mean_budget_diameter": float(r["mean_budget_diameter"]),
                "p95_budget_diameter": float(r["p95_budget_diameter"]),
                "recall_at_max_action": float(r["recall_at_max_action"]),
                "build_time_median_frozen_s": float(r["build_time_median_seconds"]),
                "build_time_wall_mean_s": sum(walls) / len(walls) if walls else None,
                "n_index_hashes": len(set(hashes)),
                "byte_identical_within_tier": (len(set(hashes)) == 1 if hashes else
                                               ("N/A_RANDOM_SEEDS_BY_DESIGN" if tier == "D0C" else None)),
            })
        b = {r["regime"]: r for r in rows if r["dataset"] == ds}
        for name, lo, hi in [("order_pinning_D0C_to_D1", "D0C", "D1"),
                             ("seed_pinning_D1_to_D2", "D1", "D2"),
                             ("single_threading_D2_to_D3", "D2", "D3")]:
            marg_rows.append({
                "dataset": ds, "chain_step": name,
                "variation_before": b[lo]["min_safe_action_variation"],
                "variation_after": b[hi]["min_safe_action_variation"],
                "variation_change": b[hi]["min_safe_action_variation"] - b[lo]["min_safe_action_variation"],
                "build_time_ratio_vs_prev": b[hi]["build_time_median_frozen_s"] / b[lo]["build_time_median_frozen_s"],
            })
    for r in rows:
        ident_rows.append({"dataset": r["dataset"], "regime": r["regime"],
                           "n_builds_registered": r["builds"],
                           "n_index_hashes_seen": r["n_index_hashes"],
                           "byte_identical": r["byte_identical_within_tier"]})
    pd.DataFrame(rows).to_csv(OUT / "contract_ablation.csv", index=False)
    pd.DataFrame(marg_rows).to_csv(OUT / "chain_marginal_effects.csv", index=False)
    pd.DataFrame(ident_rows).to_csv(OUT / "tier_identity.csv", index=False)
    print(pd.DataFrame(rows)[["dataset", "regime", "min_safe_action_variation",
                              "build_time_median_frozen_s", "byte_identical_within_tier"]].to_string(index=False))
    print()
    print(pd.DataFrame(marg_rows).to_string(index=False))


if __name__ == "__main__":
    main()
