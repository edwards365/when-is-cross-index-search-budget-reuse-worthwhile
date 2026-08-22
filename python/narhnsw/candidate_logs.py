"""Validation and summary statistics for construction-time HNSW candidate logs."""

from __future__ import annotations

import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

DECISIONS = {"accepted", "occluded", "budget_exhausted"}


def _as_bool(value: str) -> bool:
    if value not in {"0", "1"}:
        raise ValueError(f"expected CSV boolean 0/1, received {value!r}")
    return value == "1"


def _nearest_rank(values: list[int], probability: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(probability * (len(ordered) - 1))))
    return ordered[index]


def summarize_candidate_log(directory: str | Path) -> dict[str, object]:
    """Validate logger invariants and return mechanism-level summary statistics."""
    directory = Path(directory)
    candidate_path = directory / "insertion_candidates.csv"
    changes_path = directory / "insertion_adjacency_changes.csv"
    decision_counts: Counter[str] = Counter()
    layer_zero_counts: Counter[str] = Counter()
    candidates_per_insertion: defaultdict[int, int] = defaultdict(int)
    accepted = reciprocal_after = forward_final = reciprocal_final = 0
    rejected_final_edges = 0
    row_count = 0

    with candidate_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            row_count += 1
            decision = row["decision"]
            if decision not in DECISIONS:
                raise ValueError(f"unknown decision {decision!r}")
            layer = int(row["layer"])
            insertion_id = int(row["insertion_id"])
            new_after = _as_bool(row["new_to_candidate_after"])
            reciprocal_after_row = _as_bool(row["candidate_to_new_after"])
            new_final = _as_bool(row["new_to_candidate_final"])
            reciprocal_final_row = _as_bool(row["candidate_to_new_final"])
            blocker = row["blocker_id"]
            if (decision == "occluded") != bool(blocker):
                raise ValueError("only occluded candidates must name their first blocker")
            if (decision == "accepted") != new_after:
                raise ValueError("replayed acceptance disagrees with post-insertion outgoing edge")
            if decision != "accepted" and (new_final or reciprocal_final_row):
                rejected_final_edges += 1

            decision_counts[decision] += 1
            if layer == 0:
                layer_zero_counts[decision] += 1
                candidates_per_insertion[insertion_id] += 1
            if decision == "accepted":
                accepted += 1
                reciprocal_after += int(reciprocal_after_row)
                forward_final += int(new_final)
                reciprocal_final += int(reciprocal_final_row)

    change_counts: Counter[str] = Counter()
    with changes_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            action = row["action"]
            if action not in {"added", "removed"}:
                raise ValueError(f"unknown adjacency action {action!r}")
            change_counts[action] += 1

    insertion_sizes = list(candidates_per_insertion.values())
    return {
        "candidate_rows": row_count,
        "decision_counts": dict(decision_counts),
        "layer_zero_decision_counts": dict(layer_zero_counts),
        "layer_zero_insertions_with_candidates": len(insertion_sizes),
        "layer_zero_candidates_mean": statistics.fmean(insertion_sizes) if insertion_sizes else 0.0,
        "layer_zero_candidates_median": (
            statistics.median(insertion_sizes) if insertion_sizes else 0.0
        ),
        "layer_zero_candidates_p95": _nearest_rank(insertion_sizes, 0.95),
        "accepted_reciprocal_after_rate": reciprocal_after / accepted if accepted else 0.0,
        "accepted_forward_final_survival_rate": forward_final / accepted if accepted else 0.0,
        "accepted_reciprocal_final_survival_rate": reciprocal_final / accepted if accepted else 0.0,
        "rejected_final_edge_count": rejected_final_edges,
        "adjacency_change_counts": dict(change_counts),
    }
