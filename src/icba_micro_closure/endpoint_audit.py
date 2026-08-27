#!/usr/bin/env python3
"""Streaming Gate E0 audit over frozen Cross-Index CSV.GZ files.

Writes only the compact graph-level CSV. Query-level Parquet is intentionally
not materialized while the preregistered free-space gate is closed.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import math
from collections import defaultdict
from pathlib import Path


GRID = (10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512)
TAU = 0.9
DELTA = 0.05
ALPHA = 0.05


def binom_cdf(k: int, n: int, p: float) -> float:
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    q = 1.0 - p
    log_term = (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                + k * math.log(p) + (n - k) * math.log(q))
    term = math.exp(log_term) if log_term > -745 else 0.0
    total = term
    for i in range(k, 0, -1):
        term *= i / (n - i + 1) * q / p
        total += term
    return min(1.0, max(0.0, total))


def cp_interval(failures: int, n: int, alpha: float = ALPHA) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    if failures == 0:
        lo = 0.0
    else:
        left, right = 0.0, failures / n
        target = 1.0 - alpha / 2.0
        for _ in range(70):
            mid = (left + right) / 2.0
            if binom_cdf(failures - 1, n, mid) > target:
                left = mid
            else:
                right = mid
        lo = (left + right) / 2.0
    if failures == n:
        hi = 1.0
    else:
        left, right = failures / n, 1.0
        target = alpha / 2.0
        for _ in range(70):
            mid = (left + right) / 2.0
            if binom_cdf(failures, n, mid) > target:
                left = mid
            else:
                right = mid
        hi = (left + right) / 2.0
    return lo, hi


def cp_upper_one_sided(failures: int, n: int, alpha: float = ALPHA) -> float:
    if failures == n:
        return 1.0
    left, right = failures / n, 1.0
    for _ in range(70):
        mid = (left + right) / 2.0
        if binom_cdf(failures, n, mid) > alpha:
            left = mid
        else:
            right = mid
    return (left + right) / 2.0


def quantile(values: list[float], p: float) -> float:
    xs = sorted(values)
    if not xs:
        return math.nan
    pos = (len(xs) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def audit(path: Path) -> dict[str, object]:
    by_query: dict[int, dict[int, float]] = defaultdict(dict)
    first: dict[str, str] | None = None
    label_consistent = True
    with gzip.open(path, "rt", newline="") as handle:
        for row in csv.DictReader(handle):
            first = first or row
            qid = int(row["query_id"])
            ef = int(row.get("ef_search") or row["budget"])
            by_query[qid][ef] = float(row["recall_at_10"])
            if "success" in row:
                label_consistent &= row["success"].lower() == "true" and not row["error_code"]
    assert first is not None
    complete = all(tuple(sorted(v)) == GRID for v in by_query.values())
    monotone = sum(any(v[b] > v[c] for b, c in zip(GRID, GRID[1:])) for v in by_query.values())
    stable: dict[int, int | None] = {}
    for qid, curve in by_query.items():
        stable[qid] = next((b for i, b in enumerate(GRID) if all(curve[x] >= TAU for x in GRID[i:])), None)
    failures = {b: sum(curve[b] < TAU for curve in by_query.values()) for b in GRID}
    n = len(by_query)
    empirical = next((b for b in GRID if failures[b] / n <= DELTA), None)
    certified = next((b for b in GRID if cp_upper_one_sided(failures[b], n) <= DELTA), None)
    max_fail = failures[GRID[-1]]
    if not complete or not label_consistent:
        status = "LABEL_OR_PROTOCOL_INCONSISTENCY"
    elif max_fail / n > DELTA:
        status = "GRID_RIGHT_CENSORED" if any(v is None for v in stable.values()) else "NO_PRACTICAL_SAFE_ENDPOINT"
    elif certified == GRID[-1]:
        status = "HIGHER_SAFE_ENDPOINT_REQUIRED"
    elif certified is not None:
        status = "CURRENT_ENDPOINT_CERTIFIABLY_SAFE"
    else:
        status = "NO_PRACTICAL_SAFE_ENDPOINT"
    lo, hi = cp_interval(max_fail, n)
    out: dict[str, object] = {
        "dataset": first["dataset"], "implementation": path.parent.name,
        "history": first.get("insertion_order") or first["history"],
        "seed": first.get("graph_seed") or first["seed"],
        "graph_hash": first["graph_hash"], "queries": n, "grid_complete": complete,
        "protocol_consistent": label_consistent, "nonmonotone_queries": monotone,
        "right_censored_queries": sum(v is None for v in stable.values()),
        "right_censored_rate": sum(v is None for v in stable.values()) / n,
        "max_budget_failures": max_fail, "max_budget_failure_rate": max_fail / n,
        "max_budget_cp95_low": lo, "max_budget_cp95_high": hi,
        "empirical_safe_budget": empirical or "", "certified_safe_budget": certified or "",
        "endpoint_status": status,
    }
    for b in GRID:
        out[f"failures_ef{b}"] = failures[b]
        out[f"failure_rate_ef{b}"] = failures[b] / n
        vals = [curve[b] for curve in by_query.values()]
        out[f"mean_recall_ef{b}"] = sum(vals) / n
        out[f"p05_recall_ef{b}"] = quantile(vals, 0.05)
        out[f"cp95_upper_ef{b}"] = cp_upper_one_sided(failures[b], n)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.root.glob("*/*.csv.gz"))
    rows = [audit(path) for path in paths]
    if len(rows) != 81:
        raise SystemExit(f"expected 81 frozen graphs, found {len(rows)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    with tmp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    tmp.replace(args.output)


if __name__ == "__main__":
    main()
