#!/usr/bin/env python3
"""Build hash-audited DARTH adapters for frozen Arxiv data-refresh cells."""

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


SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267]
FRACTIONS = [0.01, 0.05, 0.10]
ROLES = {
    "training": (100000, 102000, "learn.1M"),
    "validation": (102000, 102500, "validation.10K"),
    "evaluation": (102500, 103500, "query.10K"),
}
TOP = 100


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_vecs(path: Path, values: np.ndarray, dtype: str) -> None:
    values = np.ascontiguousarray(values, dtype=np.dtype(dtype))
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite: {path}")
    with path.open("wb") as stream:
        prefix = struct.pack("<i", values.shape[1])
        for row in values:
            stream.write(prefix)
            stream.write(row.tobytes())


def link(source: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"refusing to replace: {destination}")
    os.symlink(source, destination)


def exact_truth(base: np.ndarray, queries: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    base_norm = (base * base).sum(axis=1)
    ids, distances = [], []
    for start in range(0, len(queries), 16):
        query = queries[start : start + 16]
        matrix = (query * query).sum(axis=1)[:, None] + base_norm[None, :] - 2 * (query @ base.T)
        nearest = np.argpartition(matrix, TOP - 1, axis=1)[:, :TOP]
        nearest_distances = np.take_along_axis(matrix, nearest, axis=1)
        order = np.argsort(nearest_distances, axis=1)
        ids.append(np.take_along_axis(nearest, order, axis=1).astype("<i4"))
        distances.append(np.take_along_axis(nearest_distances, order, axis=1).astype("<f4"))
    return np.vstack(ids), np.vstack(distances)


def canonical_names(role: str, stem: str) -> tuple[list[str], list[str], list[str]]:
    query_names = [f"{stem}.fvecs"]
    id_names = [f"{stem}.groundtruth.ivecs"]
    distance_names = [f"{stem}.groundtruth.fvecs"]
    aliases = {
        "training": "learn.groundtruth.1M.k1000",
        "validation": "validation.groundtruth.10K.k1000",
        "evaluation": "query.groundtruth.10K.k1000",
    }
    if role in aliases:
        id_names.append(aliases[role] + ".ivecs")
        distance_names.append(aliases[role] + ".fvecs")
    return query_names, id_names, distance_names


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hdf5", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    args = parser.parse_args()
    started = time.time()
    with h5py.File(args.hdf5, "r") as source:
        old = np.ascontiguousarray(source["train"][:100000], dtype="<f4")
        reserve = np.ascontiguousarray(source["train"][103500:113500], dtype="<f4")
        queries = {role: np.ascontiguousarray(source["train"][start:end], dtype="<f4") for role, (start, end, _) in ROLES.items()}
    base_keys = {row.tobytes() for row in np.vstack([old, reserve])}
    role_keys = {role: {row.tobytes() for row in values} for role, values in queries.items()}
    if any(base_keys & values for values in role_keys.values()):
        raise ValueError("query content overlaps old base or insert reserve")
    roles = list(role_keys)
    if any(role_keys[roles[i]] & role_keys[roles[j]] for i in range(len(roles)) for j in range(i)):
        raise ValueError("query role content overlap")

    refreshes = []
    for fraction in FRACTIONS:
        count = int(len(old) * fraction)
        rng = np.random.RandomState(991 + int(fraction * 10000))
        deleted = np.sort(rng.choice(len(old), count, replace=False))
        keep = np.ones(len(old), dtype=bool)
        keep[deleted] = False
        refreshed = np.ascontiguousarray(np.vstack([old[keep], reserve[:count]]), dtype="<f4")
        common = args.output_root / f"refresh_{int(fraction * 100):02d}" / "common" / "SIFT100M"
        common.mkdir(parents=True, exist_ok=True)
        truth = {}
        common_hashes = {}
        for role, values in queries.items():
            stem = ROLES[role][2]
            query_names, id_names, distance_names = canonical_names(role, stem)
            ids, distances = exact_truth(refreshed, values)
            truth[role] = ids
            for name in query_names:
                write_vecs(common / name, values, "<f4")
                common_hashes[name] = sha256(common / name)
            for name in id_names:
                write_vecs(common / name, ids, "<i4")
                common_hashes[name] = sha256(common / name)
            for name in distance_names:
                write_vecs(common / name, distances, "<f4")
                common_hashes[name] = sha256(common / name)

        builds = []
        for seed in SEEDS:
            build = args.output_root / f"refresh_{int(fraction * 100):02d}" / f"seed_{seed}" / "SIFT100M"
            build.mkdir(parents=True, exist_ok=True)
            permutation = np.random.RandomState(seed).permutation(len(refreshed)).astype("<i4")
            inverse = np.empty_like(permutation)
            inverse[permutation] = np.arange(len(refreshed), dtype="<i4")
            write_vecs(build / "base.100M.fvecs", refreshed[permutation], "<f4")
            for role, (_, _, stem) in ROLES.items():
                query_names, id_names, distance_names = canonical_names(role, stem)
                for name in query_names + distance_names:
                    link(common / name, build / name)
                for name in id_names:
                    write_vecs(build / name, inverse[truth[role]], "<i4")
            builds.append({
                "seed": seed,
                "base_sha256": sha256(build / "base.100M.fvecs"),
                "permutation_sha256": hashlib.sha256(permutation.tobytes()).hexdigest(),
            })
        refreshes.append({
            "fraction": fraction,
            "deleted_count": count,
            "inserted_count": count,
            "deleted_ids_sha256": hashlib.sha256(deleted.astype("<i4").tobytes()).hexdigest(),
            "refreshed_content_sha256": hashlib.sha256(refreshed.tobytes()).hexdigest(),
            "common_files": common_hashes,
            "builds": builds,
        })
    ledger = {
        "status": "PASS",
        "source_hdf5": str(args.hdf5),
        "source_hdf5_sha256": sha256(args.hdf5),
        "old_base_rows": [0, 100000],
        "insert_reserve_rows": [103500, 113500],
        "query_roles": {role: [start, end] for role, (start, end, _) in ROLES.items()},
        "content_overlap_zero": True,
        "refreshes": refreshes,
        "elapsed_seconds": time.time() - started,
    }
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "refreshes": len(refreshes), "builds": len(SEEDS) * len(refreshes), "elapsed_seconds": ledger["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
