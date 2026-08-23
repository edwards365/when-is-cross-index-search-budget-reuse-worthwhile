#!/usr/bin/env python
"""Verify that a regenerated plan prefix matches resumable Gate-A shards."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

AUDIT_FIELDS = [
    "center",
    "method",
    "swap_steps",
    "terminal_changed_edges",
    "geometry_base",
    "geometry_final",
    "true_frozen_leverage_total",
]
DISCRETE_AUDIT_FIELDS = AUDIT_FIELDS[:4]
FLOAT_AUDIT_FIELDS = AUDIT_FIELDS[4:]


def prefix_sha256(
    shard_root: Path, method: str, centers: int, shard_size: int
) -> str:
    digest = hashlib.sha256()
    for start in range(0, centers, shard_size):
        stop = min(start + shard_size, centers)
        digest.update(
            (shard_root / f"{start:06d}_{stop:06d}_{method}.csv").read_bytes()
        )
    return digest.hexdigest()


def read_old_audit(shard_root: Path, centers: int, shard_size: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for start in range(0, centers, shard_size):
        stop = min(start + shard_size, centers)
        with (shard_root / f"{start:06d}_{stop:06d}_audit.csv").open(
            newline="", encoding="utf-8"
        ) as source:
            rows.extend(dict(zip(AUDIT_FIELDS, row, strict=True)) for row in csv.reader(source))
    return rows


def compare_audit(
    old_rows: list[dict[str, str]],
    new_rows: list[dict[str, str]],
    *,
    tolerance: float,
) -> dict[str, object]:
    discrete_mismatches = 0
    maximum_absolute_difference = {field: 0.0 for field in FLOAT_AUDIT_FIELDS}
    floating_mismatches = 0
    if len(old_rows) != len(new_rows):
        return {
            "rows_match": False,
            "old_rows": len(old_rows),
            "new_rows": len(new_rows),
            "discrete_mismatches": None,
            "floating_mismatches": None,
            "maximum_absolute_difference": maximum_absolute_difference,
        }
    for old, new in zip(old_rows, new_rows, strict=True):
        if any(old[field] != new[field] for field in DISCRETE_AUDIT_FIELDS):
            discrete_mismatches += 1
        for field in FLOAT_AUDIT_FIELDS:
            difference = abs(float(old[field]) - float(new[field]))
            maximum_absolute_difference[field] = max(
                maximum_absolute_difference[field], difference
            )
            if not math.isclose(
                float(old[field]), float(new[field]), rel_tol=tolerance, abs_tol=tolerance
            ):
                floating_mismatches += 1
    return {
        "rows_match": True,
        "old_rows": len(old_rows),
        "new_rows": len(new_rows),
        "discrete_mismatches": discrete_mismatches,
        "floating_mismatches": floating_mismatches,
        "maximum_absolute_difference": maximum_absolute_difference,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-output", type=Path, required=True)
    parser.add_argument("--new-output", type=Path, required=True)
    parser.add_argument("--centers", type=int, required=True)
    parser.add_argument("--shard-size", type=int, default=100)
    parser.add_argument("--tolerance", type=float, default=1e-10)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    complete = json.loads((args.new_output / "complete.json").read_text(encoding="utf-8"))
    if complete.get("centers") != args.centers or complete.get("full_frozen_center_count"):
        raise ValueError("new output is not the requested validation prefix")
    methods = sorted(complete["plans"])
    plans: dict[str, object] = {}
    all_plans_match = True
    for method in methods:
        old_hash = prefix_sha256(
            args.old_output / "shards", method, args.centers, args.shard_size
        )
        new_path = args.new_output / "plans" / f"{method}.csv"
        new_hash = hashlib.sha256(new_path.read_bytes()).hexdigest()
        matches = old_hash == new_hash == complete["plans"][method]["sha256"]
        all_plans_match &= matches
        plans[method] = {
            "matches": matches,
            "old_prefix_sha256": old_hash,
            "new_sha256": new_hash,
        }
    old_audit = read_old_audit(
        args.old_output / "shards", args.centers, args.shard_size
    )
    with (args.new_output / "per_center.csv").open(newline="", encoding="utf-8") as source:
        new_audit = list(csv.DictReader(source))
    audit = compare_audit(old_audit, new_audit, tolerance=args.tolerance)
    compatible = bool(
        all_plans_match
        and audit["rows_match"]
        and audit["discrete_mismatches"] == 0
        and audit["floating_mismatches"] == 0
    )
    report = {
        "compatible": compatible,
        "centers": args.centers,
        "tolerance": args.tolerance,
        "plans": plans,
        "audit": audit,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not compatible:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
