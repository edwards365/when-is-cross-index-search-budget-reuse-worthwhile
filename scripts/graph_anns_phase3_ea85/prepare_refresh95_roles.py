#!/usr/bin/env python3
"""Prepare new Recall@10=.95 query roles for frozen 5% refresh indexes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import time
from pathlib import Path

import faiss
import h5py
import numpy as np


SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267]
ROLES = {
    "selection": ("learn.1M", "training"),
    "certification": ("validation.10K", "validation"),
    "cold_evaluation": ("query.10K", "testing"),
}
TOP = 100


CONFIG = {
    "sift100k": {
        "hdf5": Path("/home/wlk/projects/navigation-aware-resistance-hnsw/data/raw/sift-128-euclidean.hdf5"),
        "reserve": (100000, 110000),
        "ranges": {"selection": (994000, 994500), "certification": (994500, 995000), "cold_evaluation": (995000, 996000)},
        "old_dataset": "/home/wlk/data500/graph_anns_score8/darth_comparison/multibuild/datasets/seed_{seed}/SIFT100M",
        "target_dataset": "/home/wlk/data500/graph_anns_score8/darth_comparison/refresh/datasets/refresh_05/seed_{seed}/SIFT100M",
    },
    "arxiv_nomic_100k": {
        "hdf5": Path("/home/wlk/projects/navigation-aware-resistance-hnsw/data/raw/arxiv-nomic-768-normalized.hdf5"),
        "reserve": (103500, 113500),
        "ranges": {"selection": (113500, 114000), "certification": (114000, 114500), "cold_evaluation": (114500, 115500)},
        "old_dataset": "/home/wlk/data500/graph_anns_score8/darth_comparison/arxiv/builds/seed_{seed}/SIFT100M",
        "target_dataset": "/home/wlk/data500/graph_anns_score8/darth_comparison/arxiv/refresh/datasets/refresh_05/seed_{seed}/SIFT100M",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_vecs(path: Path, values: np.ndarray, dtype: str) -> None:
    values = np.ascontiguousarray(values, dtype=np.dtype(dtype))
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    with path.open("wb") as stream:
        prefix = struct.pack("<i", values.shape[1])
        for row in values:
            stream.write(prefix)
            stream.write(row.tobytes())


def link(source: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    os.symlink(source, destination)


def exact_truth(base: np.ndarray, queries: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    index = faiss.IndexFlatL2(base.shape[1])
    index.add(np.ascontiguousarray(base, np.float32))
    distances, ids = index.search(np.ascontiguousarray(queries, np.float32), TOP)
    return ids.astype("<i4"), distances.astype("<f4")


def vector_keys(values: np.ndarray) -> set[bytes]:
    return {row.tobytes() for row in np.ascontiguousarray(values, np.float32)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=sorted(CONFIG), required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--sift-hdf5", type=Path, default=CONFIG["sift100k"]["hdf5"])
    parser.add_argument("--arxiv-hdf5", type=Path, default=CONFIG["arxiv_nomic_100k"]["hdf5"])
    parser.add_argument(
        "--score8-root", type=Path,
        default=Path(os.environ.get("ICBA_SCORE8_ROOT", "/home/wlk/data500/graph_anns_score8")),
    )
    args = parser.parse_args()
    cfg = dict(CONFIG[args.dataset])
    score8 = args.score8_root.resolve()
    if args.dataset == "sift100k":
        cfg["hdf5"] = args.sift_hdf5.resolve()
        cfg["old_dataset"] = str(score8 / "darth_comparison/multibuild/datasets/seed_{seed}/SIFT100M")
        cfg["target_dataset"] = str(score8 / "darth_comparison/refresh/datasets/refresh_05/seed_{seed}/SIFT100M")
    else:
        cfg["hdf5"] = args.arxiv_hdf5.resolve()
        cfg["old_dataset"] = str(score8 / "darth_comparison/arxiv/builds/seed_{seed}/SIFT100M")
        cfg["target_dataset"] = str(score8 / "darth_comparison/arxiv/refresh/datasets/refresh_05/seed_{seed}/SIFT100M")
    started = time.time()

    with h5py.File(cfg["hdf5"], "r") as source:
        old = np.ascontiguousarray(source["train"][:100000], np.float32)
        rs, re = cfg["reserve"]
        reserve = np.ascontiguousarray(source["train"][rs:re], np.float32)
        queries = {
            role: np.ascontiguousarray(source["train"][start:end], np.float32)
            for role, (start, end) in cfg["ranges"].items()
        }

    rng = np.random.RandomState(1491)
    deleted = np.sort(rng.choice(100000, 5000, replace=False))
    keep = np.ones(100000, dtype=bool)
    keep[deleted] = False
    refreshed = np.ascontiguousarray(np.vstack([old[keep], reserve[:5000]]), np.float32)

    occupied = vector_keys(np.vstack([old, reserve]))
    role_keys = {role: vector_keys(values) for role, values in queries.items()}
    if any(occupied & keys for keys in role_keys.values()):
        raise ValueError("query overlaps base or insert reserve")
    names = list(role_keys)
    if any(role_keys[names[i]] & role_keys[names[j]] for i in range(len(names)) for j in range(i)):
        raise ValueError("query-role content overlap")

    output = args.output_root / args.dataset
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema_version": "ea85-phase2-refresh95-inputs-1.0",
        "dataset": args.dataset,
        "source_hdf5": str(cfg["hdf5"]),
        "source_hdf5_sha256": sha256(cfg["hdf5"]),
        "refresh_fraction": 0.05,
        "deleted_ids_sha256": hashlib.sha256(deleted.astype("<i4").tobytes()).hexdigest(),
        "query_ranges": cfg["ranges"],
        "content_overlap_zero": True,
        "snapshots": {},
    }

    for snapshot, base, template in (
        ("old", old, cfg["old_dataset"]),
        ("target_refresh05", refreshed, cfg["target_dataset"]),
    ):
        common = output / snapshot / "common"
        common.mkdir(parents=True)
        truths = {}
        common_files = {}
        for role, values in queries.items():
            stem, _ = ROLES[role]
            ids, distances = exact_truth(base, values)
            truths[role] = ids
            qpath = common / f"{stem}.fvecs"
            dpath = common / f"{stem}.groundtruth.fvecs"
            write_vecs(qpath, values, "<f4")
            write_vecs(dpath, distances, "<f4")
            common_files[qpath.name] = sha256(qpath)
            common_files[dpath.name] = sha256(dpath)

        builds = []
        for seed in SEEDS:
            source_dir = Path(template.format(seed=seed))
            source_base = source_dir / "base.100M.fvecs"
            if not source_base.exists():
                raise FileNotFoundError(source_base)
            destination = output / snapshot / f"seed_{seed}" / "SIFT100M"
            destination.mkdir(parents=True)
            link(source_base.resolve(), destination / "base.100M.fvecs")
            permutation = np.random.RandomState(seed).permutation(100000).astype("<i4")
            inverse = np.empty_like(permutation)
            inverse[permutation] = np.arange(100000, dtype="<i4")
            build_files = {}
            for role, (stem, _) in ROLES.items():
                link((common / f"{stem}.fvecs").resolve(), destination / f"{stem}.fvecs")
                link((common / f"{stem}.groundtruth.fvecs").resolve(), destination / f"{stem}.groundtruth.fvecs")
                mapped = inverse[truths[role]]
                ipath = destination / f"{stem}.groundtruth.ivecs"
                write_vecs(ipath, mapped, "<i4")
                build_files[ipath.name] = sha256(ipath)
                alias = {
                    "selection": "learn.groundtruth.1M.k1000.ivecs",
                    "certification": "validation.groundtruth.10K.k1000.ivecs",
                    "cold_evaluation": "query.groundtruth.10K.k1000.ivecs",
                }[role]
                link(ipath.resolve(), destination / alias)
                dalias = alias.replace(".ivecs", ".fvecs")
                link((common / f"{stem}.groundtruth.fvecs").resolve(), destination / dalias)
            builds.append({
                "seed": seed,
                "source_base": str(source_base.resolve()),
                "source_base_sha256": sha256(source_base.resolve()),
                "permutation_sha256": hashlib.sha256(permutation.tobytes()).hexdigest(),
                "files": build_files,
            })
        manifest["snapshots"][snapshot] = {"common_files": common_files, "builds": builds}

    manifest["elapsed_seconds"] = time.time() - started
    manifest_path = output / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "PASS", "dataset": args.dataset, "elapsed_seconds": manifest["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
