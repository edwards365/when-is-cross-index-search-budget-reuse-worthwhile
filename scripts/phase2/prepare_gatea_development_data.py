#!/usr/bin/env python
"""Create distinct 100K Gate-A development queries and exact top-k truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))

from narhnsw.ground_truth import exact_top_k  # noqa: E402

from scripts.experiments.run_phase2_selector_audit import sha256  # noqa: E402


def array_sha256(values: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(np.ascontiguousarray(values).view(np.uint8))
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("raw output directory exists and will not be overwritten")
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True)
    receipts = []
    started = time.perf_counter()

    for dataset_index, manifest_name in enumerate(config["datasets"]):
        manifest = yaml.safe_load((REPO / manifest_name).read_text(encoding="utf-8"))
        source = REPO / manifest["local_path"]
        if sha256(source) != manifest["sha256"]:
            raise ValueError(f"dataset checksum mismatch: {manifest['name']}")
        required = (
            config["base_vectors"] + config["query_sampling_pool"]
        )
        with h5py.File(source, "r") as handle:
            if len(handle["train"]) < required:
                raise ValueError("train member is too small for the frozen development split")
            pool = np.asarray(handle["train"][:required], dtype=np.float32)
        angular = str(manifest["distance"]).startswith("angular")
        if angular:
            norms = np.linalg.norm(pool, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise ValueError("angular train member contains a zero vector")
            pool /= norms
        base = np.ascontiguousarray(pool[: config["base_vectors"]])
        query_pool = pool[config["base_vectors"] :]
        rng = np.random.default_rng(config["query_seed"] + dataset_index)
        offsets = np.sort(
            rng.choice(
                len(query_pool), size=config["development_queries"], replace=False
            )
        )
        queries = np.ascontiguousarray(query_pool[offsets])
        base_rows = {row.tobytes() for row in base}
        if any(row.tobytes() in base_rows for row in queries):
            raise RuntimeError("sampled development query duplicates a base vector")
        truth_started = time.perf_counter()
        labels, distances = exact_top_k(
            base,
            queries,
            config["k"],
            metric="angular" if angular else "l2",
            query_batch=config["query_batch"],
            base_batch=config["base_batch"],
        )
        truth_seconds = time.perf_counter() - truth_started
        safe_name = manifest["name"].replace("/", "_")
        np.save(args.output / f"{safe_name}_queries.npy", queries, allow_pickle=False)
        np.save(args.output / f"{safe_name}_ground_truth.npy", labels, allow_pickle=False)
        np.save(
            args.output / f"{safe_name}_ground_truth_distances.npy",
            distances,
            allow_pickle=False,
        )
        source_ids = config["base_vectors"] + offsets
        np.save(args.output / f"{safe_name}_query_source_ids.npy", source_ids, allow_pickle=False)
        receipts.append(
            {
                "dataset": manifest["name"],
                "source_sha256": manifest["sha256"],
                "distance_protocol": (
                    "float64 one-minus-inner-product on L2-normalized vectors"
                    if angular
                    else "float64 squared Euclidean"
                ),
                "base_sha256": array_sha256(base),
                "queries_sha256": array_sha256(queries),
                "ground_truth_sha256": array_sha256(labels),
                "query_source_ids_sha256": array_sha256(source_ids),
                "truth_seconds": truth_seconds,
            }
        )

    (args.output / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    metadata = {
        "run_id": config["run_id"],
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "formal_test_members_accessed": False,
        "receipts": receipts,
        "total_seconds": time.perf_counter() - started,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
