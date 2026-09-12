#!/usr/bin/env python
"""P11-BF: build-farm population study — the first population-level view of rebuild
transport risk. Two arms on a 10K base (SIFT):
  ARM A (registered style): 100 builds, single-thread, random seed + random order
  ARM B (deployment style): 100 builds, 8-thread, random order, no seed control
     (parallel-scheduling nondeterminism included, as in real serving fleets)
Per build: search 500 fresh queries (hdf5 test, seed 991, disjoint from base —
forensics-gated) over the registered grid; record hit counts.
Metrics: population histogram of directed-pair incremental risk; P(random directed pair
exceeds the 2% gate); per-target mean-risk distribution; conformal validity at k=9,
alpha=0.10 (realized vs nominal); rank-uniformity KS statistic (exchangeability check);
arm A vs arm B comparison (scheduling-noise contribution).
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
N_BASE = 10_000
N_Q = 500
N_FARMS = 100


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def rh(a):
    b = np.ascontiguousarray(a, dtype="<f4").view(np.uint8).reshape(len(a), -1)
    return {hashlib.sha256(r.tobytes()).hexdigest() for r in b}


def main():
    t0 = time.time()
    with h5py.File(HDF5, "r") as f:
        base = np.ascontiguousarray(f["train"][:N_BASE], dtype=np.float32)
        test = f["test"][:]
    rng = np.random.RandomState(991)
    queries = np.ascontiguousarray(test[rng.choice(len(test), N_Q, replace=False)],
                                   dtype=np.float32)
    assert len(rh(queries) & rh(base)) == 0, "forensics gate failed"
    log(f"farm: base {base.shape}, queries {queries.shape}, overlap=0")

    # exact truth once (base fixed across all builds)
    b2 = (base ** 2).sum(1)
    truth = []
    for s in range(0, N_Q, 128):
        q = queries[s:s + 128]
        d = b2[None, :] - 2 * (q @ base.T)
        truth.append(np.argpartition(d, 10, axis=1)[:, :10])
    truth = np.vstack(truth)
    log("truth done")

    def run_arm(arm, n, threads):
        Hm = np.zeros((n, N_Q, len(GRID)), dtype=np.int8)
        for bi in range(n):
            seed = 10_000 + bi
            o = np.random.RandomState(seed).permutation(N_BASE)
            p = hnswlib.Index(space="l2", dim=base.shape[1])
            p.init_index(max_elements=N_BASE, ef_construction=100, random_seed=seed)
            p.set_num_threads(threads)
            p.add_items(base[o], o.astype(np.int64))
            for gi, ef in enumerate(GRID):
                p.set_ef(ef)
                labels, _ = p.knn_query(queries, k=10)
                Hm[bi, :, gi] = [len(set(l.tolist()) & set(tr.tolist()))
                                 for l, tr in zip(labels, truth)]
            if (bi + 1) % 25 == 0:
                log(f"arm {arm}: {bi+1}/{n} builds "
                    f"({(time.time()-t0)/60:.1f} min elapsed)")
            del p
        return Hm

    log("ARM A: 100 single-thread registered-style builds")
    HA = run_arm("A", N_FARMS, threads=1)
    log("ARM B: 100 8-thread deployment-style builds")
    HB = run_arm("B", N_FARMS, threads=8)
    np.savez_compressed(OUT / "build_farm_hits.npz", HA=HA, HB=HB, grid=GRID)

    # ---- population analysis ----
    def population(Hm, arm):
        n = Hm.shape[0]
        ok = Hm >= H
        Bm = np.where(ok.any(axis=2), GRID[np.argmax(ok, axis=2)], -1).astype(float)
        pairs = []
        for t in range(n):
            hv_t = Hm[t]  # RAW hit counts (0..10); boolean matrix was a bug
            for s in range(n):
                if s == t:
                    continue
                a = np.where(Bm[s] < 0, GRID[-1], Bm[s])
                j = np.clip(np.searchsorted(GRID, a), 0, len(GRID) - 1)
                z = (hv_t[np.arange(N_Q), j] < H).astype(float)
                # incremental: minus target-bottom reference
                bt = Bm[t]
                jr = np.clip(np.searchsorted(GRID, np.where(bt < 0, GRID[-1], bt)), 0, len(GRID) - 1)
                zref = (hv_t[np.arange(N_Q), jr] < H).astype(float)
                pairs.append((z - zref).mean())
        pairs = np.array(pairs)
        # conformal validity at k=9, alpha=0.10
        rng2 = np.random.RandomState(991)
        fails, tot, draws = 0.0, 0.0, 40
        for _ in range(draws):
            perm = rng2.permutation(n)
            t, pool = perm[0], perm[1:10]
            hv_t = (Hm[t] >= H)
            m = int(np.ceil(0.9 * 10))
            live = np.ones(N_Q, dtype=bool)
            a = np.full(N_Q, np.nan)
            for q in range(N_Q):
                vals = Bm[pool, q]
                fin = vals[vals >= 0]
                if len(fin) >= m:
                    a[q] = np.sort(fin)[m - 1]
                else:
                    live[q] = False
            dep = np.where(np.isnan(a), GRID[-1], a)
            j = np.clip(np.searchsorted(GRID, dep), 0, len(GRID) - 1)
            z = (Hm[t][np.arange(N_Q), j] < H).astype(float)  # raw counts
            fails += float(z[live].sum()); tot += float(live.sum())
        # rank-uniformity KS: rank of held-out build's B among pool+target per query
        from scipy import stats as st
        perms = [rng2.permutation(n) for _ in range(30)]
        ks_stats = []
        for perm in perms:
            t, pool = perm[0], perm[1:10]
            ranks = []
            Bt = Bm[t]
            for q in range(N_Q):
                vals = np.r_[Bm[pool, q], Bt[q]]
                fin = vals[vals >= 0]
                if len(fin) < 5 or Bt[q] < 0:
                    continue
                # randomized tie-breaking: rank = 1 + #{others strictly greater} + U#{ties}
                others = fin[fin != fin.max()] if False else None
                gt = (fin > Bt[q]).sum()
                tie = (fin == Bt[q]).sum()
                rk = (gt + rng2.randint(1, tie + 1)) / len(fin)
                ranks.append(rk)
            if len(ranks) > 30:
                ks_stats.append(st.kstest(ranks, "uniform").statistic)
        return {
            "arm": arm, "n_builds": n,
            "pair_risk_mean": float(pairs.mean()),
            "pair_risk_p95": float(np.percentile(pairs, 95)),
            "pair_risk_max": float(pairs.max()),
            "frac_pairs_above_2pct": float((pairs > 0.02).mean()),
            "frac_pairs_above_5pct": float((pairs > 0.05).mean()),
            "conformal_k9_alpha010_realized": float(fails / tot),
            "ks_median": float(np.median(ks_stats)) if ks_stats else None,
        }, pairs

    sa, pa = population(HA, "A_single_thread_registered")
    sb, pb = population(HB, "B_deployment_8thread")
    summary = {"A": sa, "B": sb, "grid": GRID.tolist(), "H": H, "n_q": N_Q}
    (OUT / "build_farm_summary.json").write_text(json.dumps(summary, indent=2))
    np.save(OUT / "build_farm_pair_risks.npy", np.vstack([pa, pb]))
    log(f"FARM DONE in {(time.time()-t0)/60:.1f} min")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
