#!/usr/bin/env python
"""Verify frozen Gate-A development inputs without touching formal HDF5 members."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))

from narhnsw.firewall import read_hdf5_rows  # noqa: E402
from narhnsw.ground_truth import exact_top_k  # noqa: E402


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def array_sha256(values: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(np.ascontiguousarray(values).view(np.uint8))
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if config["formal"] or config["firewall"] != "sealed":
        raise PermissionError("Gate-A preflight requires a sealed development config")
    if config["enabled_hdf5_members"] != ["train"]:
        raise PermissionError("Gate-A development config may enable only train")

    rows = []
    sample_rng = np.random.default_rng(20260824)
    for dataset_id, dataset in config["datasets"].items():
        source = REPO / dataset["source"]
        if file_sha256(source) != dataset["source_sha256"]:
            raise ValueError(f"source checksum mismatch: {dataset_id}")
        base = read_hdf5_rows(
            source,
            dataset["source_member"],
            slice(0, config["base_vectors"]),
            role="construction",
        ).astype(np.float32, copy=False)
        query_source_ids = np.load(REPO / dataset["query_source_ids"], allow_pickle=False)
        source_rows = read_hdf5_rows(
            source,
            dataset["source_member"],
            slice(int(query_source_ids.min()), int(query_source_ids.max()) + 1),
            role="development",
        ).astype(np.float32, copy=False)
        queries = np.load(REPO / dataset["queries"], allow_pickle=False)
        truth = np.load(REPO / dataset["ground_truth"], allow_pickle=False)
        truth_distances = np.load(
            REPO / dataset["ground_truth_distances"], allow_pickle=False
        )
        if dataset["normalized"]:
            base /= np.linalg.norm(base, axis=1, keepdims=True)
            source_rows /= np.linalg.norm(source_rows, axis=1, keepdims=True)
        reconstructed_queries = source_rows[
            query_source_ids.astype(np.int64) - int(query_source_ids.min())
        ]
        if not np.array_equal(reconstructed_queries, queries):
            raise ValueError(f"query/source mismatch: {dataset_id}")
        if array_sha256(base) != dataset["base_content_sha256"]:
            raise ValueError(f"base content mismatch: {dataset_id}")
        for key in (
            "queries",
            "ground_truth",
            "ground_truth_distances",
            "query_source_ids",
        ):
            if file_sha256(REPO / dataset[key]) != dataset[f"{key}_sha256"]:
                raise ValueError(f"derived checksum mismatch: {dataset_id}/{key}")
        if base.shape != (config["base_vectors"], dataset["dimensions"]):
            raise ValueError(f"base shape mismatch: {dataset_id}")
        if queries.shape != (config["development_queries"], dataset["dimensions"]):
            raise ValueError(f"query shape mismatch: {dataset_id}")
        if truth.shape != (config["development_queries"], config["k"]):
            raise ValueError(f"truth shape mismatch: {dataset_id}")
        if np.any(query_source_ids < config["base_vectors"]):
            raise ValueError(f"query ID overlaps base range: {dataset_id}")
        base_bytes = {row.tobytes() for row in base}
        if any(row.tobytes() in base_bytes for row in queries):
            raise ValueError(f"query vector duplicates base: {dataset_id}")
        sample = np.sort(sample_rng.choice(len(queries), size=8, replace=False))
        sample_truth, sample_distances = exact_top_k(
            base,
            queries[sample],
            config["k"],
            metric="angular" if dataset["normalized"] else "l2",
            query_batch=4,
            base_batch=10_000,
        )
        if not np.array_equal(sample_truth, truth[sample]):
            raise ValueError(f"sample truth mismatch: {dataset_id}")
        if not np.allclose(sample_distances, truth_distances[sample], rtol=0, atol=1e-12):
            raise ValueError(f"sample truth-distance mismatch: {dataset_id}")
        rows.append(
            {
                "dataset": dataset_id,
                "base_shape": list(base.shape),
                "base_dtype": str(base.dtype),
                "query_shape": list(queries.shape),
                "query_dtype": str(queries.dtype),
                "truth_shape": list(truth.shape),
                "truth_dtype": str(truth.dtype),
                "query_source_min": int(query_source_ids.min()),
                "query_source_max": int(query_source_ids.max()),
                "base_id_overlap": False,
                "base_vector_duplicate": False,
                "sample_truth_queries_recomputed": len(sample),
                "sample_truth_exact_match": True,
                "accessed_hdf5_members": ["train"],
                "formal_members_accessed": False,
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"datasets": rows}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"datasets": rows}, indent=2))


if __name__ == "__main__":
    main()
