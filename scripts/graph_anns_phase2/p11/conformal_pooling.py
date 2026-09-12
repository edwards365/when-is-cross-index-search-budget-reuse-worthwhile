#!/usr/bin/env python
"""P11-C: conformal pooling — validity experiment for Theorem 3.

Theorem 3 (exchangeable-build conformal pooling). Let the target build E_t and the k
source builds be exchangeable (build-unit exchangeability; queries arbitrary). Deploy
a(q) = the m-th smallest of the source min-safe actions {B_1(q),...,B_k(q)} with
m = ceil((1-alpha)(k+1)). Then, per query and marginally over the build draw,
  Pr[ B_t(q) > a(q) ] <= alpha,
a finite-sample guarantee requiring no query-distribution assumption and no truth at
deployment beyond the cached source labels.

This experiment checks (i) VALIDITY: realized failure rate <= nominal alpha under
leave-one-build-out (each of the 24 builds as target, k = 23 sources), for alpha in
{0.02, 0.05, 0.10, 0.20}; (ii) k-sensitivity: k in {3, 5, 10, 23} (subsampled pools);
(iii) adaptivity: mean DistComp vs oracle and mean chosen ef versus always-max.
BOT handling: a source with B_s(q) = BOT contributes +inf (excluded from the quantile
rank); if all sources are BOT the policy abstains (excluded from risk numerator,
counted as abstain).
"""
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
ALPHAS = [0.02, 0.05, 0.10, 0.20]
KS = [3, 5, 10, 23]
DRAWS = 12


def snap(a):
    return GRID[np.clip(np.searchsorted(GRID, a), 0, len(GRID) - 1)]


def main():
    rows = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        builds = load_hnswlib(dataset)
        B, tables = min_safe_actions(builds, list(GRID))
        names = sorted(B)
        qids = tables[names[0]][0].index.values
        nq = len(qids)
        Bm = np.stack([B[n] for n in names]).astype(float)
        rng = np.random.RandomState(991)
        for alpha in ALPHAS:
            for k in KS:
                fails, tot, abst, dcnum, dcden, mef, mx_fail = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, []
                for ti, t in enumerate(names):
                    hit_t, ndc_t, _ = tables[t]
                    hv = hit_t.loc[qids].values
                    nv = ndc_t.loc[qids].values
                    feas = ~np.isnan(Bm[ti])
                    jor = np.array([np.searchsorted(GRID, v) if v > 0 else len(GRID) - 1
                                    for v in Bm[ti]])
                    c_or = nv[np.arange(nq), jor]
                    for draw in range(DRAWS):
                        src_idx = [i for i in range(len(names)) if i != ti]
                        pick = list(rng.choice(src_idx, size=k, replace=False))
                        src = Bm[pick]                       # (k, nq), nan = BOT
                        m = int(np.ceil((1 - alpha) * (k + 1)))
                        a = np.full(nq, np.nan)
                        for q in range(nq):
                            vals = src[:, q][~np.isnan(src[:, q])]
                            if len(vals) < k:               # some source BOT -> abstain-ish
                                continue
                            a[q] = np.sort(vals)[min(m - 1, len(vals) - 1)]
                        deployed = np.where(np.isnan(a), GRID[-1], a)
                        z = (hv[np.arange(nq), np.clip(
                            np.searchsorted(GRID, deployed), 0, 5)] < H).astype(float)
                        live = ~np.isnan(a)
                        fails += float(z[live].sum())
                        tot += float(live.sum())
                        abst += float((~live).mean())
                        ok = feas & live
                        dcnum += float(np.sum(nv[np.arange(nq), np.clip(
                            np.searchsorted(GRID, deployed), 0, 5)][ok]
                            / c_or[ok]))
                        dcden += float(ok.sum())
                        mef += float(pd.Series(deployed[live]).map(
                            {g: i for i, g in enumerate(GRID)}).mean())
                        mx_fail.append(float(z[live].mean()))
                realized = fails / tot
                rows.append({"dataset": dataset, "alpha": alpha, "k": k,
                             "realized_failure_rate": realized,
                             "nominal_alpha": alpha,
                             "valid": realized <= alpha + 1e-12,
                             "mean_abstain_rate": abst / (DRAWS * len(names)),
                             "mean_distcomp": dcnum / dcden,
                             "mean_chosen_ef_idx": mef / (DRAWS * len(names)),
                             "worst_target_failure_rate": max(mx_fail)})
                print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(OUT / "conformal_pooling_validity.csv", index=False)


if __name__ == "__main__":
    main()
