#!/usr/bin/env python3
"""Join rejected insertion candidates to exact HNSW query traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from narhnsw.query_attribution import attribute_rejected_candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scores", type=Path)
    parser.add_argument("traces", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty result directory: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    attributed, failure_support, summary = attribute_rejected_candidates(args.scores, args.traces)
    attributed.to_csv(args.output / "candidate_trace_attribution.csv", index=False)
    failure_support.to_csv(args.output / "failure_query_support.csv", index=False)
    shortlist = attributed[attributed["missed_ground_truth_eligible_count"] > 0].sort_values(
        [
            "missed_ground_truth_eligible_count",
            "progressive_eligible_count",
            "scheme_b_gain",
        ],
        ascending=[False, False, False],
    )
    shortlist.to_csv(args.output / "intervention_shortlist.csv", index=False)
    with (args.output / "attribution_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
