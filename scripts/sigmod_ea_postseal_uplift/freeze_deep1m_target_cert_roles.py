#!/usr/bin/env python3
"""Materialize the preregistered Deep1M fresh-query role IDs without data access."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def ids_sha(ids):
    return hashlib.sha256(np.asarray(ids, dtype="<i8").tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prior_scale = set(json.loads(args.prior_manifest.read_text(encoding="utf-8"))["query_ids"])
    prior_p10 = set(np.sort(np.random.RandomState(991).choice(10000, 500, replace=False)).tolist())
    available = np.asarray(sorted(set(range(10000)) - prior_scale - prior_p10), dtype=np.int64)
    selected = np.random.default_rng(3991).choice(available, 1500, replace=False)
    roles = {
        "source_design": sorted(map(int, selected[:500])),
        "target_certification": sorted(map(int, selected[500:1000])),
        "target_evaluation": sorted(map(int, selected[1000:])),
    }
    overlaps = {}
    names = list(roles)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            overlaps[f"{left}__{right}"] = len(set(roles[left]) & set(roles[right]))
    overlaps["new__prior_scale"] = len(set(selected) & prior_scale)
    overlaps["new__prior_p10"] = len(set(selected) & prior_p10)
    result = {
        "status": "FROZEN_BEFORE_VECTOR_TRUTH_OR_SEARCH_ACCESS",
        "universe_size": 10000,
        "seed": 3991,
        "roles": roles,
        "role_sha256": {name: ids_sha(ids) for name, ids in roles.items()},
        "overlap_counts": overlaps,
    }
    if any(overlaps.values()) or any(len(ids) != 500 for ids in roles.values()):
        raise RuntimeError("query firewall failure")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        old = json.loads(args.output.read_text(encoding="utf-8"))
        if old != result:
            raise RuntimeError("frozen role manifest drift")
    else:
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "overlaps": overlaps, "role_sha256": result["role_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
