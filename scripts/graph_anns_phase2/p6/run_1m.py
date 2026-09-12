#!/usr/bin/env python
"""P6-A: SIFT-1M registered cell. Executes the committed preregistration exactly.
Storage protocol: build -> search -> sha256 -> delete index (15GB disk budget).
"""
import csv
import hashlib
import pandas as pd
import json
import os
import time
from pathlib import Path

import h5py
import numpy as np
import hnswlib

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p6"
TMP = Path("/home/wlk/data500/graph_anns_phase2_p6")
TMP.mkdir(parents=True, exist_ok=True)
LOG = OUT / "run_1m.log"
GRID = [10, 20, 40, 80, 120, 200]
EVAL_N = 500
SEEDS = [13, 83, 197, 2029]
ORDERS = ["random_order", "lid_ascending_by_norm"]
M, EFC = 16, 100


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)  # stdout is nohup-redirected to the same log


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def row_hashes(a):
    b = np.ascontiguousarray(a, dtype="<f4").view(np.uint8).reshape(len(a), -1)
    return {hashlib.sha256(r.tobytes()).hexdigest() for r in b}


def order_indices(n, kind, seed):
    rs = np.random.RandomState(seed)
    if kind == "random_order":
        return rs.permutation(n)
    if kind == "lid_ascending_by_norm":
        return None  # computed once from base norms by caller
    raise ValueError(kind)


def main():
    t0 = time.time()
    log("P6-A SIFT-1M run start")
    with h5py.File(REPO / "data/raw/sift-128-euclidean.hdf5", "r") as f:
        base = f["train"][:]
        test_q = f["test"][:]
        truth = f["neighbors"][:]
    log(f"base {base.shape} test {test_q.shape} truth {truth.shape}")

    rng = np.random.RandomState(991)
    eval_ids = np.sort(rng.choice(len(test_q), EVAL_N, replace=False))
    q = np.ascontiguousarray(test_q[eval_ids], dtype=np.float32)
    q_truth = truth[eval_ids][:, :10]  # first 10 neighbors

    # forensics gate: query/base raw-content overlap must be 0
    t = time.time()
    q_hashes = row_hashes(q)
    base_hashes = row_hashes(base)
    overlap = len(q_hashes & base_hashes)
    log(f"forensics: query/base raw overlap = {overlap} (computed in {time.time()-t:.0f}s)")
    assert overlap == 0, "CLEAN-FORENSICS GATE FAILED - halting per preregistration"

    # shared structures
    norms = np.linalg.norm(base, axis=1)
    lid_idx = np.argsort(norms, kind="stable")
    dim = base.shape[1]

    builds = [(s, o) for s in SEEDS for o in ORDERS]
    results = []
    identity_hashes = []
    perbuild_csv = OUT / "sift1m_perbuild.csv"
    done = set()
    if perbuild_csv.exists() and perbuild_csv.stat().st_size > 0:
        prev = pd.read_csv(perbuild_csv)
        done = set(prev["build"].unique())
        log(f"resuming: {len(done)} builds already recorded: {sorted(done)}")
    for bi, (seed, order) in enumerate(builds):
        if f"sift1m__seed{seed}__{order}" in done:
            log(f"skip build seed={seed} order={order} (already recorded)")
            continue
        if order == "random_order":
            idx_order = order_indices(len(base), order, seed)
        else:
            idx_order = lid_idx
        t = time.time()
        p = hnswlib.Index(space="l2", dim=dim)
        p.init_index(max_elements=len(base), ef_construction=EFC, random_seed=seed)
        p.set_num_threads(1)
        p.add_items(base[idx_order], idx_order.astype(np.int64))
        build_s = time.time() - t
        ip = TMP / f"idx_{bi}.bin"
        p.save_index(str(ip))
        isha = sha256_file(ip)
        p.set_ef(200)  # search-time ef set per query below
        rows = []
        for ef in GRID:
            p.set_ef(ef)
            t = time.time()
            labels, _ = p.knn_query(q, k=10)
            lat = (time.time() - t) / len(q)
            hits = np.array([len(set(l.tolist()) & set(tr.tolist()))
                             for l, tr in zip(labels, q_truth)])
            for qi in range(EVAL_N):
                rows.append((qi, ef, int(hits[qi]), lat * 1e9))
        bname = f"sift1m__seed{seed}__{order}"
        results.append({"build": bname, "seed": seed,
                        "order": order, "index_sha256": isha,
                        "build_seconds": build_s, "rows": rows})
        with open(perbuild_csv, "a", newline="") as f:
            w = csv.writer(f)
            if not perbuild_csv.exists() or perbuild_csv.stat().st_size == 0:
                w.writerow(["build", "seed", "order", "index_sha256",
                            "query_id", "ef", "hit_count", "latency_ns_per_query"])
            for row in rows:
                w.writerow([bname, seed, order, isha, row[0], row[1], row[2], row[3]])
        mh200 = np.mean([r[2] for r in rows if r[1] == 200])
        log(f"build {bi+1}/8 seed={seed} order={order}: {build_s:.0f}s, "
            f"sha={isha[:12]}, mean hits@ef200={mh200:.3f}")
        assert mh200 > 9.5, f"SANITY GATE FAILED: mean hits@ef200={mh200}"
        ip.unlink()
        del p

    # identity check: seed 13 random_order twice
    id_hashes = []
    for rep in (1, 2):
        idx_order = order_indices(len(base), "random_order", 13)
        t = time.time()
        p = hnswlib.Index(space="l2", dim=dim)
        p.init_index(max_elements=len(base), ef_construction=EFC, random_seed=13)
        p.set_num_threads(1)
        p.add_items(base[idx_order], idx_order.astype(np.int64))
        build_s = time.time() - t
        ip = TMP / f"idx_id{rep}.bin"
        p.save_index(str(ip))
        isha = sha256_file(ip)
        id_hashes.append(isha)
        log(f"identity rep {rep}: {build_s:.0f}s sha={isha[:12]}")
        ip.unlink()
        del p

    # consolidate: perquery view from the incremental per-build store (all builds ever done)
    perbuild_csv = OUT / "sift1m_perbuild.csv"
    pb = (pd.read_csv(perbuild_csv) if perbuild_csv.exists()
          and perbuild_csv.stat().st_size > 0 else pd.DataFrame())
    pb.to_csv(OUT / "sift1m_perquery.csv", index=False)
    meta = {
        "eval_ids": eval_ids.tolist(),
        "forensics_query_base_raw_overlap": overlap,
        "builds": (pb[["build", "seed", "order", "index_sha256"]]
                   .drop_duplicates("build").to_dict("records")),
        "identity_check_hashes": id_hashes,
        "identity_byte_identical": id_hashes[0] == id_hashes[1],
        "wall_total_seconds": time.time() - t0,
    }
    (OUT / "sift1m_run_meta.json").write_text(json.dumps(meta, indent=2))
    log(f"ALL DONE in {(time.time()-t0)/60:.1f} min; identity_equal={id_hashes[0]==id_hashes[1]}")


if __name__ == "__main__":
    main()
