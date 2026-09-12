#!/usr/bin/env python
"""P8-A: quality-threshold sensitivity (h in {8,9,10}) for the cells lacking registered
h-rows: clean Faiss-100K and the preregistered SIFT-1M cell. hnswlib-100K rows already
exist in the frozen S1 table and are quoted, not recomputed.
Metric: mean single-source transport risk over all directed pairs (family summary,
same estimator family as P4 grid sensitivity)."""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "p4"))
from grid_sensitivity import load_hnswlib, load_faiss, family_risk  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p8"

rows = []
# clean Faiss-100K
for ds in ("sift_100k", "arxiv_nomic_100k"):
    builds = load_faiss(ds)
    for H in (8, 9, 10):
        r = family_risk(builds, [16, 32, 64, 128, 256, 512], H=H)
        rows.append({"cell": "faiss_clean_100k", "dataset": ds, "h": H,
                     "family_transport_risk": r})
        print(rows[-1])
# SIFT-1M (per-query hit counts from the preregistered run)
per = pd.read_csv(REPO / "results/graph_anns_phase2_p6/sift1m_perquery.csv")
GRID = np.array([10, 20, 40, 80, 120, 200])
B, hits = {}, {}
for b, g in per.groupby("build"):
    piv = g.pivot(index="query_id", columns="ef", values="hit_count")[GRID]
    hits[b] = piv
for H in (8, 9, 10):
    B = {}
    for name, piv in hits.items():
        ok = piv.values >= H
        B[name] = np.where(ok.any(axis=1), GRID[np.argmax(ok, axis=1)], -1)
    names = sorted(B)
    nq = len(hits[names[0]])
    tot = 0.0
    for t in names:
        hv = hits[t].values
        for s in names:
            if s == t:
                continue
            a = np.where(B[s] < 0, GRID[-1], B[s])
            j = np.clip(np.searchsorted(GRID, a), 0, 5)
            tot += (hv[np.arange(nq), j] < H).mean()
    r = tot / (len(names) * (len(names) - 1))
    rows.append({"cell": "sift1m", "dataset": "sift_1m", "h": H,
                 "family_transport_risk": r})
    print(rows[-1])
pd.DataFrame(rows).to_csv(OUT / "h_sensitivity.csv", index=False)
mn = min(r["family_transport_risk"] for r in rows)
print(f"\nMINIMUM risk across h=8/9/10 and all cells: {mn:.4f} "
      f"(2% materiality gate: {'ABOVE - phenomenon robust' if mn > 0.02 else 'BELOW'})")
