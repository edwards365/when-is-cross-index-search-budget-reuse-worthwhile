#!/usr/bin/env python3
"""Stream a frozen sentinel action table into a GSC proposal-only slack audit.

The script never opens evaluation or future-confirm paths and writes only the
caller-specified GSC-derived output.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def quantile(values: list[float], q: float) -> float:
    values = sorted(values)
    if not values:
        raise ValueError("empty sample")
    index = max(0, min(len(values) - 1, int(q * len(values)) - 1))
    return values[index]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sentinel-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pattern = re.compile(r"^(?P<dataset>.+)__G(?P<build>[0-9]+)__sentinel_actions\.csv$")
    rows: list[dict[str, object]] = []
    for path in sorted(args.sentinel_dir.glob("*_sentinel_actions.csv")):
        match = pattern.match(path.name)
        if not match:
            continue
        groups: dict[int, list[dict[str, str]]] = {}
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                groups.setdefault(int(row["requested_ef"]), []).append(row)
        for ef, action_rows in sorted(groups.items()):
            ndc = [float(row["native_ndc"]) for row in action_rows]
            z_abs = [int(row["Z_abs"]) for row in action_rows]
            endpoint = sorted({row["endpoint_status"] for row in action_rows})
            native_equal = all(row["native_tracer_topk_equal"] == "1" for row in action_rows)
            rows.append(
                {
                    "dataset": match.group("dataset"),
                    "build": f"G{match.group('build')}",
                    "requested_ef": ef,
                    "queries": len(action_rows),
                    "z_abs_count": sum(z_abs),
                    "z_abs_rate": sum(z_abs) / len(action_rows),
                    "mean_ndc": sum(ndc) / len(ndc),
                    "p95_ndc": quantile(ndc, 0.95),
                    "p99_ndc": quantile(ndc, 0.99),
                    "endpoint_status": "+".join(endpoint),
                    "native_tracer_topk_equal": int(native_equal),
                    "source_role": "FROZEN_SENTINEL_AUDIT",
                }
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["dataset", "build", "requested_ef"]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} action cells to {args.output}")


if __name__ == "__main__":
    main()
