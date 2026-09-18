#!/usr/bin/env python3
"""Run the frozen Deep1M target-certification roles on existing indexes."""

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

import h5py
import numpy as np


GRID = [200, 300, 400, 600, 800, 1200]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def normalize(values):
    values = np.asarray(values, dtype=np.float32)
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return np.ascontiguousarray(values / np.maximum(norms, np.finfo(np.float32).tiny))


def write_vecs(path, values, dtype):
    values = np.asarray(values, dtype=dtype)
    dim = np.full((values.shape[0], 1), values.shape[1], dtype="<i4")
    payload = np.concatenate([dim.view("<f4"), values], axis=1) if dtype == "<f4" else np.concatenate([dim, values], axis=1)
    payload.tofile(path)


def exact_truth(base, queries, k=10):
    best_scores = np.full((len(queries), k), -np.inf, dtype=np.float32)
    best_ids = np.full((len(queries), k), -1, dtype=np.int32)
    for start in range(0, len(base), 100000):
        block = normalize(base[start:start + 100000])
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--roles", type=Path, required=True)
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    free = shutil.disk_usage(args.output.parent).free
    if free < 7 * 2**30:
        raise RuntimeError("insufficient data500 space: require projected 2 GiB plus 5 GiB reserve")
    args.output.mkdir(parents=True, exist_ok=True)
    inputs = args.output / "inputs"
    replay = args.output / "replay"
    inputs.mkdir(exist_ok=True)
    replay.mkdir(exist_ok=True)

    role_manifest = json.loads(args.roles.read_text(encoding="utf-8"))
    role_order = ["source_design", "target_certification", "target_evaluation"]
    external_ids = np.asarray([qid for role in role_order for qid in role_manifest["roles"][role]], dtype=np.int64)
    with h5py.File(args.dataset, "r") as handle:
        base = np.asarray(handle["train"][:1000000], dtype=np.float32)
        # h5py requires a globally increasing fancy index; materializing this
        # 10k-row test matrix preserves the preregistered role order exactly.
        all_queries = np.asarray(handle["test"], dtype=np.float32)
        queries = normalize(all_queries[external_ids])
    query_file = inputs / "queries.fvecs"
    truth_file = inputs / "truth.ivecs"
    if not query_file.exists():
        write_vecs(query_file, queries, "<f4")
    truth_seconds = 0.0
    if not truth_file.exists():
        start = time.time()
        truth = exact_truth(base, queries)
        truth_seconds = time.time() - start
        write_vecs(truth_file, truth, "<i4")

    binary = args.prior_root / "bin/deep1m_counting_runner"
    builds = sorted((args.prior_root / "builds").glob("*.bin"))
    if len(builds) != 8 or not binary.exists():
        raise RuntimeError("frozen Deep1M indexes or counting runner missing")
    ledger = []
    for index_path in builds:
        build = index_path.stem
        output = replay / f"{build}.csv"
        if not output.exists():
            subprocess.run([
                str(binary), str(index_path), str(query_file), str(truth_file),
                ",".join(map(str, GRID)), build, str(output),
            ], check=True)
        ledger.append({
            "build": build,
            "index_sha256": sha256(index_path),
            "response_sha256": sha256(output),
            "rows": 1500 * len(GRID),
        })
        (args.output / "progress.json").write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "complete", "build": build}), flush=True)
    inventory = {
        "status": "COMPLETE",
        "grid": GRID,
        "role_order": role_order,
        "role_manifest_sha256": sha256(args.roles),
        "dataset_sha256": sha256(args.dataset),
        "queries_sha256": sha256(query_file),
        "truth_sha256": sha256(truth_file),
        "truth_seconds_this_run": truth_seconds,
        "builds": ledger,
    }
    (args.output / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "builds": len(ledger), "free_gib": free / 2**30}, indent=2))


if __name__ == "__main__":
    main()
