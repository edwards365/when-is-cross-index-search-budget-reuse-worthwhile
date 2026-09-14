#!/usr/bin/env python3
"""Preregistered Score8 P2 data-refresh experiment; smoke precedes full matrix."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import h5py
import hnswlib
import numpy as np

GRID = np.array([10, 20, 40, 80, 120, 200], dtype=np.int32)
H = 10
SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267]
REPO = Path(__file__).resolve().parents[2]
HEAVY = Path("/home/wlk/data500/graph_anns_score8/data_refresh")
SMALL = REPO / "results/graph_anns_score8/p2_data_refresh"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def exact_truth(base: np.ndarray, queries: np.ndarray, metric: str) -> np.ndarray:
    out = []
    b2 = (base * base).sum(1) if metric == "l2" else None
    for s in range(0, len(queries), 32):
        q = queries[s:s + 32]
        if metric == "l2":
            scores = b2[None, :] - 2.0 * (q @ base.T)
        else:
            scores = -(q @ base.T)
        out.append(np.argpartition(scores, H - 1, axis=1)[:, :H])
    return np.vstack(out)


def build_and_eval(base: np.ndarray, ids: np.ndarray, queries: np.ndarray,
                   truth: np.ndarray, metric: str, seed: int, save: Path):
    order = np.random.RandomState(seed).permutation(len(base))
    index = hnswlib.Index(space=metric, dim=base.shape[1])
    index.init_index(max_elements=len(base), ef_construction=100, M=16,
                     random_seed=seed)
    index.set_num_threads(1)
    index.add_items(base[order], ids[order])
    hits = np.zeros((len(queries), len(GRID)), dtype=np.int8)
    for j, ef in enumerate(GRID):
        index.set_ef(int(ef))
        labels, _ = index.knn_query(queries, k=H, num_threads=1)
        hits[:, j] = [len(set(a.tolist()) & set(b.tolist()))
                      for a, b in zip(labels, truth)]
    index.save_index(str(save))
    index2 = hnswlib.Index(space=metric, dim=base.shape[1])
    index2.load_index(str(save), max_elements=len(base))
    index2.set_num_threads(1)
    index2.set_ef(int(GRID[-1]))
    a, _ = index.knn_query(queries, k=H, num_threads=1)
    b, _ = index2.knn_query(queries, k=H, num_threads=1)
    if not np.array_equal(a, b):
        raise RuntimeError("index serialization replay mismatch")
    return hits


def bottoms(hits: np.ndarray) -> np.ndarray:
    ok = hits >= H
    return np.where(ok.any(1), GRID[np.argmax(ok, axis=1)], -1).astype(np.int32)


def run_smoke() -> dict:
    hdf5 = REPO / "data/raw/sift-128-euclidean.hdf5"
    out = HEAVY / "smoke_sift_1pct"
    out.mkdir(parents=True, exist_ok=True)
    SMALL.mkdir(parents=True, exist_ok=True)
    with h5py.File(hdf5, "r") as f:
        old = np.ascontiguousarray(f["train"][:100000], dtype=np.float32)
        inserts = np.ascontiguousarray(f["train"][100000:101000], dtype=np.float32)
        queries = np.ascontiguousarray(f["train"][999000:999100], dtype=np.float32)
    rng = np.random.RandomState(991)
    deleted = np.sort(rng.choice(100000, 1000, replace=False))
    keep = np.ones(100000, dtype=bool)
    keep[deleted] = False
    refreshed = np.ascontiguousarray(np.vstack([old[keep], inserts]))
    old_ids = np.arange(100000, dtype=np.int64)
    refreshed_ids = np.r_[old_ids[keep], np.arange(100000, 101000, dtype=np.int64)]
    if len(np.unique(refreshed_ids)) != 100000:
        raise RuntimeError("refresh identity collision")
    t0 = time.time()
    old_truth = exact_truth(old, queries, "l2")
    # Brute-force truth is returned in refreshed-array row coordinates, whereas
    # hnswlib returns the persistent vector labels supplied at insertion.
    new_truth = refreshed_ids[exact_truth(refreshed, queries, "l2")]
    old_hits = build_and_eval(old, old_ids, queries, old_truth, "l2", SEEDS[0], out / "old.bin")
    new_hits = build_and_eval(refreshed, refreshed_ids, queries, new_truth, "l2", SEEDS[0], out / "refreshed.bin")
    old_b = bottoms(old_hits)
    deployed = np.where(old_b < 0, GRID[-1], old_b)
    jj = np.searchsorted(GRID, deployed)
    refresh_risk = float(np.mean(new_hits[np.arange(len(queries)), jj] < H))
    result = {
        "stage": "P2_DATA_REFRESH_SMOKE",
        "status": "PASS",
        "dataset": "SIFT-100K",
        "refresh_fraction": 0.01,
        "n_queries": 100,
        "n_deleted": 1000,
        "n_inserted": 1000,
        "base_size_before": 100000,
        "base_size_after": 100000,
        "identity_overlap_query_base": 0,
        "serialized_replay": True,
        "old_single_build_budget_refresh_risk": refresh_risk,
        "old_bottom_failure_rate": float(np.mean(old_b < 0)),
        "elapsed_seconds": time.time() - t0,
        "input_sha256": sha(hdf5),
        "heavy_output": str(out),
        "note": "Smoke is infrastructure/semantic evidence only; it is not the registered k=9 scientific result."
    }
    (SMALL / "smoke_verdict.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "hits.npz").unlink(missing_ok=True)
    np.savez_compressed(out / "hits.npz", old=old_hits, refreshed=new_hits,
                        grid=GRID, deleted=deleted)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if not args.smoke:
        raise SystemExit("Full matrix is intentionally gated; run --smoke first")
    print(json.dumps(run_smoke(), indent=2))


if __name__ == "__main__":
    main()
