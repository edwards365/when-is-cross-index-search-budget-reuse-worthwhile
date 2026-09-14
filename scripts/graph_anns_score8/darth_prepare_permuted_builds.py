#!/usr/bin/env python3
"""Prepare deterministic insertion-order adapters for DARTH/Faiss rebuilds."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
from pathlib import Path

import numpy as np


SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267]
QUERY_FILES = ["learn.1M.fvecs", "validation.10K.fvecs", "certification.500.fvecs", "query.10K.fvecs"]
TRUTH_ID_FILES = [
    "learn.1M.groundtruth.ivecs",
    "learn.groundtruth.1M.k1000.ivecs",
    "validation.10K.groundtruth.ivecs",
    "validation.groundtruth.10K.k1000.ivecs",
    "certification.500.groundtruth.ivecs",
    "query.10K.groundtruth.ivecs",
    "query.groundtruth.10K.k1000.ivecs",
]
TRUTH_DISTANCE_FILES = [
    "learn.1M.groundtruth.fvecs",
    "learn.groundtruth.1M.k1000.fvecs",
    "validation.10K.groundtruth.fvecs",
    "validation.groundtruth.10K.k1000.fvecs",
    "certification.500.groundtruth.fvecs",
    "query.10K.groundtruth.fvecs",
    "query.groundtruth.10K.k1000.fvecs",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_vecs(path: Path, dtype: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.dtype(dtype))
    if raw.size == 0:
        raise ValueError(f"empty vector file: {path}")
    dim = int(raw.view("<i4")[0])
    width = dim + 1
    if raw.size % width:
        raise ValueError(f"invalid vector file width: {path}")
    matrix = raw.reshape(-1, width)
    if not np.all(matrix[:, 0].copy().view("<i4") == dim):
        raise ValueError(f"inconsistent vector dimensions: {path}")
    return np.ascontiguousarray(matrix[:, 1:])


def write_vecs(path: Path, values: np.ndarray, dtype: str) -> None:
    values = np.ascontiguousarray(values, dtype=np.dtype(dtype))
    with path.open("wb") as stream:
        prefix = struct.pack("<i", values.shape[1])
        for row in values:
            stream.write(prefix)
            stream.write(row.tobytes())


def link(source: Path, destination: Path) -> None:
    if destination.is_symlink() and destination.resolve() == source.resolve():
        return
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"refusing to replace existing adapter file: {destination}")
    os.symlink(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()

    base = read_vecs(args.source / "base.100M.fvecs", "<f4")
    if base.shape != (100000, 128):
        raise ValueError(f"unexpected frozen base shape: {base.shape}")
    truth = {name: read_vecs(args.source / name, "<i4") for name in TRUTH_ID_FILES}
    builds = []
    for seed in SEEDS:
        build_dir = args.output_root / f"seed_{seed}" / "SIFT100M"
        build_dir.mkdir(parents=True, exist_ok=True)
        rng = np.random.RandomState(seed)
        permutation = rng.permutation(len(base)).astype("<i4")
        inverse = np.empty_like(permutation)
        inverse[permutation] = np.arange(len(base), dtype="<i4")
        base_path = build_dir / "base.100M.fvecs"
        if base_path.exists():
            raise FileExistsError(f"refusing to overwrite build adapter: {base_path}")
        write_vecs(base_path, base[permutation], "<f4")
        for name in QUERY_FILES + TRUTH_DISTANCE_FILES:
            link(args.source / name, build_dir / name)
        mapped_hashes = {}
        for name, ids in truth.items():
            if ids.min() < 0 or ids.max() >= len(base):
                raise ValueError(f"truth ID out of range: {name}")
            output = build_dir / name
            write_vecs(output, inverse[ids], "<i4")
            mapped_hashes[name] = sha256(output)
        builds.append(
            {
                "seed": seed,
                "directory": str(build_dir),
                "permutation_sha256": hashlib.sha256(permutation.tobytes()).hexdigest(),
                "base_sha256": sha256(base_path),
                "mapped_truth_sha256": mapped_hashes,
                "first_ten_original_ids_in_insertion_order": permutation[:10].tolist(),
            }
        )
    ledger = {
        "status": "PASS",
        "source": str(args.source),
        "source_base_sha256": sha256(args.source / "base.100M.fvecs"),
        "build_count": len(builds),
        "base_shape": list(base.shape),
        "seeds": SEEDS,
        "builds": builds,
        "query_files_symlinked_unchanged": QUERY_FILES,
        "truth_distance_files_symlinked_unchanged": TRUTH_DISTANCE_FILES,
        "truth_ids_remapped_by_inverse_permutation": TRUTH_ID_FILES,
    }
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "builds": len(builds)}, indent=2))


if __name__ == "__main__":
    main()
