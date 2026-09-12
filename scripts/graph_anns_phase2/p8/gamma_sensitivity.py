#!/usr/bin/env python
"""P8-B: gamma-sensitivity of the Theorem-2 margin audit (reviewer Q4).
For each target, on the same frozen 375-query selection block (seed 991, role split
identical to P2), ask: does ANY non-maximal action satisfy point risk <= delta-2*gamma?
Count pass targets for gamma in {0.005, 0.01, 0.02}. Also recompute the zero-failure
certification outcome for the gamma-optimal screened action to show certification
still fails/independently of gamma."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "p2"))
from max_over_source import load_hnswlib, min_safe_actions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p8"
H, DELTA = 10, 0.05
SEL_N = 375


def main():
    rows = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        builds = load_hnswlib(dataset)
        GRID=[10,20,40,80,120,200]
        B, tables = min_safe_actions(builds, GRID)
        names = sorted(B)
        qids = tables[names[0]][0].index.values
        rng = np.random.RandomState(991)
        perm = rng.permutation(len(qids))
        sel = perm[:SEL_N]
        for gamma in (0.005, 0.01, 0.02):
            thr = DELTA - 2 * gamma
            pass_t = 0
            for t in names:
                hit, _, ef_idx = tables[t]
                hv_sel = hit.loc[qids].values[sel]
                risks = (hv_sel < H).mean(axis=0)
                nonmax = risks[:-1]  # exclude max registered action (ef=200)
                if (nonmax <= thr).any():
                    pass_t += 1
            rows.append({"dataset": dataset, "gamma": gamma, "threshold": thr,
                         "targets_with_margin_passing_nonmax_action": pass_t,
                         "total_targets": len(names)})
            print(rows[-1])
    pd.DataFrame(rows).to_csv(OUT / "gamma_sensitivity.csv", index=False)


if __name__ == "__main__":
    main()
