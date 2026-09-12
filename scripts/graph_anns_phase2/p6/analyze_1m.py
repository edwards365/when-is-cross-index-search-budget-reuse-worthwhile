#!/usr/bin/env python
"""P6-A analysis: transport risk, variation, pooling k-curve, profiling cost at SIFT-1M.
Pure post-processing of sift1m_perquery.csv (preregistered metrics only)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p6"
H = 10
GRID = np.array([10, 20, 40, 80, 120, 200])


def main():
    df = pd.read_csv(OUT / "sift1m_perquery.csv")
    meta = json.loads((OUT / "sift1m_run_meta.json").read_text())
    B = {}
    hit_by = {}
    for b, g in df.groupby("build"):
        piv = g.pivot(index="query_id", columns="ef", values="hit_count")
        piv = piv[GRID]
        ok = piv.values >= H
        B[b] = pd.Series(np.where(ok.any(axis=1), GRID[np.argmax(ok, axis=1)], -1),
                         index=piv.index)
        hit_by[b] = piv
    names = sorted(B)
    qids = B[names[0]].index.values
    Bm = np.stack([B[n].loc[qids].values for n in names]).astype(float)

    # variation
    fin = Bm >= 0
    n_finite = fin.sum(axis=0)
    v_fin = float(((n_finite > 0) & (n_finite > 1)).mean())
    end_state = ~fin  # is-BOT per build
    endpoint_var = float(((end_state.sum(axis=0) > 0) & (end_state.sum(axis=0) < len(names))).mean())
    unresolved = float((end_state.sum(axis=0) == len(names)).mean())

    # transport risk: mean over 8x7 directed pairs
    risks = []
    ref_risks = []
    ref_events = []
    for ti, t in enumerate(names):
        hits_t = hit_by[t].loc[qids].values
        tgt = Bm[ti]
        j_or = np.clip(np.searchsorted(GRID, np.where(tgt > 0, tgt, GRID[-1])), 0, 5)
        z_ref = (hits_t[np.arange(len(qids)), j_or] < H).astype(float)
        ref_risks.append(z_ref.mean())
        ref_events.append(z_ref)
        for si in range(len(names)):
            if si == ti:
                continue
            a = np.where(Bm[si] < 0, GRID[-1], Bm[si])
            j = np.clip(np.searchsorted(GRID, a), 0, 5)
            risks.append((hits_t[np.arange(len(qids)), j] < H).astype(float).mean())
    abs_risk = float(np.mean(risks))
    inc_risk = abs_risk - float(np.mean(ref_risks))
    # bootstrap CI over queries (recompute mean pair risk per query bootstrap)
    pair_mat = []
    for ti, t in enumerate(names):
        hits_t = hit_by[t].loc[qids].values
        for si in range(len(names)):
            if si == ti:
                continue
            a = np.where(Bm[si] < 0, GRID[-1], Bm[si])
            j = np.clip(np.searchsorted(GRID, a), 0, 5)
            pair_mat.append((hits_t[np.arange(len(qids)), j] < H).astype(float))
    pair_mat = np.stack(pair_mat)
    ref_mat = np.stack(ref_events)  # (8, nq) target reference events
    rng = np.random.RandomState(991)
    idx = rng.randint(0, len(qids), size=(5000, len(qids)))
    abs_boots = pair_mat[:, idx].mean(axis=1).mean(axis=0)
    ref_boots = ref_mat[:, idx].mean(axis=1).mean(axis=0)
    inc_boots = abs_boots - ref_boots
    ci = [float(np.percentile(inc_boots, 2.5)), float(np.percentile(inc_boots, 97.5))]
    ci_abs = [float(np.percentile(abs_boots, 2.5)), float(np.percentile(abs_boots, 97.5))]

    # pooling k-curve
    pool = []
    for k in range(1, 8):
        rs = []
        for ti, t in enumerate(names):
            hits_t = hit_by[t].loc[qids].values
            src_idx = [i for i in range(len(names)) if i != ti]
            for _ in range(50):
                pick = rng.choice(src_idx, size=min(k, len(src_idx)), replace=False)
                src = Bm[pick]
                any_bot = np.isnan(src).any(axis=0)
                a = np.where(any_bot, GRID[-1], np.nanmax(src, axis=0))
                j = np.clip(np.searchsorted(GRID, a), 0, 5)
                rs.append((hits_t[np.arange(len(qids)), j] < H).astype(float).mean())
        pool.append({"k_sources": k, "mean_risk": float(np.mean(rs)),
                     "risk_p95": float(np.percentile(rs, 95))})
    pool_df = pd.DataFrame(pool)
    pool_df.to_csv(OUT / "sift1m_pooling_curve.csv", index=False)

    # naive k=1 == mean single-source risk
    naive = abs_risk
    summary = {
        "dataset_scale": "SIFT-1M",
        "builds": len(names),
        "forensics_query_base_raw_overlap": meta["forensics_query_base_raw_overlap"],
        "finite_action_variation": v_fin,
        "endpoint_variation": endpoint_var,
        "unresolved_mass": unresolved,
        "absolute_transport_risk": abs_risk,
        "incremental_transport_risk": inc_risk,
        "bootstrap_ci": ci,
        "bootstrap_ci_absolute": ci_abs,
        "build_seconds_median": float(np.median(meta.get("per_build_seconds", [float("nan")]))) ,
        "identity_byte_identical": meta["identity_byte_identical"],
        "pooling": pool,
        "naive_k1_risk": naive,
    }
    (OUT / "sift1m_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
