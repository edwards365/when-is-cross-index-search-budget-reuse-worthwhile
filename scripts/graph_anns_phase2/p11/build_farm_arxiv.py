#!/usr/bin/env python
"""P11-BF2: Arxiv-Nomic-10K farm — second-dataset exchangeability + population check."""
import hashlib, json, time
from pathlib import Path
import h5py, numpy as np, hnswlib
from scipy import stats as st

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results/graph_anns_phase2_p11"
HDF5 = REPO / "data/raw/arxiv-nomic-768-normalized.hdf5"
GRID = np.array([10, 20, 40, 80, 120, 200]); H = 10
N_BASE = 10_000; N_Q = 500; N_FARMS = 100

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def rh(a):
    b = np.ascontiguousarray(a, dtype="<f4").view(np.uint8).reshape(len(a), -1)
    return {hashlib.sha256(r.tobytes()).hexdigest() for r in b}

def main():
    t0 = time.time()
    with h5py.File(HDF5, "r") as f:
        base = np.ascontiguousarray(f["train"][:N_BASE], dtype=np.float32)
        test = f["test"][:]
        truth = f["neighbors"][:]
    rng = np.random.RandomState(991)
    queries = np.ascontiguousarray(test[rng.choice(len(test), N_Q, replace=False)], dtype=np.float32)
    assert len(rh(queries) & rh(base)) == 0, "forensics gate failed"
    log(f"farm: base {base.shape}, queries {queries.shape}, overlap=0")

    b2 = (base ** 2).sum(1)
    truth_t10 = []
    for s in range(0, N_Q, 128):
        q = queries[s:s+128]
        d = b2[None,:] - 2*(q@base.T)
        truth_t10.append(np.argpartition(d, 10, axis=1)[:, :10])
    truth_t10 = np.vstack(truth_t10)

    def run_arm(arm, n, threads):
        Hm = np.zeros((n, N_Q, len(GRID)), dtype=np.int8)
        for bi in range(n):
            seed = 20_000 + bi
            o = np.random.RandomState(seed).permutation(N_BASE)
            p = hnswlib.Index(space="cosine", dim=base.shape[1])
            p.init_index(max_elements=N_BASE, ef_construction=100, random_seed=seed)
            p.set_num_threads(threads)
            p.add_items(base[o], o.astype(np.int64))
            for gi, ef in enumerate(GRID):
                p.set_ef(ef)
                labels, _ = p.knn_query(queries, k=10)
                Hm[bi,:,gi] = [len(set(l.tolist())&set(tr.tolist()))
                               for l,tr in zip(labels, truth_t10)]
            if (bi+1) % 25 == 0: log(f"arm {arm}: {bi+1}/{n}")
            del p
        return Hm

    log("ARM A: 100 single-thread")
    HA = run_arm("A", N_FARMS, threads=1)
    log("ARM B: 100 8-thread deployment-style")
    HB = run_arm("B", N_FARMS, threads=8)
    np.savez_compressed(OUT / "arxiv_farm_hits.npz", HA=HA, HB=HB, grid=GRID)

    # population analysis
    def population(Hm, arm):
        n = Hm.shape[0]
        ok = Hm >= H
        Bm = np.where(ok.any(axis=2), GRID[np.argmax(ok, axis=2)], -1).astype(float)
        pairs = []
        for t in range(n):
            hv_t = Hm[t]
            for s in range(n):
                if s == t: continue
                a = np.where(Bm[s] < 0, GRID[-1], Bm[s])
                j = np.clip(np.searchsorted(GRID, a), 0, len(GRID)-1)
                z = (hv_t[np.arange(N_Q), j] < H).astype(float)
                bt = Bm[t]
                jr = np.clip(np.searchsorted(GRID, np.where(bt<0,GRID[-1],bt)), 0, len(GRID)-1)
                zref = (hv_t[np.arange(N_Q), jr] < H).astype(float)
                pairs.append((z-zref).mean())
        pairs = np.array(pairs)
        rng2 = np.random.RandomState(991)
        fails = tot = draws = 0
        ks_stats = []
        for _ in range(40):
            perm = rng2.permutation(n)
            t, pool = perm[0], perm[1:10]
            hv_t = (Hm[t] >= H)
            live = np.ones(N_Q, dtype=bool)
            a = np.full(N_Q, np.nan)
            Bt = Bm[t]
            for q in range(N_Q):
                vals = Bm[pool, q]
                fin = vals[vals >= 0]
                if len(fin) >= 9:
                    a[q] = np.sort(fin)[8]
                else:
                    live[q] = False
            dep = np.where(np.isnan(a), GRID[-1], a)
            j = np.clip(np.searchsorted(GRID, dep), 0, len(GRID)-1)
            z = (hv_t[np.arange(N_Q), j] < H).astype(float)
            fails += float(z[live].sum()); tot += float(live.sum()); draws += 1
            ranks = []
            Bt_q = Bm[t]
            for q in range(N_Q):
                vals = np.r_[Bm[pool, q], Bt[q]]
                fin = vals[vals >= 0]
                if len(fin) < 5 or Bt[q] < 0: continue
                gt = (fin > Bt[q]).sum()
                tie = (fin == Bt[q]).sum()
                ranks.append((gt + rng2.randint(1, tie+1)) / len(fin))
            if len(ranks) > 30:
                ks_stats.append(st.kstest(ranks, "uniform").statistic)
        return {"arm": arm, "n_builds": n,
                "pair_risk_mean": round(float(pairs.mean()), 4),
                "pair_risk_p95": round(float(np.percentile(pairs, 95)), 4),
                "pair_risk_max": round(float(pairs.max()), 4),
                "frac_above_2pct": round(float((pairs > 0.02).mean()), 4),
                "conformal_k9_alpha010_realized": round(float(fails/tot), 4),
                "ks_median": round(float(np.median(ks_stats)), 4) if ks_stats else None}

    from scipy import stats as st
    sa = population(HA, "A_single_thread")
    sb = population(HB, "B_8thread")
    summary = {"A": sa, "B": sb, "grid": GRID.tolist(), "H": H, "n_q": N_Q,
               "dataset": "Arxiv-Nomic-100 angular (10K farm)"}
    (OUT / "arxiv_farm_summary.json").write_text(json.dumps(summary, indent=2))
    log(f"FARM DONE in {(time.time()-t0)/60:.1f} min")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
