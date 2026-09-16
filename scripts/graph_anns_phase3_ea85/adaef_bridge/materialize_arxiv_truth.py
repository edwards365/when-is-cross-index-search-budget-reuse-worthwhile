#!/usr/bin/env python3
"""Materialize frozen Arxiv-100K queries and exact IP truth for Ada-ef roles."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import faiss
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
    parser.add_argument("--hdf5", type=Path, required=True)
    parser.add_argument("--roles", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--index-size", type=int, default=100_000)
    parser.add_argument("--k", type=int, default=100)
    parser.add_argument("--threads", type=int, default=32)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    faiss.omp_set_num_threads(args.threads)

    started = time.time()
    with h5py.File(args.hdf5, "r") as source:
        data = np.ascontiguousarray(source["train"][: args.index_size], dtype=np.float32)
        norms = np.linalg.norm(data, axis=1)
        if not np.allclose(norms, 1.0, atol=2e-4):
            raise RuntimeError("registered normalized Arxiv data are not unit norm")

        index = faiss.IndexFlatIP(data.shape[1])
        index.add(data)
        entries: dict[str, dict[str, object]] = {}
        for role in ("design", "certification", "evaluation"):
            ids_path = args.roles / f"arxiv_nomic_100k__adaef_{role}_source_ids.npy"
            ids = np.load(ids_path, allow_pickle=False)
            queries = np.ascontiguousarray(source["train"][ids], dtype=np.float32)
            distances, neighbors = index.search(queries, args.k)
            q_path = args.output / f"arxiv_nomic_100k__adaef_{role}_queries.npy"
            n_path = args.output / f"arxiv_nomic_100k__adaef_{role}_truth.npy"
            d_path = args.output / f"arxiv_nomic_100k__adaef_{role}_truth_distances.npy"
            np.save(q_path, queries, allow_pickle=False)
            np.save(n_path, neighbors.astype(np.int64, copy=False), allow_pickle=False)
            np.save(d_path, distances.astype(np.float32, copy=False), allow_pickle=False)
            entries[role] = {
                "queries": {"path": q_path.name, "shape": list(queries.shape), "sha256": sha256(q_path)},
                "truth": {"path": n_path.name, "shape": list(neighbors.shape), "sha256": sha256(n_path)},
                "truth_distances": {"path": d_path.name, "shape": list(distances.shape), "sha256": sha256(d_path)},
            }

    manifest = {
        "schema_version": "ea85-adaef-arxiv-truth-1.0",
        "status": "FROZEN_EXACT_TRUTH",
        "metric": "inner_product_on_unit_normalized_vectors",
        "index_membership": f"train rows [0, {args.index_size})",
        "k": args.k,
        "faiss_version": faiss.__version__,
        "threads": args.threads,
        "elapsed_seconds": time.time() - started,
        "roles": entries,
        "access_policy": {
            "design": "authorized for Ada-ef estimator/action construction",
            "certification": "authorized only after the action table is frozen",
            "evaluation": "sealed until the certified deployment policy is frozen",
        },
    }
    manifest_path = args.output / "arxiv_nomic_100k__adaef_truth_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
