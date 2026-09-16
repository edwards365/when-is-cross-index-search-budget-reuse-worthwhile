#!/usr/bin/env python3
"""Prepare, build, instrument, and replay the preregistered Deep1M cell."""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
import os
import resource
import shutil
import subprocess
import time
from pathlib import Path

import h5py
import hnswlib
import numpy as np


REPO = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(os.environ.get("ICBA_EA85_ROOT", "/home/wlk/data500/graph_anns_phase3_ea85"))
GRID = [10, 20, 40, 80, 120, 200]
SEEDS = [3011, 3203, 3413, 3617]
ORDERS = ["random", "norm_ascending"]
N_BASE = 1_000_000
N_QUERY = 1_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    return np.ascontiguousarray(x / np.maximum(norms, np.finfo(np.float32).tiny))


def write_vecs(path: Path, values: np.ndarray, dtype: str) -> None:
    values = np.asarray(values, dtype=dtype)
    dim = np.full((values.shape[0], 1), values.shape[1], dtype="<i4")
    if dtype == "<f4":
        payload = np.concatenate([dim.view("<f4"), values], axis=1)
    else:
        payload = np.concatenate([dim, values], axis=1)
    payload.tofile(path)


def row_hashes(values: np.ndarray) -> set[str]:
    raw = np.ascontiguousarray(values, dtype="<f4").view(np.uint8).reshape(len(values), -1)
    return {hashlib.sha256(row.tobytes()).hexdigest() for row in raw}


def exact_truth(base: np.ndarray, queries: np.ndarray, k: int = 10) -> np.ndarray:
    best_scores = np.full((len(queries), k), -np.inf, dtype=np.float32)
    best_ids = np.full((len(queries), k), -1, dtype=np.int32)
    for start in range(0, len(base), 100_000):
        block = normalize(base[start:start + 100_000])
        for qs in range(0, len(queries), 100):
            q = queries[qs:qs + 100]
            scores = q @ block.T
            local = np.argpartition(scores, -k, axis=1)[:, -k:]
            local_scores = np.take_along_axis(scores, local, axis=1)
            ids = local.astype(np.int32) + start
            merged_scores = np.concatenate([best_scores[qs:qs + len(q)], local_scores], axis=1)
            merged_ids = np.concatenate([best_ids[qs:qs + len(q)], ids], axis=1)
            keep = np.argpartition(merged_scores, -k, axis=1)[:, -k:]
            best_scores[qs:qs + len(q)] = np.take_along_axis(merged_scores, keep, axis=1)
            best_ids[qs:qs + len(q)] = np.take_along_axis(merged_ids, keep, axis=1)
    order = np.argsort(-best_scores, axis=1)
    return np.take_along_axis(best_ids, order, axis=1)


