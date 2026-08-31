#!/usr/bin/env python3
"""Materialize train-only runtime buffers; never opens truth or sealed HDF5 members."""

from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
PRIMARY = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
RUNTIME = ROOT / "results/icba_cibs_stage1/runtime"
BASE_DIR = RUNTIME / "base"
ORDER_DIR = RUNTIME / "orders"
QUERY_DIR = RUNTIME / "queries"
RESULT = RUNTIME / "runtime_input_manifest.json"
PROJECTED_ADDITIONS = 3365465672
RESERVE = 5 * 1024**3

DATASETS = {
    "sift_100k": {
        "source": PRIMARY / "data/raw/sift-128-euclidean.hdf5",
        "dimensions": 128,
        "normalized": False,
        "base_sha256": "d0ad618c42429e9e2261e37e7ecaf042af58e47117ad62d5935457e129d0ab21",
    },
    "arxiv_nomic_100k": {
        "source": PRIMARY / "data/raw/arxiv-nomic-768-normalized.hdf5",
        "dimensions": 768,
        "normalized": True,
        "base_sha256": "9fc6c6e71329832643a6c1e57eecd32e632bf90b1a5a4bed83587dbab70de107",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def array_sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).view(np.uint8)).hexdigest()


def write_matrix(path: Path, array: np.ndarray) -> None:
    array = np.ascontiguousarray(array, dtype="<f4")
    with path.open("xb") as handle:
        handle.write(struct.pack("<QQ", *array.shape))
        handle.write(array.tobytes())


def write_order(path: Path, order: np.ndarray) -> None:
    order = np.ascontiguousarray(order, dtype="<u4")
    with path.open("xb") as handle:
        handle.write(struct.pack("<Q", order.size))
        handle.write(order.tobytes())


def gate() -> dict:
    stats = os.statvfs(ROOT)
    free = stats.f_bavail * stats.f_frsize
    required = PROJECTED_ADDITIONS + RESERVE
    if free < required:
        raise RuntimeError(
            f"INSUFFICIENT_RESOURCES_FOR_CIBS_STAGE1 free={free} required={required}"
        )
    return {"free_bytes": free, "required_bytes": required, "status": "PASS"}


def main() -> None:
    if RUNTIME.exists():
        raise RuntimeError(f"refusing to overwrite runtime inputs: {RUNTIME}")
    BASE_DIR.mkdir(parents=True)
    ORDER_DIR.mkdir()
    QUERY_DIR.mkdir()
    record = {
        "schema_version": 1,
        "status": "PASS_TRAIN_ONLY_RUNTIME_INPUT_MATERIALIZATION",
        "resource_gate": gate(),
        "hdf5_members_read": ["train"],
        "truth_members_read": [],
        "truth_artifacts_read": [],
        "datasets": {},
        "orders": {},
    }
    for dataset, spec in DATASETS.items():
        with h5py.File(spec["source"], "r") as handle:
            base = np.asarray(handle["train"][:100000], dtype=np.float32)
        if spec["normalized"]:
            base /= np.linalg.norm(base, axis=1, keepdims=True)
            base = np.asarray(base, dtype=np.float32)
        if base.shape != (100000, spec["dimensions"]):
            raise RuntimeError(f"base shape mismatch for {dataset}: {base.shape}")
        if array_sha256(base) != spec["base_sha256"]:
            raise RuntimeError(f"base content hash mismatch for {dataset}")
        base_path = BASE_DIR / f"{dataset}.f32bin"
        write_matrix(base_path, base)
        query_records = {}
        for role in ("cibs_design", "cibs_sentinel", "cibs_evaluation"):
            source = (
                ROOT
                / "results/icba_cibs_stage1/phase1/query_roles"
                / f"{dataset}__{role}__queries.npy"
            )
            queries = np.load(source, allow_pickle=False)
            query_path = QUERY_DIR / f"{dataset}__{role}.f32bin"
            write_matrix(query_path, queries)
            query_records[role] = {
                "source_npy": str(source.relative_to(ROOT)),
                "source_npy_sha256": sha256(source),
                "runtime_path": str(query_path.relative_to(ROOT)),
                "runtime_sha256": sha256(query_path),
                "shape": list(queries.shape),
            }
        record["datasets"][dataset] = {
            "source": str(spec["source"]),
            "source_member_read": "train",
            "base_array_sha256": spec["base_sha256"],
            "runtime_base_path": str(base_path.relative_to(ROOT)),
            "runtime_base_sha256": sha256(base_path),
            "shape": list(base.shape),
            "normalized": spec["normalized"],
            "queries": query_records,
        }
    for build_id in ("G1", "G2", "G3"):
        source = (
            ROOT
            / "results/icba_cibs_stage1/phase1/build_preregistration"
            / f"{build_id}__insertion_order.npy"
        )
        order = np.load(source, allow_pickle=False)
        path = ORDER_DIR / f"{build_id}.u32bin"
        write_order(path, order)
        record["orders"][build_id] = {
            "source_npy": str(source.relative_to(ROOT)),
            "source_npy_sha256": sha256(source),
            "runtime_path": str(path.relative_to(ROOT)),
            "runtime_sha256": sha256(path),
        }
    RESULT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": record["status"], "resource_gate": record["resource_gate"]}))


if __name__ == "__main__":
    main()
