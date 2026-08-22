import csv

import pytest
from narhnsw.candidate_logs import summarize_candidate_log

HEADER = [
    "insertion_id",
    "layer",
    "candidate_id",
    "distance_to_new",
    "decision",
    "blocker_id",
    "new_to_candidate_after",
    "candidate_to_new_after",
    "new_to_candidate_final",
    "candidate_to_new_final",
]


def write_fixture(tmp_path, rows):
    with (tmp_path / "insertion_candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)
    with (tmp_path / "insertion_adjacency_changes.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["insertion_id", "layer", "source", "target", "action"])
        writer.writerow([2, 0, 0, 2, "added"])
        writer.writerow([2, 0, 0, 1, "removed"])


def test_candidate_log_summary_and_invariants(tmp_path):
    write_fixture(
        tmp_path,
        [
            [2, 0, 0, 1.0, "accepted", "", 1, 1, 1, 0],
            [2, 0, 1, 2.0, "occluded", 0, 0, 0, 0, 0],
            [3, 1, 0, 3.0, "budget_exhausted", "", 0, 0, 0, 0],
        ],
    )
    summary = summarize_candidate_log(tmp_path)
    assert summary["decision_counts"] == {
        "accepted": 1,
        "occluded": 1,
        "budget_exhausted": 1,
    }
    assert summary["accepted_forward_final_survival_rate"] == 1.0
    assert summary["accepted_reciprocal_final_survival_rate"] == 0.0
    assert summary["rejected_final_edge_count"] == 0
    assert summary["adjacency_change_counts"] == {"added": 1, "removed": 1}


def test_candidate_log_rejects_missing_occlusion_blocker(tmp_path):
    write_fixture(tmp_path, [[2, 0, 0, 1.0, "occluded", "", 0, 0, 0, 0]])
    with pytest.raises(ValueError, match="first blocker"):
        summarize_candidate_log(tmp_path)
