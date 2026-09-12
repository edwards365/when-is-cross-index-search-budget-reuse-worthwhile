#!/usr/bin/env python
"""P8-E: quantile pooling (reviewer Q3) — instead of max over k sources, deploy the
q-th order statistic of the source min-safe actions (q in {0.5, 0.75, 0.9, 1.0=max}).
Risk vs conservatism tradeoff, k in {3,5,10,22}, 50 draws, seed 991, hnswlib cells."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "p2"))
from max_over_source import load_hnswlib, min_safe_actions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p8"
GRID = np.array([10, 20, 40, 80, 120, 200])
H = 10


def main():
    rows = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        builds = load_hnswlib(dataset)
        B, tables = min_safe_actions(builds, list(GRID))
        names = sorted(B)
        qids = tables[names[0]][0].index.values
        Bmat = np.stack([B[n] for n in names]).astype(float)
        Bmat[Bmat < 0] = np.nan
        rng = np.random.RandomState(991)
        for k in (3, 10, 22):
            for q in (0.5, 0.9, 1.0):
                risks, cons = [], []
                for ti, t in enumerate(names):
                    hit_t, _, _ = tables[t]
                    hv = hit_t.loc[qids].values
                    src_idx = [i for i in range(len(names)) if i != ti]
                    for _ in range(10):
                        pick = rng.choice(src_idx, size=min(k, len(src_idx)), replace=False)
                        src = Bmat[pick]
                        any_bot = np.isnan(src).any(axis=0)
                        a = np.where(any_bot, GRID[-1], np.nanquantile(src, q, axis=0))
                        a = GRID[np.clip(np.searchsorted(GRID, a), 0, 5)]
                        j = np.clip(np.searchsorted(GRID, a), 0, 5)
                        z = (hv[np.arange(len(qids)), j] < H).astype(float)
                        risks.append(z.mean())
                        tgt = Bmat[ti]
                        feas = ~np.isnan(tgt)
                        cons.append(float(np.mean(a[feas] > tgt[feas])))
                rows.append({"dataset": dataset, "k": k, "quantile": q,
                             "mean_risk": float(np.mean(risks)),
                             "mean_conservative_rate": float(np.mean(cons))})
                print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(OUT / "quantile_pooling.csv", index=False)


if __name__ == "__main__":
    main()
