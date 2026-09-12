#!/usr/bin/env python
"""P10: 10M-scale cell on ann-benchmarks deep-image-96-angular. Executes the committed
preregistration exactly. Resumable per-build CSV; storage protocol deletes each index
after its searches are recorded."""
import csv
import gzip
import hashlib
import json
import time
from pathlib import Path

import h5py
import numpy as np
import hnswlib

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p10"
TMP = Path("/home/wlk/data500/graph_anns_phase2_p10")
TMP.mkdir(parents=True, exist_ok=True)
H5 = REPO / "data" / "raw" / "deep-image-96-angular.hdf5"
URL = "https://ann-benchmarks.com/deep-image-96-angular.hdf5"
LOG = OUT / "run_10m.log"
GRID = [10, 20, 40, 80, 120, 200]
EVAL_N = 500
SEEDS = [13, 83, 197, 2029]
ORDERS = ["random_order", "lid_ascending_by_norm"]
M, EFC = 16, 100
MIN_FREE_GB = 3.0


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


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


def free_gb():
    return 15.0  # replaced below with os.statvfs


def free_gb_real(path="/home/wlk"):
    import shutil
    return shutil.disk_usage(path).free / 2**30


def ensure_data():
    if H5.exists() and H5.stat().st_size == 3848008288:
        log("hdf5 present with expected size")
        return
    log(f"downloading {URL} (3.85GB)...")
    import subprocess
    r = subprocess.run(["curl", "-s", "-o", str(H5), URL])
    assert r.returncode == 0 and H5.stat().st_size == 3848008288, "download failed"
    log("download complete")


def main():
    t0 = time.time()
    ensure_data()
    with h5py.File(H5, "r") as f:
        base = f["train"][:]
        test_q = f["test"][:]
        truth = f["neighbors"][:]
    log(f"base {base.shape} test {test_q.shape} truth {truth.shape}")
    sha = sha256_file(H5)
    pre = json.loads((OUT / "preregistration.json").read_text())
    pre["dataset"]["sha256"] = sha
    (OUT / "preregistration.json").write_text(json.dumps(pre, indent=2))

    rng = np.random.RandomState(991)
    eval_ids = np.sort(rng.choice(len(test_q), EVAL_N, replace=False))
    q = np.ascontiguousarray(test_q[eval_ids], dtype=np.float32)
    q_truth = truth[eval_ids][:, :10]

    t = time.time()
    q_hashes = row_hashes(q)
    # stream base in chunks for the overlap gate (memory-safe)
    overlap = 0
    with h5py.File(H5, "r") as f:
        n = f["train"].shape[0]
        for s in range(0, n, 500_000):
            chunk = f["train"][s:s + 500_000]
            overlap += len(q_hashes & row_hashes(chunk))
    log(f"forensics: query/base raw overlap = {overlap} ({time.time()-t:.0f}s)")
    assert overlap == 0, "FORENSICS GATE FAILED"

    norms = np.linalg.norm(base, axis=1)
    lid_idx = np.argsort(norms, kind="stable")
    dim = base.shape[1]
    perbuild = OUT / "deep10m_perbuild.csv"

    def order_idx(kind, seed):
        return (np.random.RandomState(seed).permutation(len(base))
                if kind == "random_order" else lid_idx)

    def run_build(tag, seed, kind):
        idx_order = order_idx(kind, seed)
        t = time.time()
        p = hnswlib.Index(space="cosine", dim=dim)
        p.init_index(max_elements=len(base), ef_construction=EFC, random_seed=seed)
        p.set_num_threads(1)
        # insert in slices to bound per-call memory; labels = original row ids
        SL = 1_000_000
        for s in range(0, len(base), SL):
            sl = idx_order[s:s + SL]
            p.add_items(base[sl], sl.astype(np.int64))
        build_s = time.time() - t
        ip = TMP / "idx.bin"
        p.save_index(str(ip))
        isha = sha256_file(ip)
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
        new = not perbuild.exists() or perbuild.stat().st_size == 0
        with open(perbuild, "a", newline="") as fcsv:
            w = csv.writer(fcsv)
            if new:
                w.writerow(["build", "seed", "order", "index_sha256", "query_id",
                            "ef", "hit_count", "latency_ns_per_query"])
            for r in rows:
                w.writerow([tag, seed, kind, isha, r[0], r[1], r[2], r[3]])
        mh200 = np.mean([r[2] for r in rows if r[1] == 200])
        log(f"{tag}: build {build_s:.0f}s sha={isha[:12]} hits@ef200={mh200:.3f}")
        ip.unlink()
        del p
        assert mh200 > 8.5, f"SANITY GATE FAILED {mh200}"

    done = set()
    if perbuild.exists() and perbuild.stat().st_size > 0:
        done = set(pd_read_builds())
        log(f"resuming, done={sorted(done)}")

    def pd_read_builds():
        import pandas as pd
        return pd.read_csv(perbuild)["build"].unique().tolist()

    builds = [(s, o) for s in SEEDS for o in ORDERS]
    for bi, (seed, kind) in enumerate(builds):
        tag = f"deep10m__seed{seed}__{kind}"
        if tag in done:
            log(f"skip {tag}")
            continue
        if free_gb_real() < MIN_FREE_GB:
            log(f"STOP RULE: free disk {free_gb_real():.1f}GB < {MIN_FREE_GB}GB")
            return
        run_build(tag, seed, kind)

    # identity check: seed13/random twice
    id_hashes = []
    for rep in (1, 2):
        tag = f"deep10m__identity{rep}"
        if tag in done:
            continue
        t = time.time()
        idx_order = order_idx("random_order", 13)
        p = hnswlib.Index(space="cosine", dim=dim)
        p.init_index(max_elements=len(base), ef_construction=EFC, random_seed=13)
        p.set_num_threads(1)
        SL = 1_000_000
        for s in range(0, len(base), SL):
            sl = idx_order[s:s + SL]
            p.add_items(base[sl], sl.astype(np.int64))
        build_s = time.time() - t
        ip = TMP / "idx.bin"
        p.save_index(str(ip))
        isha = sha256_file(ip)
        with open(perbuild, "a", newline="") as fcsv:
            w = csv.writer(fcsv)
            for qi in range(1):
                w.writerow([tag, 13, "random_order", isha, -1, -1, -1, -1.0])
        log(f"identity rep {rep}: {build_s:.0f}s sha={isha[:12]}")
        id_hashes.append(isha)
        ip.unlink()
        del p

    prev = [r for r in pd_read_builds() if r.startswith("deep10m__identity")]
    hs = sorted(prev)
    meta = {
        "forensics_query_base_raw_overlap": overlap,
        "hdf5_sha256": sha,
        "base_shape": list(base.shape),
        "identity_builds": hs,
        "identity_byte_identical": len(hs) >= 2 and hs[0] == hs[-1],
        "wall_total_seconds": time.time() - t0,
    }
    (OUT / "deep10m_run_meta.json").write_text(json.dumps(meta, indent=2))
    log(f"ALL DONE in {(time.time()-t0)/60:.1f} min; identity_equal={meta['identity_byte_identical']}")


if __name__ == "__main__":
    main()
