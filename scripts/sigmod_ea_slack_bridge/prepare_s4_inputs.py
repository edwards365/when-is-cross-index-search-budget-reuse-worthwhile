#!/usr/bin/env python3
"""Materialize frozen future queries and exact top-10 truth without ANN access."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import h5py
import numpy as np


DATA = {
    "sift_100k": ("data/raw/sift-128-euclidean.hdf5", "l2"),
    "arxiv_nomic_100k": ("data/raw/arxiv-nomic-768-normalized.hdf5", "ip"),
}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_vecs(path, array, dtype):
    array = np.ascontiguousarray(array, dtype=dtype)
    with path.open("wb") as f:
        dim = np.int32(array.shape[1])
        for row in array:
            f.write(dim.tobytes())
            f.write(row.tobytes())


def exact_top10(base, queries, metric, block=25):
    result = np.empty((len(queries), 10), dtype=np.int32)
    if metric == "l2":
        base_norm = np.sum(base * base, axis=1)
    for start in range(0, len(queries), block):
        q = queries[start : start + block]
        scores = q @ base.T
        if metric == "l2":
            values = np.sum(q * q, axis=1)[:, None] + base_norm[None, :] - 2.0 * scores
            idx = np.argpartition(values, 10, axis=1)[:, :10]
            local = np.take_along_axis(values, idx, axis=1)
            order = np.argsort(local, axis=1)
        else:
            idx = np.argpartition(-scores, 10, axis=1)[:, :10]
            local = np.take_along_axis(scores, idx, axis=1)
            order = np.argsort(-local, axis=1)
        result[start : start + len(q)] = np.take_along_axis(idx, order, axis=1)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    doc = json.loads(args.manifest.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    inventory = []
    for dataset, (relative, metric) in DATA.items():
        ids = doc["roles"][dataset]["fresh_source_certification_ids"] + doc["roles"][dataset]["fresh_target_evaluation_ids"]
        source = args.root / relative
        with h5py.File(source, "r") as f:
            base = np.asarray(f["train"][:100000], dtype=np.float32)
            order = np.argsort(ids)
            sorted_queries = np.asarray(f["train"][np.asarray(ids)[order]], dtype=np.float32)
            queries = sorted_queries[np.argsort(order)]
        if metric == "ip":
            base /= np.maximum(np.linalg.norm(base, axis=1, keepdims=True), np.finfo(np.float32).tiny)
            queries /= np.maximum(np.linalg.norm(queries, axis=1, keepdims=True), np.finfo(np.float32).tiny)
        truth = exact_top10(base, queries, metric)
        if any(int(source_id) in set(map(int, truth[i])) for i, source_id in enumerate(ids)):
            raise RuntimeError("fresh query self-match against 100K base")
        prefix = args.output / dataset
        np.save(prefix.with_suffix(".queries.npy"), queries)
        np.save(prefix.with_suffix(".truth.npy"), truth)
        write_vecs(prefix.with_suffix(".queries.fvecs"), queries, np.float32)
        write_vecs(prefix.with_suffix(".truth.ivecs"), truth, np.int32)
        id_path = prefix.with_suffix(".external_ids.json")
        id_path.write_text(json.dumps(ids) + "\n")
        for path in (
            prefix.with_suffix(".queries.npy"),
            prefix.with_suffix(".truth.npy"),
            prefix.with_suffix(".queries.fvecs"),
            prefix.with_suffix(".truth.ivecs"),
            id_path,
        ):
            inventory.append({"dataset": dataset, "path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)})
        del base, queries, truth
    (args.output / "input_inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print(json.dumps({"status": "COMPLETE", "files": len(inventory)}, indent=2))


if __name__ == "__main__":
    main()
