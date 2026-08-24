#!/usr/bin/env python3
"""Independently audit the frozen Graph Gate E0 treatment-plan matrix."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from itertools import groupby
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_events(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        rows = (row for row in csv.DictReader(stream) if int(row["layer"]) == 0)
        for source, group in groupby(rows, key=lambda row: int(row["insertion_id"])):
            event = list(group)
            candidates = [int(row["candidate_id"]) for row in event]
            accepted = {int(row["candidate_id"]) for row in event if row["decision"] == "accepted"}
            algorithm4 = tuple(item for item in candidates if item in accepted)
            yield source, candidates, algorithm4


def read_plan(path: Path) -> dict[int, tuple[int, ...]]:
    result: dict[int, list[int]] = {}
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            result.setdefault(int(row["source"]), []).append(int(row["target"]))
    return {source: tuple(targets) for source, targets in result.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_e0.yaml"))
    parser.add_argument("--plans", type=Path, default=Path("results/gb_mpcc/e0/plans"))
    parser.add_argument("--raw", type=Path, default=Path("results/gb_mpcc/r0_candidates"))
    parser.add_argument("--original-audits", type=Path, default=Path("results/gb_mpcc/e0/audits"))
    args = parser.parse_args()

    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if protocol["firewall"]["formal_test_access"] != "forbidden":
        raise PermissionError("formal-test firewall is open")
    expected_methods = set(protocol["execution"]["methods_order"]) - {"original_algorithm4"}
    run_summaries = []
    total_edges = 0
    for dataset in protocol["execution"]["datasets_order"]:
        for seed in protocol["execution"]["seeds_order"]:
            run_id = f"{dataset}-b{seed}"
            directory = args.plans / run_id
            metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
            if metadata["status"] != "complete" or metadata["formal_test_members_accessed"]:
                raise ValueError(f"{run_id}: invalid completion or firewall metadata")
            if set(metadata["methods"]) != expected_methods:
                raise ValueError(f"{run_id}: method matrix differs from preregistration")
            plans = {method: read_plan(directory / f"{method}.csv") for method in expected_methods}
            changed = {method: 0 for method in expected_methods}
            edge_counts = {method: 0 for method in expected_methods}
            events = 0
            for source, candidates, algorithm4 in candidate_events(
                args.raw / run_id / "insertion_candidates.csv.gz"
            ):
                candidate_set = set(candidates)
                for method, plan in plans.items():
                    selected = plan.get(source)
                    if selected is None:
                        raise ValueError(f"{run_id}/{method}: missing source {source}")
                    if len(selected) != len(algorithm4) or len(set(selected)) != len(selected):
                        raise ValueError(f"{run_id}/{method}/{source}: budget or uniqueness")
                    if not set(selected) <= candidate_set:
                        raise ValueError(f"{run_id}/{method}/{source}: outside candidate pool")
                    if "backbone" in method:
                        radius = int(method.rsplit("R", 1)[1])
                        backbone = algorithm4[: max(0, len(algorithm4) - radius)]
                        if selected[: len(backbone)] != backbone:
                            raise ValueError(f"{run_id}/{method}/{source}: backbone mismatch")
                    edge_counts[method] += len(selected)
                    changed[method] += set(selected) != set(algorithm4)
                events += 1
            if events != 9999 or any(len(plan) != events for plan in plans.values()):
                raise ValueError(f"{run_id}: source matrix is incomplete")
            if edge_counts != metadata["edge_counts"]:
                raise ValueError(f"{run_id}: edge-count metadata mismatch")
            if changed != metadata["changed_events_vs_algorithm4"]:
                raise ValueError(f"{run_id}: change-count metadata mismatch")
            for method in expected_methods:
                if sha256(directory / f"{method}.csv") != metadata["plan_sha256"][method]:
                    raise ValueError(f"{run_id}/{method}: plan checksum mismatch")
            original = json.loads(
                (
                    args.original_audits / f"{run_id}-original" / "original_reproduction_audit.json"
                ).read_text(encoding="utf-8")
            )
            if not original["original_exact_reproduction"]:
                raise ValueError(f"{run_id}: Original reproduction did not pass")
            total_edges += sum(edge_counts.values())
            run_summaries.append(
                {
                    "run": run_id,
                    "events": events,
                    "methods": len(plans),
                    "plan_edges": sum(edge_counts.values()),
                    "original_exact_reproduction": True,
                }
            )
            print(json.dumps(run_summaries[-1], sort_keys=True), flush=True)
    summary = {
        "status": "PASS",
        "runs": len(run_summaries),
        "treatment_plans": len(run_summaries) * len(expected_methods),
        "total_plan_edges": total_edges,
        "all_candidate_membership_valid": True,
        "all_budgets_valid": True,
        "all_backbones_valid": True,
        "all_plan_hashes_valid": True,
        "all_original_reproductions_exact": True,
        "query_independent": True,
        "formal_test_members_accessed": False,
        "e1_authorized": False,
        "runs_detail": run_summaries,
    }
    (args.plans / "matrix_audit.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
