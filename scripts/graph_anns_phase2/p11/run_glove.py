#!/usr/bin/env python
"""P11: GloVe-100 compact cell (third dataset, angular geometry, 1.19M scale).
Mirrors P10 design exactly per preregistration; resumable; delete-as-you-go."""
import csv
import hashlib
import json
import time
from pathlib import Path

import h5py
import numpy as np
import hnswlib

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results/graph_anns_phase2_p11"
TMP = Path("/home/wlk/data500/graph_anns_phase2_p11")
TMP.mkdir(parents=True, exist_ok=True)
HDF5 = REPO / "data/raw/glove-100-angular.hdf5"
LOG = OUT / "run_glove.log"
GRID = np.array([10, 20, 40, 80, 120, 200])
H = 10
SEEDS = [13, 83, 197, 2029]
ORDERS = ["random_order", "lid_ascending_by_norm"]


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def rh(a):
    b = np.ascontiguousarray(a, dtype="<f4").view(np.uint8).reshape(len(a), -1)
    return {hashlib.sha256(r.tobytes()).hexdigest() for r in b}


def main():
    t0 = time.time()
    with h5py.File(HDF5, "r") as f:
        base = np.ascontiguousarray(f["train"][:], dtype=np.float32)
        test = f["test"][:]
        truth = f["neighbors"][:]
    log(f"base {base.shape} test {test.shape} truth {truth.shape}")

    rng = np.random.RandomState(991)
    eval_ids = np.sort(rng.choice(len(test), 500, replace=False))
    q = np.ascontiguousarray(test[eval_ids], dtype=np.float32)
    q_truth = truth[eval_ids][:, :10]

    overlap = len(rh(q) & rh(base))
    log(f"forensics: query/base overlap = {overlap}")
    assert overlap == 0

    norms = np.linalg.norm(base, axis=1)
    lid = np.argsort(norms, kind="stable")
    perbuild = OUT / "glove_perbuild.csv"
    done = set()
    if perbuild.exists() and perbuild.stat().st_size > 0:
        done = set(pd_read_builds())
        log(f"resuming: {sorted(done)}")

    def pd_read_builds():
        import pandas as pd
        return pd.read_csv(perbuild)["build"].unique().tolist()

    for bi, (seed, kind) in enumerate([(s, o) for s in SEEDS for o in ORDERS]):
        tag = f"glove100__seed{seed}__{kind}"
        if tag in done:
            log(f"skip {tag}")
            continue
        o = (np.random.RandomState(seed).permutation(len(base))
             if kind == "random_order" else lid)
        t = time.time()
        p = hnswlib.Index(space="cosine", dim=base.shape[1])
        p.init_index(max_elements=len(base), ef_construction=100, random_seed=seed)
        p.set_num_threads(1)
        SL = 1_000_000
        for st in range(0, len(base), SL):
            sl = o[st:st + SL]
            p.add_items(base[sl], sl.astype(np.int64))
        build_s = time.time() - t
        for gi, ef in enumerate(GRID):
            p.set_ef(ef)
            labels, _ = p.knn_query(q, k=10)
            hits = np.array([len(set(l.tolist()) & set(tr.tolist()))
                             for l, tr in zip(labels, q_truth)])
            new = not perbuild.exists() or perbuild.stat().st_size == 0
            with open(perbuild, "a", newline="") as fc:
                w = csv.writer(fc)
                if new:
                    w.writerow(["build", "seed", "order", "ef", "query_id", "hit_count"])
                for qi in range(len(q)):
                    w.writerow([tag, seed, kind, ef, qi, int(hits[qi])])
        log(f"build {bi+1}/8 {tag}: {build_s:.0f}s hits@ef200={hits.mean():.3f}")
        assert hits.mean() > 8.5, f"SANITY FAIL {hits.mean()}"
        del p

    log(f"builds done in {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
