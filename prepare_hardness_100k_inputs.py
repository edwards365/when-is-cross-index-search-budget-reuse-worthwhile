#!/usr/bin/env python3
"""Freeze independent 100K scale-dev queries and exact top-10 evidence."""
import hashlib
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import yaml

ROOT = Path("/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k")
MAIN = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
sys.path.insert(0, str(ROOT / "python"))
from narhnsw.ground_truth import exact_top_k

SELECTION_SEED = 20260915
SPLIT_SEED = 20260915
BASE_SIZE = 100000
QUERY_COUNT = 1000
OUT = ROOT / "results/hardness_portability_100k/query_inputs"
MAN = ROOT / "manifests/hardness_portability_100k"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector_hashes(array: np.ndarray) -> list[str]:
    return [hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest() for v in array]


def main() -> None:
    if OUT.exists():
        raise RuntimeError(f"refusing to overwrite frozen output directory: {OUT}")
    OUT.mkdir(parents=True)
    cfg = yaml.safe_load((ROOT / "configs/gate_a/gate_a_100k.yaml").read_text())
    datasets = ["sift_100k", "glove100_100k", "arxiv_nomic_100k"]
    records = []
    for offset, key in enumerate(datasets):
        d = cfg["datasets"][key]
        source = MAIN / d["source"]
        old_design_ids = np.load(MAIN / d["query_source_ids"], allow_pickle=False).astype(np.int64)
        with h5py.File(source, "r") as f:
            train_count, dimensions = f["train"].shape
            pool = np.setdiff1d(
                np.arange(BASE_SIZE, train_count, dtype=np.int64),
                old_design_ids,
                assume_unique=False,
            )
            rng = np.random.default_rng(SELECTION_SEED + offset)
            if pool.size < QUERY_COUNT:
                raise RuntimeError(f"{key}: only {pool.size} legal train candidates")
            ids = np.sort(rng.choice(pool, QUERY_COUNT, replace=False))
            queries = np.asarray(f["train"][ids], dtype=np.float32)
            base = np.asarray(f["train"][:BASE_SIZE], dtype=np.float32)
        if d["normalized"]:
            queries /= np.linalg.norm(queries, axis=1, keepdims=True)
            base /= np.linalg.norm(base, axis=1, keepdims=True)
        query_hashes = vector_hashes(queries)
        base_hashes = set(vector_hashes(base))
        if len(set(query_hashes)) != QUERY_COUNT or any(h in base_hashes for h in query_hashes):
            raise RuntimeError(f"{key}: duplicate or base/query overlap")
        truth, distances = exact_top_k(base, queries, 10, metric="l2")
        paths = {
            "queries": OUT / f"{key}_queries.npy",
            "truth": OUT / f"{key}_truth.npy",
            "truth_distances": OUT / f"{key}_truth_distances.npy",
            "source_ids": OUT / f"{key}_source_ids.npy",
        }
        for name, array in [
            ("queries", queries),
            ("truth", truth.astype(np.uint32)),
            ("truth_distances", distances.astype(np.float64)),
            ("source_ids", ids),
        ]:
            np.save(paths[name], array, allow_pickle=False)
        records.append({
            "dataset": key,
            "source_path": d["source"],
            "source_sha256": d["source_sha256"],
            "source_member": "train",
            "train_count": int(train_count),
            "base_source_ids": [0, BASE_SIZE - 1],
            "base_size": BASE_SIZE,
            "base_content_sha256": d["base_content_sha256"],
            "selection_seed": SELECTION_SEED,
            "seed_offset": offset,
            "legal_pool_rule": "train ids >=100000 excluding frozen Gate-A design source ids",
            "excluded_gate_a_design_count": int(np.isin(old_design_ids, ids).sum()),
            "ocgt_v3_overlap_impossible_by_range": True,
            "query_count": QUERY_COUNT,
            "dimensions": int(dimensions),
            "normalized": bool(d["normalized"]),
            "query_hashes": query_hashes,
            **{f"{name}_path": str(path.relative_to(ROOT)) for name, path in paths.items()},
            **{f"{name}_sha256": sha(path) for name, path in paths.items()},
            "unique_queries": True,
            "base_overlap_count": 0,
            "gate_a_design_source_id_overlap_count": 0,
            "formal_test_accessed": False,
        })
        del base, queries, truth, distances

    rng = np.random.default_rng(SPLIT_SEED)
    perm = rng.permutation(QUERY_COUNT)
    split = {
        "train_design": sorted(map(int, perm[:250])),
        "internal_test": sorted(map(int, perm[250:])),
    }
    membership = {
        "schema_version": 1,
        "protocol": "Query Hardness Is Not Portable 100K",
        "status": "FROZEN_SCALE_DEV_MEMBERSHIP",
        "datasets": records,
        "selection_seed": SELECTION_SEED,
        "same_frozen_train_parent_as_base": True,
        "ocgt_v2_v3_queries_excluded": True,
        "formal_test_accessed": False,
    }
    split_doc = {
        "schema_version": 1,
        "protocol": "Query Hardness Is Not Portable 100K",
        "seed": SPLIT_SEED,
        "rng": "numpy.random.Generator(PCG64)",
        "permutation_sha256": hashlib.sha256(np.asarray(perm, dtype="<u4").tobytes()).hexdigest(),
        "splits": split,
        "same_ids_across_graphs": True,
        "outcome_independent_materialization": True,
    }
    (MAN / "data_query_truth_manifest.json").write_text(json.dumps(membership, indent=2) + "\n")
    (MAN / "query_split.json").write_text(json.dumps(split_doc, indent=2) + "\n")
    print(json.dumps({"datasets": [{"dataset": r["dataset"], "queries": r["queries_sha256"], "truth": r["truth_sha256"]} for r in records], "split": {k: len(v) for k, v in split.items()}}, indent=2))


if __name__ == "__main__":
    main()
