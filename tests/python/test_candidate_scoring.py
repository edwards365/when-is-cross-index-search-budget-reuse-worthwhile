import csv
import math

import numpy as np
import pytest
from narhnsw.candidate_scoring import score_candidate_log, write_candidate_scores
from narhnsw.resistance import effective_resistance_matrix


def _write_fixture(tmp_path, *, final_edges=None):
    np.savetxt(
        tmp_path / "points.csv",
        np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [1.0, 1.0]]),
        delimiter=",",
    )
    with (tmp_path / "insertion_candidates.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
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
        )
        writer.writerows(
            [
                [1, 0, 0, 1.0, "accepted", "", 1, 1, 1, 1],
                [2, 0, 1, 1.0, "accepted", "", 1, 1, 1, 1],
                [2, 0, 0, 4.0, "occluded", 1, 0, 0, 0, 0],
                [3, 0, 1, 1.0, "accepted", "", 1, 1, 1, 1],
                [3, 0, 0, 2.0, "occluded", 1, 0, 0, 0, 0],
            ]
        )
    with (tmp_path / "insertion_adjacency_changes.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["insertion_id", "layer", "source", "target", "action"])
        writer.writerows([[1, 0, 0, 1, "added"], [2, 0, 1, 2, "added"], [3, 0, 1, 3, "added"]])
    if final_edges is None:
        final_edges = [(0, 1), (1, 0), (1, 2), (1, 3), (2, 1), (3, 1)]
    with (tmp_path / "edges.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source", "target"])
        writer.writerows(final_edges)


def test_scores_three_schemes_and_replays_final_graph(tmp_path):
    _write_fixture(tmp_path)
    rows, summary = score_candidate_log(tmp_path)
    assert summary["replay_matches_final_edges"] is True
    assert summary["final_directed_edges"] == 6
    assert len(rows) == 5
    accepted = [row for row in rows if row["decision"] == "accepted"]
    rejected = [row for row in rows if row["decision"] == "occluded"]
    assert all(math.isnan(row["scheme_b_gain"]) for row in accepted)
    assert all(0.0 < row["scheme_c_tau"] <= 1.0 + 1e-10 for row in accepted)
    assert all(math.isnan(row["scheme_c_tau"]) for row in rejected)
    assert all(row["scheme_b_connected"] == 1 for row in rejected)
    assert all(row["scheme_b_gain"] > 0.0 for row in rejected)
    assert all(0.0 < row["scheme_a_tau"] <= 1.0 + 1e-10 for row in rows)

    output = tmp_path / "scores.csv"
    write_candidate_scores(rows, output)
    text = output.read_text(encoding="utf-8")
    assert "nan" not in text.lower()


def test_replay_rejects_final_edge_mismatch(tmp_path):
    _write_fixture(tmp_path, final_edges=[(0, 1)])
    with pytest.raises(ValueError, match="disagrees with edges.csv"):
        score_candidate_log(tmp_path)


def test_tiny_nonzero_conductance_remains_connected():
    weights = np.array([[0.0, 1.0e-9], [1.0e-9, 0.0]])
    resistance = effective_resistance_matrix(weights)
    assert np.isfinite(resistance[0, 1])
    assert resistance[0, 1] == pytest.approx(1.0e9, rel=1.0e-8)
