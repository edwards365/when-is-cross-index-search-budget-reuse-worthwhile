#!/usr/bin/env python
"""P11-A5: no-truth budget rule. Deployment scenario: exact truth is unavailable, so the
operator cannot measure Recall@10; the only observable is the search-cost curve across
ef (visited nodes / queue pushes / latency per ef). Rule under test: pick the smallest
ef whose visited-node growth into the NEXT ef is below theta (queue saturation proxy of
graph convergence). Sweep theta; report the rule's realized incremental risk and mean
DistComp vs the per-query oracle. If the rule is unsafe (risk >> delta) while expensive,
'profile without truth' is exposed as having hidden risk."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "p2"))
from max_over_source import load_hnswlib, min_safe_actions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
DATA500 = Path("/home/wlk/data500")
OUT = REPO / "results" / "graph_anns_phase2_p11"
GRID = np.array([10, 20, 40, 80, 120, 200])
H = 10
VIS_CAP = 4000.0


def visited_curve(raw_dir_name_seed, dataset, qids):
    """visited_nodes per (query, ef) for one build."""
    import gzip
    bdir = DATA500 / "graph_anns_e4" / "raw" / raw_dir_name_seed
    with gzip.open(bdir / "queries.csv.gz", "rt") as f:
        df = pd.read_csv(f)
    df = df[df["query_id"].isin(qids) & (df["latency_round"] == 0)]
    df = df.drop_duplicates(subset=["query_id", "ef_search"])
    return df.pivot(index="query_id", columns="ef_search", values="visited_nodes")[list(GRID)]


def main():
    out = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        builds = load_hnswlib(dataset)
        B, tables = min_safe_actions(builds, list(GRID))
        names = sorted(B)
        qids = tables[names[0]][0].index.values
        nq = len(qids)
        Bmat = np.stack([B[n] for n in names]).astype(float)
        Bmat[Bmat < 0] = np.nan
        for ti, t in enumerate(names):
            hit_t, ndc_t, _ = tables[t]
            hv = hit_t.loc[qids].values
            nv = ndc_t.loc[qids].values
            vis = visited_curve(t, dataset, qids).values
            vis = np.minimum(vis, VIS_CAP)
            feas = ~np.isnan(Bmat[ti])
            # oracle cost
            jor = np.array([np.searchsorted(GRID, v) if v > 0 else len(GRID) - 1
                            for v in Bmat[ti]])
            c_or = nv[np.arange(nq), jor]

            def risk_cost(a):
                j = np.clip(np.searchsorted(GRID, a), 0, len(GRID) - 1)
                z = (hv[np.arange(nq), j] < H).astype(float)
                c = nv[np.arange(nq), j]
                ok = feas & ~np.isnan(c_or)
                return float(z.mean()), float(np.mean(c[ok] / c_or[ok]))

            for theta in (1.02, 1.05, 1.10, 1.25):
                growth = np.ones((nq, len(GRID)))
                growth[:, :-1] = vis[:, 1:] / np.maximum(vis[:, :-1], 1)
                pick = (growth <= theta).argmax(axis=1)
                a = GRID[pick]
                r, c = risk_cost(a.astype(float))
                out.append({"dataset": dataset, "target": t, "theta": theta,
                            "rule": "visited_saturation",
                            "chosen_mean_ef": float(a.mean()),
                            "realized_risk": r, "distcomp_vs_oracle": c})
            # reference points
            for nm, a in (("max_action", np.full(nq, GRID[-1])),
                          ("oracle", np.where(feas, Bmat[ti], GRID[-1]))):
                r, c = risk_cost(a.astype(float))
                out.append({"dataset": dataset, "target": t, "theta": nm,
                            "rule": "reference", "chosen_mean_ef": float(np.nanmean(a)),
                            "realized_risk": r, "distcomp_vs_oracle": c})
        g = pd.DataFrame([x for x in out if x["dataset"] == dataset])
        print(dataset)
        print(g[g.target == names[0]].round(3).to_string(index=False))
    pd.DataFrame(out).to_csv(OUT / "no_truth_rule.csv", index=False)


if __name__ == "__main__":
    main()
