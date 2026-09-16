#!/usr/bin/env python3
"""Bundle frozen Arxiv-100K Ada-ef inputs for the C++ bridge."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--index-size", type=int, default=100_000)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(args.source, "r") as source, h5py.File(args.output, "w") as bundle:
        train = source["train"][: args.index_size]
        # Keep the bridge bundle filter-free: the isolated C++ HDF5 runtime does
        # not load h5py's dynamically provided LZF plugin.
        bundle.create_dataset("train", data=train, chunks=(256, train.shape[1]))
        for role in ("design", "certification", "evaluation"):
            queries = np.load(args.frozen / f"arxiv_nomic_100k__adaef_{role}_queries.npy", allow_pickle=False)
            truth = np.load(args.frozen / f"arxiv_nomic_100k__adaef_{role}_truth.npy", allow_pickle=False)
            bundle.create_dataset(f"{role}_queries", data=queries, chunks=(128, queries.shape[1]))
            bundle.create_dataset(f"{role}_truth", data=truth.astype(np.int32), chunks=True)
        bundle.attrs["metric"] = "inner_product_on_unit_normalized_vectors"
        bundle.attrs["index_size"] = args.index_size
        bundle.attrs["scientific_target"] = "Recall@10 >= 0.95"

    info = {
        "schema_version": "ea85-adaef-arxiv-input-bundle-1.0",
        "status": "FROZEN_BEFORE_SCIENTIFIC_RESULTS",
        "path": str(args.output),
        "bytes": args.output.stat().st_size,
        "sha256": sha256(args.output),
        "datasets": {
            "train": [100_000, 768],
            "design_queries": [2_000, 768],
            "design_truth": [2_000, 100],
            "certification_queries": [500, 768],
            "certification_truth": [500, 100],
            "evaluation_queries": [1_000, 768],
            "evaluation_truth": [1_000, 100],
        },
        "evaluation_access": "sealed until certified policy is frozen",
    }
    manifest = args.output.with_suffix(args.output.suffix + ".manifest.json")
    manifest.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n")
    print(json.dumps(info, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
