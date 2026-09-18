#!/usr/bin/env python3
"""Materialize frozen S9-4 query roles and exact truth after preregistration."""

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np


DATASETS = {
    "sift_100k": ("data/raw/sift-128-euclidean.hdf5", "l2"),
    "arxiv_nomic_100k": ("data/raw/arxiv-nomic-768-normalized.hdf5", "ip"),
}
ROLES = ["baseline_selection", "baseline_certification", "baseline_evaluation"]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_top10(base, queries, metric, block=25):
    result = np.empty((len(queries), 10), dtype=np.int32)
    base_norm = np.sum(base * base, axis=1) if metric == "l2" else None
    for start in range(0, len(queries), block):
        query = queries[start : start + block]
        products = query @ base.T
        if metric == "l2":
            values = np.sum(query * query, axis=1)[:, None] + base_norm[None, :] - 2 * products
            ids = np.argpartition(values, 10, axis=1)[:, :10]
            local = np.take_along_axis(values, ids, axis=1)
            order = np.argsort(local, axis=1)
        else:
            ids = np.argpartition(-products, 10, axis=1)[:, :10]
            local = np.take_along_axis(products, ids, axis=1)
            order = np.argsort(-local, axis=1)
        result[start : start + len(query)] = np.take_along_axis(ids, order, axis=1)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--roles", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    role_manifest = json.loads(args.roles.read_text(encoding="utf-8"))
    if prereg["status"] != "FROZEN_BEFORE_QUERY_VECTOR_TRUTH_RESPONSE_POLICY_OR_RUNTIME_ACCESS":
        raise RuntimeError("S9-4 preregistration gate failed")
    if role_manifest["status"] != "FROZEN_BEFORE_VECTOR_TRUTH_RESPONSE_OR_POLICY_ACCESS":
        raise RuntimeError("S9-4 role gate failed")
    if sha(args.roles) != prereg["query_role_manifest_sha256"]:
        raise RuntimeError("S9-4 role manifest hash drift")
    args.output.mkdir(parents=True, exist_ok=False)
    inventory, access = [], []
    for dataset, (relative, metric) in DATASETS.items():
        role = role_manifest["roles"][dataset]
        role_ids = {name: list(map(int, role[f"{name}_ids"])) for name in ROLES}
        ids = [value for name in ROLES for value in role_ids[name]]
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
        if any(source_id in set(map(int, truth[position])) for position, source_id in enumerate(ids)):
            raise RuntimeError("query self-match against 100K base")
        prefix = args.output / dataset
        paths = {
            "queries": prefix.with_suffix(".queries.npy"),
            "truth": prefix.with_suffix(".truth.npy"),
            "external_ids": prefix.with_suffix(".external_ids.json"),
        }
        np.save(paths["queries"], queries)
        np.save(paths["truth"], truth)
        paths["external_ids"].write_text(json.dumps({
            "role_order": ROLES,
            "role_offsets": {name: [position * 500, (position + 1) * 500] for position, name in enumerate(ROLES)},
            "external_ids": ids,
        }, indent=2) + "\n", encoding="utf-8")
        for label, path in paths.items():
            inventory.append({"dataset": dataset, "kind": label, "path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)})
        access.append({
            "dataset": dataset,
            "source": str(source),
            "members": ["train[:100000]", "train[frozen_S9_4_ids]"],
            "roles": {name: 500 for name in ROLES},
            "exact_truth_computed": True,
            "access_after_preregistration": True,
            "validation_dev_accessed": False,
            "formal_test_accessed": False,
        })
    (args.output / "input_inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    (args.output / "truth_access_log.json").write_text(json.dumps(access, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "datasets": len(access), "files": len(inventory)}))


if __name__ == "__main__":
    main()
