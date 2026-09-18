#!/usr/bin/env python3
"""Fail-closed checks for the Deep1M target-certified scale replication."""

import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--roles", type=Path, required=True)
    args = parser.parse_args()
    checks = []

    def require(condition, message):
        if not condition:
            raise AssertionError(message)
        checks.append(message)

    roles = json.loads(args.roles.read_text(encoding="utf-8"))
    require(roles["status"] == "FROZEN_BEFORE_VECTOR_TRUTH_OR_SEARCH_ACCESS", "roles frozen before access")
    require(all(value == 0 for value in roles["overlap_counts"].values()), "all query-role overlaps are zero")
    require(all(len(ids) == 500 for ids in roles["roles"].values()), "three roles contain 500 IDs each")

    summary = json.loads((args.results / "summary.json").read_text(encoding="utf-8"))
    pairs = list(csv.DictReader((args.results / "pair_results.csv").open(encoding="utf-8")))
    source = list(csv.DictReader((args.results / "source_policy.csv").open(encoding="utf-8")))
    intervals = list(csv.DictReader((args.results / "interval_sensitivity.csv").open(encoding="utf-8")))
    require(len(source) == 8, "eight source policies")
    require(len(pairs) == 56, "56 directed source-target decisions")
    require(len(intervals) == 3, "three registered resampling analyses")
    require(all(int(row["candidate_clipped"]) == 0 for row in source), "all source-derived candidates are non-clipped")
    require(all(row["decision"] == "DEPLOY_CANDIDATE" for row in pairs), "all target decisions deploy the candidate")
    require(max(float(row["candidate_cert_ucb"]) for row in pairs) <= .05, "all candidates pass target certification")
    require(max(float(row["endpoint_cert_ucb"]) for row in pairs) <= .05, "all endpoints pass target certification")
    crossed = next(row for row in intervals if row["resampling"] == "CROSSED_TARGET_QUERY")
    require(float(crossed["risk_ci_high"]) < .05, "crossed risk interval remains below 5 percent")
    require(float(crossed["saving_ci_low"]) > 0, "crossed NDC-saving interval remains positive")
    require(float(summary["pooled_p95_ratio"]) <= 1, "pooled p95 does not worsen")
    require(float(summary["max_target_p95_ratio"]) <= 1, "no target p95 worsens")
    require(float(summary["lobo_min_saving"]) > 0, "LOTO minimum saving is positive")
    require(float(summary["min_target_saving"]) > 0, "every target has positive mean saving")
    require(summary["gate"] == "PASS", "registered aggregate gate passes")
    report = {"status": "PASS", "checks_passed": len(checks), "checks": checks}
    (args.results / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
