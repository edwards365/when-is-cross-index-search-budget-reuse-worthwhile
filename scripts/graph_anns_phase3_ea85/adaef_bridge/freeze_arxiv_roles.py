#!/usr/bin/env python3
"""Freeze Ada-ef Arxiv-100K query roles before any scientific run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--population", type=int, default=1_344_643)
    parser.add_argument("--index-size", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=991)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    candidate_ids = np.arange(args.index_size, args.population, dtype=np.int64)
    chosen = rng.choice(candidate_ids, size=3_500, replace=False)
    roles = {
        "design": np.sort(chosen[:2_000]),
        "certification": np.sort(chosen[2_000:2_500]),
        "evaluation": np.sort(chosen[2_500:3_500]),
    }

    sets = {name: set(values.tolist()) for name, values in roles.items()}
    overlap = {
        f"{left}__{right}": len(sets[left] & sets[right])
        for left in roles
        for right in roles
        if left < right
    }
    if any(overlap.values()):
        raise RuntimeError(f"query-role overlap: {overlap}")

    files: dict[str, dict[str, object]] = {}
    for role, values in roles.items():
        path = args.output / f"arxiv_nomic_100k__adaef_{role}_source_ids.npy"
        np.save(path, values, allow_pickle=False)
        files[role] = {
            "path": path.name,
            "count": int(values.size),
            "min_source_id": int(values.min()),
            "max_source_id": int(values.max()),
            "sha256": sha256(path),
        }

    manifest = {
        "schema_version": "ea85-adaef-arxiv-query-roles-1.0",
        "status": "FROZEN_BEFORE_SCIENTIFIC_RESULTS",
        "dataset": "arxiv_nomic_100k",
        "index_membership": "raw train rows [0, 100000)",
        "query_population": "raw train rows [100000, 1344643)",
        "seed": args.seed,
        "roles": files,
        "pairwise_overlap": overlap,
        "evaluation_policy": "Evaluation IDs and truth cannot affect estimator, action table, certification, or fallback selection.",
    }
    manifest_path = args.output / "arxiv_nomic_100k__adaef_query_role_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
