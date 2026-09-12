#!/usr/bin/env python
"""P11-B: decisive online head-to-head on fresh (cold) queries.

Rebuilds the 24 registered E4 hnswlib builds on SIFT-100K; fresh workload = 500
SIFT-1M test queries (seed 991; disjoint from every registered role; forensics-gated).
Stores per-(build,query,ef) hit counts and per-query latency, then evaluates policies.
"""
import hashlib
import json
import time
from pathlib import Path

import h5py
import numpy as np
import hnswlib

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p11"
TMP = Path("/home/wlk/data500/graph_anns_phase2_p11")
TMP.mkdir(parents=True, exist_ok=True)
HDF5 = REPO / "data/raw/sift-128-euclidean.hdf5"
GRID = np.array([10, 20, 40, 80, 120, 200])
H = 10
SEEDS = [83, 97, 109, 127, 149, 163, 181, 197]
ORDERS = ["random", "lid_ascending", "lid_descending"]
EFC = 100
FRESH_N = 500


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def rh(a):
    b = np.ascontiguousarray(a, dtype="<f4").view(np.uint8).reshape(len(a), -1)
    return {hashlib.sha256(r.tobytes()).hexdigest() for r in b}


def top10_exact(queries, base):
    b2 = (base ** 2).sum(1)
    out = []
    for s in range(0, len(queries), 128):
        q = queries[s:s + 128]
        d = b2[None, :] - 2 * (q @ base.T)
        out.append(np.argpartition(d, 10, axis=1)[:, :10])
    return np.vstack(out)


