#!/usr/bin/env python3
"""Prepare preregistered fresh-query adapters and prospective target builds."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import time
from pathlib import Path

import h5py
import numpy as np

SOURCE_SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131]
TARGET_SEEDS = [2381, 2503, 2633]
RANGES = {
    "sift": {"cert": (994000, 994500), "eval": (994500, 995500)},
    "arxiv": {"cert": (103500, 104000), "eval": (104000, 105000)},
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_vecs(path: Path, values: np.ndarray, dtype: str) -> None:
    values = np.ascontiguousarray(values, dtype=np.dtype(dtype))
    prefix = struct.pack("<i", values.shape[1])
    with path.open("wb") as stream:
        for row in values:
            stream.write(prefix)
            stream.write(row.tobytes())


def exact_truth(base: np.ndarray, queries: np.ndarray, metric: str,
                top: int = 100, block: int = 16) -> tuple[np.ndarray, np.ndarray]:
    ids, distances = [], []
    base_norm = (base * base).sum(1)
    for start in range(0, len(queries), block):
        q = queries[start:start + block]
        if metric == "l2":
            scores = (q * q).sum(1)[:, None] + base_norm[None, :] - 2 * q @ base.T
        elif metric == "angular":
            scores = 2.0 - 2.0 * (q @ base.T)
        else:
            raise ValueError(metric)
        selected = np.argpartition(scores, top - 1, axis=1)[:, :top]
        selected_scores = np.take_along_axis(scores, selected, axis=1)
        order = np.argsort(selected_scores, axis=1)
        ids.append(np.take_along_axis(selected, order, axis=1).astype("<i4"))
        distances.append(np.take_along_axis(selected_scores, order, axis=1).astype("<f4"))
    return np.vstack(ids), np.vstack(distances)


def permutation(seed: int, size: int) -> tuple[np.ndarray, np.ndarray]:
    order = np.random.RandomState(seed).permutation(size).astype("<i4")
    inverse = np.empty_like(order)
    inverse[order] = np.arange(size, dtype="<i4")
    return order, inverse


def safe_link(source: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    os.symlink(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["sift", "arxiv"], required=True)
    parser.add_argument("--source-hdf5", type=Path, required=True)
    parser.add_argument("--existing-build-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.time()
    args.output.mkdir(parents=True, exist_ok=False)
    canonical = args.output / "canonical"
    canonical.mkdir()

    expected_dim = 128 if args.dataset == "sift" else 768
    metric = "l2" if args.dataset == "sift" else "angular"
    cert_range, eval_range = RANGES[args.dataset]["cert"], RANGES[args.dataset]["eval"]
    with h5py.File(args.source_hdf5, "r") as source:
        base = np.ascontiguousarray(source["train"][:100000], dtype="<f4")
        cert = np.ascontiguousarray(source["train"][slice(*cert_range)], dtype="<f4")
        evaluation = np.ascontiguousarray(source["train"][slice(*eval_range)], dtype="<f4")
    if base.shape != (100000, expected_dim) or cert.shape[0] != 500 or evaluation.shape[0] != 1000:
        raise ValueError("unexpected frozen source shape")
    if set(map(bytes, cert)).intersection(map(bytes, evaluation)):
        raise RuntimeError("certification/evaluation content overlap")

    query_files = {}
    for role, values, stem in (
        ("cert", cert, "validation"), ("eval", evaluation, "query")
    ):
        truth_ids, truth_distances = exact_truth(base, values, metric)
        vectors_path = canonical / f"{stem}.10K.fvecs"
        ids_path = canonical / f"{stem}.groundtruth.10K.k1000.ivecs"
        distances_path = canonical / f"{stem}.groundtruth.10K.k1000.fvecs"
        write_vecs(vectors_path, values, "<f4")
        write_vecs(ids_path, truth_ids, "<i4")
        write_vecs(distances_path, truth_distances, "<f4")
        query_files[role] = {
            "vectors": vectors_path, "ids": ids_path, "distances": distances_path,
            "truth_ids": truth_ids,
        }

    builds = []
    for seed in SOURCE_SEEDS + TARGET_SEEDS:
        build = args.output / "builds" / f"seed_{seed}" / "SIFT100M"
        build.mkdir(parents=True)
        order, inverse = permutation(seed, len(base))
        if seed in SOURCE_SEEDS:
            source_base = args.existing_build_root / f"seed_{seed}" / "SIFT100M" / "base.100M.fvecs"
            safe_link(source_base, build / "base.100M.fvecs")
            role = "historical_source"
        else:
            write_vecs(build / "base.100M.fvecs", base[order], "<f4")
            role = "prospective_target"
        for role_name, stem in (("cert", "validation"), ("eval", "query")):
            item = query_files[role_name]
            safe_link(item["vectors"], build / f"{stem}.10K.fvecs")
            safe_link(item["distances"], build / f"{stem}.groundtruth.10K.k1000.fvecs")
            mapped = inverse[item["truth_ids"]]
            write_vecs(build / f"{stem}.groundtruth.10K.k1000.ivecs", mapped, "<i4")
        builds.append({
            "seed": seed,
            "role": role,
            "permutation_sha256": hashlib.sha256(order.tobytes()).hexdigest(),
            "base_sha256": sha(build / "base.100M.fvecs"),
        })

    files = []
    for path in sorted(args.output.rglob("*")):
        if path.is_file() and not path.is_symlink():
            files.append({"path": str(path.relative_to(args.output)), "bytes": path.stat().st_size,
                          "sha256": sha(path)})
    ledger = {
        "status": "PASS",
        "dataset": args.dataset,
        "source_hdf5": str(args.source_hdf5),
        "source_hdf5_sha256": sha(args.source_hdf5),
        "metric": metric,
        "base_rows": [0, 100000],
        "certification_rows": list(cert_range),
        "evaluation_rows": list(eval_range),
        "role_overlap": 0,
        "source_seeds": SOURCE_SEEDS,
        "target_seeds": TARGET_SEEDS,
        "builds": builds,
        "generated_files": files,
        "elapsed_seconds": time.time() - started,
    }
    (args.output / "adapter_ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "dataset": args.dataset,
                      "files": len(files), "elapsed_seconds": ledger["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
