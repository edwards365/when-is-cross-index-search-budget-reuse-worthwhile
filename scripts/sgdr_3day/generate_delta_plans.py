#!/usr/bin/env python3
"""Generate frozen 10%/5% SGDR delta plans from existing E0 evidence."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_edges(path: Path) -> list[tuple[int, int]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        return [(int(row["source"]), int(row["target"])) for row in csv.DictReader(stream)]


def read_plan(path: Path) -> list[tuple[int, int]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return [(int(row["source"]), int(row["target"])) for row in csv.DictReader(stream)]


def write_plan(path: Path, edges: list[tuple[int, int]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream); writer.writerow(["source", "target"]); writer.writerows(edges)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--e0", type=Path, default=Path("results/gb_mpcc/e0"))
    parser.add_argument("--output", type=Path, default=Path("results/sgdr_3day/delta_plans"))
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.mkdir(parents=True)
    records = []
    for dataset in ("sift_10k", "glove100_10k", "arxiv_nomic_10k"):
        for seed in (7, 17, 29):
            run_id = f"{dataset}-b{seed}"
            original = read_edges(args.e0 / "runs" / run_id / "original_algorithm4" / "layer0_edges.csv.gz")
            primary = read_edges(args.e0 / "runs" / run_id / "geometry_backbone_mpcc_R4" / "layer0_edges.csv.gz")
            original_set, primary_set = set(original), set(primary)
            candidates = primary_set - original_set
            source_plan = read_plan(args.e0 / "plans" / run_id / "geometry_backbone_mpcc_R4.csv")
            ranked, seen = [], set()
            for edge in source_plan:
                if edge in candidates and edge not in seen:
                    ranked.append(edge); seen.add(edge)
            ranked.extend(sorted(candidates - seen))
            if len(ranked) != len(candidates) or len(set(ranked)) != len(ranked):
                raise AssertionError(f"{run_id}: delta ranking is not a permutation")
            directory = args.output / run_id; directory.mkdir()
            budgets = {}
            for fraction, name in ((0.05, "delta_5pct.csv"), (0.10, "delta_10pct.csv")):
                count = min(len(ranked), math.floor(fraction * len(original_set)))
                path = directory / name; write_plan(path, ranked[:count])
                budgets[str(fraction)] = {"edges": count, "sha256": sha256(path),
                    "fraction_of_original_directed_edges": count / len(original_set)}
            record = {"run_id": run_id, "dataset": dataset, "build_seed": seed,
                "original_directed_edges": len(original_set), "r4_directed_edges": len(primary_set),
                "candidate_delta_edges": len(candidates),
                "source_plan_prioritized_candidates": len(seen), "budgets": budgets,
                "original_edges_deleted": 0, "new_graphs_built": False,
                "validation_dev_accessed": False, "formal_test_members_accessed": False}
            (directory / "metadata.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            records.append(record); print(json.dumps(record, sort_keys=True))
    summary = {"status": "SGDR_DELTA_PLANS_COMPLETE", "runs": 9,
        "ranking": "R4_source_plan_order_then_stable_directed_edge_id",
        "budgets": [0.05, 0.10], "original_edges_deleted": 0,
        "new_graphs_built": False, "validation_dev_accessed": False,
        "formal_test_members_accessed": False, "records": records}
    (args.output / "matrix_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
