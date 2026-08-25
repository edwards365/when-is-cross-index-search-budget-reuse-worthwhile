#!/usr/bin/env python3
"""Compute the frozen OCGT-v3 exact k=100 MLE-LID insertion orders at 100K."""
import hashlib
import json
import os
from pathlib import Path

import h5py
import numpy as np
import yaml

ROOT = Path("/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k")
MAIN = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
OUT = ROOT / "results/hardness_portability_100k/lid_orders"
STOP_BYTES = 10 * 1024**3


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def free_bytes() -> int:
    stat = os.statvfs(ROOT)
    return stat.f_bavail * stat.f_frsize


def exact_lid_order(x: np.ndarray, batch: int = 128, k: int = 100):
    n = len(x)
    norms = np.einsum("ij,ij->i", x, x)
    lid = np.empty(n, dtype=np.float64)
    for start in range(0, n, batch):
        stop = min(start + batch, n)
        block = x[start:stop]
        distances = (
            np.einsum("ij,ij->i", block, block)[:, None]
            + norms[None, :]
            - 2.0 * (block @ x.T)
        )
        distances = np.maximum(distances, 0.0)
        distances[np.arange(stop - start), np.arange(start, stop)] = np.inf
        nearest = np.partition(distances, k - 1, axis=1)[:, :k]
        radius = np.max(nearest, axis=1, keepdims=True)
        ratios = np.clip(nearest / np.maximum(radius, 1e-30), 1e-30, 1.0)
        denom = np.log(ratios).sum(axis=1)
        lid[start:stop] = np.where(denom < 0, -k / denom, np.inf)
        if start % (batch * 40) == 0:
            print(json.dumps({"completed": stop, "total": n}), flush=True)
    order = np.lexsort((np.arange(n, dtype=np.int64), lid))
    return lid, order.astype(np.uint32)


def main():
    if OUT.exists():
        raise RuntimeError(f"refusing to overwrite {OUT}")
    if free_bytes() < STOP_BYTES:
        raise RuntimeError("disk below 10 GiB stop line")
    OUT.mkdir(parents=True)
    cfg = yaml.safe_load((ROOT / "configs/gate_a/gate_a_100k.yaml").read_text())
    records = []
    for key in ["sift_100k", "glove100_100k", "arxiv_nomic_100k"]:
        d = cfg["datasets"][key]
        with h5py.File(MAIN / d["source"], "r") as handle:
            base = np.asarray(handle["train"][:100000], dtype=np.float32)
        if d["normalized"]:
            base /= np.linalg.norm(base, axis=1, keepdims=True)
        lid, order = exact_lid_order(base)
        lid_path = OUT / f"{key}_lid.npy"
        order_path = OUT / f"{key}_order.npy"
        np.save(lid_path, lid, allow_pickle=False)
        np.save(order_path, order, allow_pickle=False)
        records.append({
            "dataset": key,
            "definition": "OCGT-v3 exact squared-L2 k=100 MLE LID",
            "tie_break": "ascending external label",
            "lid_path": str(lid_path.relative_to(ROOT)),
            "lid_sha256": file_sha(lid_path),
            "order_path": str(order_path.relative_to(ROOT)),
            "order_sha256": file_sha(order_path),
            "count": 100000,
        })
        del base, lid, order
    manifest = {
        "schema_version": 1,
        "protocol": "Query Hardness Is Not Portable 100K",
        "status": "FROZEN_BEFORE_GATE_R",
        "uses_queries_or_truth": False,
        "records": records,
        "formal_test_accessed": False,
    }
    path = ROOT / "manifests/hardness_portability_100k/lid_order_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"completed": [r["dataset"] for r in records]}, indent=2))


if __name__ == "__main__":
    main()