def prepare(root: Path, h5_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    root.mkdir(parents=True, exist_ok=True)
    inputs = root / "inputs"
    inputs.mkdir(exist_ok=True)
    manifest_path = inputs / "manifest.json"
    with h5py.File(h5_path, "r") as f:
        base = np.asarray(f["train"][:N_BASE], dtype=np.float32)
        all_queries = np.asarray(f["test"], dtype=np.float32)
    prior = set(np.sort(np.random.RandomState(991).choice(len(all_queries), 500, replace=False)).tolist())
    remaining = np.asarray([i for i in range(len(all_queries)) if i not in prior], dtype=int)
    ids = np.sort(np.random.default_rng(2991).choice(remaining, N_QUERY, replace=False))
    queries = normalize(all_queries[ids])
    overlap = 0
    qhash = row_hashes(all_queries[ids])
    for start in range(0, len(base), 100_000):
        overlap += len(qhash & row_hashes(base[start:start + 100_000]))
    if overlap:
        raise RuntimeError(f"query/base overlap: {overlap}")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest["query_ids"] != ids.tolist():
            raise RuntimeError("frozen query id drift")
        truth = np.fromfile(inputs / "truth.ivecs", dtype="<i4").reshape(N_QUERY, 11)[:, 1:]
    else:
        t0 = time.time()
        truth = exact_truth(base, queries)
        write_vecs(inputs / "queries.fvecs", queries, "<f4")
        write_vecs(inputs / "truth.ivecs", truth, "<i4")
        write_vecs(inputs / "smoke_queries.fvecs", queries[:20], "<f4")
        write_vecs(inputs / "smoke_truth.ivecs", truth[:20], "<i4")
        manifest = {
            "dataset_sha256": sha256(h5_path),
            "base_rows": N_BASE,
            "query_ids": ids.tolist(),
            "query_ids_sha256": hashlib.sha256(ids.astype("<i8").tobytes()).hexdigest(),
            "prior_p10_overlap": len(prior & set(ids.tolist())),
            "base_content_overlap": overlap,
            "truth_seconds": time.time() - t0,
            "queries_sha256": sha256(inputs / "queries.fvecs"),
            "truth_sha256": sha256(inputs / "truth.ivecs"),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return base, queries, truth


def build_index(base: np.ndarray, seed: int, order_name: str, path: Path) -> float:
    if path.exists():
        return 0.0
    if order_name == "random":
        order = np.random.default_rng(seed).permutation(len(base))
    else:
        order = np.argsort(np.linalg.norm(base, axis=1), kind="stable")
    index = hnswlib.Index(space="cosine", dim=base.shape[1])
    index.init_index(max_elements=len(base), M=16, ef_construction=100, random_seed=seed)
    index.set_num_threads(1)
    t0 = time.time()
    for start in range(0, len(base), 100_000):
        ids = order[start:start + 100_000]
        index.add_items(base[ids], ids.astype(np.int64))
    elapsed = time.time() - t0
    index.save_index(str(path))
    return elapsed


def parse_topk(path: Path) -> dict[tuple[int, int], list[int]]:
    with path.open(newline="") as f:
        return {(int(r["query_id"]), int(r["ef"])): [int(x) for x in r["topk"].split(";")] for r in csv.DictReader(f)}


def native_smoke(root: Path, index_path: Path, build_id: str, queries: np.ndarray, binary: Path) -> None:
    out = root / "smoke_counting.csv"
    subprocess.run([str(binary), str(index_path), str(root / "inputs/smoke_queries.fvecs"),
                    str(root / "inputs/smoke_truth.ivecs"), "10,40,200", build_id, str(out)], check=True)
    observed = parse_topk(out)
    index = hnswlib.Index(space="cosine", dim=queries.shape[1])
    index.load_index(str(index_path))
    index.set_num_threads(1)
    for ef in (10, 40, 200):
        index.set_ef(ef)
        labels, _ = index.knn_query(queries[:20], k=10)
        for qid, row in enumerate(labels):
            if observed[(qid, ef)] != row.tolist():
                raise RuntimeError(f"native/counter mismatch q={qid} ef={ef}")
    (root / "INSTRUMENTATION_GATE_PASS").write_text("60/60 top-k exact matches\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--dataset", type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    root = args.data_root.resolve() / "deep1m"
    h5_path = (args.dataset or (repo / "data/raw/deep-image-96-angular.hdf5")).resolve()
    if shutil.disk_usage(root.parent).free < 5 * 2**30 + 4 * 2**30:
        raise RuntimeError("insufficient data500 space")
    base, queries, _ = prepare(root, h5_path)
    binary = root / "bin/deep1m_counting_runner"
    binary.parent.mkdir(exist_ok=True)
    subprocess.run(["g++", "-std=c++17", "-O3", "-pthread", "-I", str(repo / "third_party/hnswlib"),
                    str(repo / "cpp/src/deep1m_counting_runner.cpp"), "-o", str(binary)], check=True)
    builds = root / "builds"
    replay = root / "replay"
    builds.mkdir(exist_ok=True)
    replay.mkdir(exist_ok=True)
    ledger = []
    smoke_done = (root / "INSTRUMENTATION_GATE_PASS").exists()
    for seed in SEEDS:
        for order_name in ORDERS:
            build_id = f"deep1m_seed{seed}_{order_name}"
            index_path = builds / f"{build_id}.bin"
            build_seconds = build_index(base, seed, order_name, index_path)
            if not smoke_done:
                native_smoke(root, index_path, build_id, queries, binary)
                smoke_done = True
            output = replay / f"{build_id}.csv"
            if not output.exists():
                subprocess.run([str(binary), str(index_path), str(root / "inputs/queries.fvecs"),
                                str(root / "inputs/truth.ivecs"), ",".join(map(str, GRID)), build_id, str(output)], check=True)
            ledger.append({"build": build_id, "seed": seed, "order": order_name,
                           "index_sha256": sha256(index_path), "index_bytes": index_path.stat().st_size,
                           "build_seconds_this_run": build_seconds, "replay_sha256": sha256(output),
                           "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
            (root / "progress.json").write_text(json.dumps(ledger, indent=2) + "\n")
    (root / "STATUS").write_text("COMPLETE\n")


if __name__ == "__main__":
    main()
