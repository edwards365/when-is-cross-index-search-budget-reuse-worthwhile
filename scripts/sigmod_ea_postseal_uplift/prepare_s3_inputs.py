#!/usr/bin/env python3
"""Materialize S3 query roles and exact truth after preregistration."""

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np


DATA = {
    "sift_100k": ("data/raw/sift-128-euclidean.hdf5", "l2"),
    "arxiv_nomic_100k": ("data/raw/arxiv-nomic-768-normalized.hdf5", "ip"),
}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def exact_top10(base, queries, metric, block=25):
    result = np.empty((len(queries), 10), dtype=np.int32)
    base_norm = np.sum(base * base, axis=1) if metric == "l2" else None
    for start in range(0, len(queries), block):
        query = queries[start : start + block]
        scores = query @ base.T
        if metric == "l2":
            values = np.sum(query * query, axis=1)[:, None] + base_norm[None, :] - 2 * scores
            ids = np.argpartition(values, 10, axis=1)[:, :10]
            local = np.take_along_axis(values, ids, axis=1)
            order = np.argsort(local, axis=1)
        else:
            ids = np.argpartition(-scores, 10, axis=1)[:, :10]
            local = np.take_along_axis(scores, ids, axis=1)
            order = np.argsort(-local, axis=1)
        result[start : start + len(query)] = np.take_along_axis(ids, order, axis=1)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest["status"] != "PREREGISTERED_BEFORE_QUERY_OR_TRUTH_ACCESS":
        raise RuntimeError("S3 preregistration gate failed")
    args.output.mkdir(parents=True, exist_ok=False)
    inventory = []
    access = []
    for dataset, (relative, metric) in DATA.items():
        role = manifest["roles"][dataset]
        cert = list(map(int, role["target_certification_ids"]))
        evaluation = list(map(int, role["target_evaluation_ids"]))
        ids = cert + evaluation
        source = args.root / relative
        with h5py.File(source, "r") as handle:
            base = np.asarray(handle["train"][:100000], dtype=np.float32)
            order = np.argsort(ids)
            sorted_queries = np.asarray(handle["train"][np.asarray(ids)[order]], dtype=np.float32)
            queries = sorted_queries[np.argsort(order)]
        if metric == "ip":
            tiny = np.finfo(np.float32).tiny
            base /= np.maximum(np.linalg.norm(base, axis=1, keepdims=True), tiny)
            queries /= np.maximum(np.linalg.norm(queries, axis=1, keepdims=True), tiny)
        truth = exact_top10(base, queries, metric)
        if any(source_id in set(map(int, truth[i])) for i, source_id in enumerate(ids)):
            raise RuntimeError("query self-match against 100K base")
        prefix = args.output / dataset
        np.save(prefix.with_suffix(".queries.npy"), queries)
        np.save(prefix.with_suffix(".truth.npy"), truth)
        id_path = prefix.with_suffix(".external_ids.json")
        id_path.write_text(json.dumps(ids) + "\n", encoding="utf-8")
        for path in (prefix.with_suffix(".queries.npy"), prefix.with_suffix(".truth.npy"), id_path):
            inventory.append({"dataset": dataset, "path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)})
        access.append({
            "dataset": dataset,
            "source": str(source),
            "members": ["train[:100000]", "train[frozen_S2_ids]"],
            "target_certification_queries": 500,
            "target_evaluation_queries": 500,
            "exact_truth_computed": True,
            "access_after_preregistration": True,
        })
    (args.output / "input_inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    (args.output / "truth_access_log.json").write_text(json.dumps(access, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "files": len(inventory), "datasets": len(access)}))


if __name__ == "__main__":
    main()
