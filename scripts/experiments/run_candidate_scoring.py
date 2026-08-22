#!/usr/bin/env python3
"""Score logged HNSW insertion candidates without changing the index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from narhnsw.candidate_scoring import score_candidate_log, write_candidate_scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty result directory: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)

    last_reported = 0

    def report(done: int, total: int) -> None:
        nonlocal last_reported
        if done == total or done - last_reported >= 50:
            print(f"scored insertions: {done}/{total}", flush=True)
            last_reported = done

    rows, summary = score_candidate_log(args.source, progress=report)
    write_candidate_scores(rows, args.output / "candidate_scores.csv")
    with (args.output / "candidate_score_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    with (args.output / "metadata.txt").open("w", encoding="utf-8") as handle:
        handle.write("scoring_graph=actual_post_insertion_layer0_induced_candidate_graph\n")
        handle.write("weighting=gaussian_fixed_rho_per_insertion_from_base_plus_center_star\n")
        handle.write("logged_distance=hnswlib_squared_l2\n")
        handle.write("scheme_a=dense_center_star_existing_edge_leverage\n")
        handle.write("scheme_b=rejected_edge_pre_add_gain_after_standard_hnsw_insertion\n")
        handle.write("scheme_c=accepted_edge_post_insertion_deletion_leverage\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
