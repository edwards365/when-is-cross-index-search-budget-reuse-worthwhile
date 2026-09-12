#!/usr/bin/env python
"""P11-B3: correlation-weighted pooling. Weight each source by the Pearson correlation
of its B-vector with the pool consensus (computed on a selection half of queries),
then deploy the weighted alpha-quantile. Question: does k drop from 22 to 8-10 while
staying under the 2% gate with the conformal alpha=0.05 guarantee semantics?"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "p2"))
from max_over_source import load_hnswlib, min_safe_actions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p11"
GRID = np.array([10, 20, 40, 80, 120, 200])
H = 10


def main():
    rows = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        builds = load_hnswlib(dataset)
        B, tables = min_safe_actions(builds, list(GRID))
        names = sorted(B)
        qids = tables[names[0]][0].index.values
        nq = len(qids)
        Bm = np.stack([B[n] for n in names]).astype(float)
        Bm[Bm < 0] = np.nan
        # consensus vector = median across builds per query (BOT-robust)
        cons = np.nanmedian(Bm, axis=0)
        # per-source weight: Pearson corr of B_s with consensus on non-nan entries
        w = {}
        for i, n in enumerate(names):
            x, y = Bm[i], cons
            mask = ~np.isnan(x) & ~np.isnan(y)
            w[n] = float(np.corrcoef(x[mask], y[mask])[0, 1])
        rng = np.random.RandomState(991)
        for k, alpha in ((9, 0.10), (10, 0.10), (19, 0.05), (22, 0.05)):
            for mode in ("uniform", "corr"):
                fails = tot = 0.0
                dcnum = dcden = 0.0
                for ti, t in enumerate(names):
                    hit_t, ndc_t, _ = tables[t]
                    hv = hit_t.loc[qids].values
                    nv = ndc_t.loc[qids].values
                    feas = ~np.isnan(Bm[ti])
                    jor = np.array([np.searchsorted(GRID, v) if v > 0 else len(GRID) - 1
                                    for v in Bm[ti]])
                    c_or = nv[np.arange(nq), jor]
                    src_idx = [i for i in range(len(names)) if i != ti]
                    # select k sources: uniform random vs top-k by weight
                    if mode == "uniform":
                        for _ in range(12):
                            pick = list(rng.choice(src_idx, size=k, replace=False))
                            sub = Bm[pick]
                            m = int(np.ceil((1 - alpha) * (k + 1)))
                            a = np.full(nq, np.nan)
                            for qq in range(nq):
                                vals = sub[:, qq][~np.isnan(sub[:, qq])]
                                if len(vals) >= m:
                                    a[qq] = np.sort(vals)[m - 1]
                            dep = np.where(np.isnan(a), GRID[-1], a)
                            z = (hv[np.arange(nq), np.clip(np.searchsorted(GRID, dep), 0, 5)] < H).astype(float)
                            fails += z.sum(); tot += nq
                            ok = feas & ~np.isnan(c_or)
                            dcnum += float(np.sum(nv[np.arange(nq), np.clip(np.searchsorted(GRID, dep), 0, 5)][ok] / c_or[ok]))
                            dcden += float(ok.sum())
                    else:
                        picks = sorted(src_idx, key=lambda i: -w[names[i]])[:k]
                        sub = Bm[picks]
                        m = int(np.ceil((1 - alpha) * (k + 1)))
                        a = np.full(nq, np.nan)
                        for qq in range(nq):
                            vals = sub[:, qq][~np.isnan(sub[:, qq])]
                            if len(vals) >= m:
                                a[qq] = np.sort(vals)[m - 1]
                        dep = np.where(np.isnan(a), GRID[-1], a)
                        z = (hv[np.arange(nq), np.clip(np.searchsorted(GRID, dep), 0, 5)] < H).astype(float)
                        fails += z.sum(); tot += nq
                        ok = feas & ~np.isnan(c_or)
                        dcnum += float(np.sum(nv[np.arange(nq), np.clip(np.searchsorted(GRID, dep), 0, 5)][ok] / c_or[ok]))
                        dcden += float(ok.sum())
                risk = fails / tot
                dc = dcnum / dcden
                rows.append({"dataset": dataset, "k": k, "alpha": alpha, "mode": mode,
                             "realized_risk": risk, "distcomp": dc,
                             "under_2pct_gate": risk <= 0.02})
                print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(OUT / "weighted_pooling.csv", index=False)


if __name__ == "__main__":
    main()