def main():
    t0 = time.time()
    with h5py.File(HDF5, "r") as f:
        base = f["train"][:100000]
        test = f["test"][:]
    rng = np.random.RandomState(991)
    fresh = np.ascontiguousarray(test[rng.choice(len(test), FRESH_N, replace=False)],
                                 dtype=np.float32)
    assert len(rh(fresh) & rh(base)) == 0, "forensics gate failed"
    log(f"forensics PASS; base {base.shape}; fresh {fresh.shape}")
    truth = top10_exact(fresh, base)

    norms = np.linalg.norm(base, axis=1)
    ORD = {"random": lambda sd: np.random.RandomState(sd).permutation(len(base)),
           "lid_ascending": np.argsort(norms, kind="stable"),
           "lid_descending": np.argsort(-norms, kind="stable")}

    hits_by, lat_by, build_s = {}, {}, {}
    idx = 0
    for seed in SEEDS:
        for oname in ORDERS:
            o = ORD[oname](seed) if oname == "random" else ORD[oname]
            t = time.time()
            p = hnswlib.Index(space="l2", dim=base.shape[1])
            p.init_index(max_elements=len(base), ef_construction=EFC, random_seed=seed)
            p.set_num_threads(1)
            p.add_items(base[o], o.astype(np.int64))
            build_s[f"sift100k__seed{seed}__{oname}"] = time.time() - t
            Hm = np.zeros((FRESH_N, len(GRID)), dtype=int)
            Lm = np.zeros((FRESH_N, len(GRID)))
            for gi, ef in enumerate(GRID):
                p.set_ef(ef)
                labels, _ = p.knn_query(fresh, k=10)
                hits = np.array([len(set(l.tolist()) & set(tr.tolist()))
                                 for l, tr in zip(labels, truth)])
                Hm[:, gi] = hits
                t = time.time()
                p.knn_query(fresh, k=10)
                Lm[:, gi] = (time.time() - t) / FRESH_N * 1e9
            tag = f"sift100k__seed{seed}__{oname}"
            hits_by[tag], lat_by[tag] = Hm, Lm
            idx += 1
            log(f"build {idx}/24 {tag}: {build_s[tag]:.1f}s hits@ef200={Hm[:,5].mean():.3f}")
            del p

    names = sorted(hits_by)
    qidx = np.arange(FRESH_N)
    np.savez_compressed(OUT / "online_fresh_records.npz",
                        names=json.dumps(names), hits=np.stack([hits_by[n] for n in names]),
                        lat=np.stack([lat_by[n] for n in names]),
                        build_seconds=json.dumps(build_s))
    rows = []
    for ti, t in enumerate(names):
        Hv = hits_by[t]
        Lv = lat_by[t]
        src_H = np.stack([hits_by[n] for n in names if n != t])  # (23, nq, 6)
        # B_s per source: first ef with hits>=10
        okS = src_H >= H
        Bs = np.where(okS.any(axis=2), GRID[np.argmax(okS, axis=2)], -1)  # (23, nq)
        okT = Hv >= H
        Bt = np.where(okT.any(axis=1), GRID[np.argmax(okT, axis=1)], -1)
        feasT = okT.any(axis=1)
        any_bot = (~okS).any(axis=0).any(axis=1) if False else (Bs < 0).any(axis=0)

        def lat_at(a):
            j = np.clip(np.searchsorted(GRID, a), 0, len(GRID) - 1)
            return Lv[np.arange(FRESH_N), j]

        def risk(a):
            return float(z_at(a, Hv).mean())

        def z_at(a, hv):
            j = np.clip(np.searchsorted(GRID, a), 0, len(GRID) - 1)
            return (hv[np.arange(FRESH_N), j] < H).astype(float)

        # M1: random single source (mean over draws), risk on target
        m1 = []
        for _ in range(10):
            s = src_H[rng.randint(0, len(src_H))]
            oks = s >= H
            Bs1 = np.where(oks.any(axis=1), GRID[np.argmax(oks, axis=1)], GRID[-1])
            m1.append(z_at(Bs1.astype(float), Hv).mean())
        m1_risk = float(np.mean(m1))

        a2 = np.where(any_bot, GRID[-1], np.nanmax(np.where(Bs < 0, np.nan, Bs), axis=0))
        z2 = z_at(a2.astype(float), Hv)
        m2_dep = float(z2[~any_bot].mean())
        m2_all = float(z2.mean())
        l2v = lat_at(a2.astype(float))

        m3_pass = []
        fail_at_max = Hv[:, -1] < H
        for _ in range(100):
            draw = rng.choice(FRESH_N, 59, replace=False)
            m3_pass.append(fail_at_max[draw].sum() == 0)

        a5 = np.full(FRESH_N, GRID[-1])
        m5_risk = risk(a5)
        l5 = lat_at(a5)

        a6 = np.where(feasT, Bt, GRID[-1])
        m6_risk = risk(a6)
        l6 = lat_at(a6)

        def dc(a):
            j = np.clip(np.searchsorted(GRID, a), 0, len(GRID) - 1)
            c = Lv[np.arange(FRESH_N), j]
            ok = feasT
            return float(np.mean(c[ok] / l6[ok]))

        rows.append({
            "target": t,
            "M1_naive_risk": m1_risk,
            "M2_risk_deployable": m2_dep, "M2_overall_risk": m2_all,
            "M2_abstain_rate": float(any_bot.mean()),
            "M2_distcomp": dc(a2.astype(float)),
            "M2_p95_lat_us": float(np.percentile(l2v, 95)) / 1e3,
            "M2_p99_lat_us": float(np.percentile(l2v, 99)) / 1e3,
            "M3_cert_pass_prob": float(np.mean(m3_pass)),
            "M5_risk": m5_risk, "M5_distcomp": dc(a5),
            "M5_p95_lat_us": float(np.percentile(l5, 95)) / 1e3,
            "M6_risk": m6_risk,
            "M6_infeasible_rate": float((~feasT).mean()),
            "source_searches_per_cold_query": 23,
            "source_labeling_cost_per_build_s": round(500 * 6 * (lat_by[t][:, 0].mean() / 1e9) + 0.05, 4),
        })
        print(rows[-1], flush=True)

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "online_head_to_head.csv", index=False)
    meta = {"build_seconds": build_s, "wall": time.time() - t0,
            "fresh_n": FRESH_N, "forensics": "PASS"}
    (OUT / "online_head_to_head_meta.json").write_text(json.dumps(meta, indent=2))
    log(f"DONE in {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
