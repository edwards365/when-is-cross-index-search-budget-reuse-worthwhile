"""Offline insertion-time resistance scores for logged HNSW candidates.

The routines in this module replay only logged layer-0 adjacency changes. They do
not mutate or rebuild an HNSW index. Scheme A uses a dense center star, while
schemes B/C use the actual post-insertion HNSW graph induced by the construction
candidate pool. A single Gaussian scale is frozen per insertion for all schemes.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

import numpy as np
from scipy.sparse.csgraph import connected_components

from narhnsw.resistance import effective_resistance_matrix, gaussian_weight_graph

SCORE_FIELDS = [
    "insertion_id",
    "candidate_id",
    "decision",
    "blocker_id",
    "distance_to_new",
    "rho",
    "local_size",
    "base_component_count",
    "scheme_a_tau",
    "scheme_b_gain",
    "scheme_b_connected",
    "scheme_c_tau",
]


def _read_layer_zero_rows(path: Path) -> dict[int, list[dict[str, str]]]:
    grouped: defaultdict[int, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if int(row["layer"]) == 0:
                grouped[int(row["insertion_id"])].append(row)
    return dict(grouped)


def _read_layer_zero_changes(path: Path) -> dict[int, list[dict[str, str]]]:
    grouped: defaultdict[int, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if int(row["layer"]) == 0:
                grouped[int(row["insertion_id"])].append(row)
    return dict(grouped)


def _load_final_adjacency(path: Path, n_points: int) -> np.ndarray:
    adjacency = np.zeros((n_points, n_points), dtype=bool)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            source, target = int(row["source"]), int(row["target"])
            if not (0 <= source < n_points and 0 <= target < n_points):
                raise ValueError("final edge endpoint is outside points.csv")
            adjacency[source, target] = True
    return adjacency


def _insertion_scale(points: np.ndarray, local_ids: list[int], base: np.ndarray) -> float:
    local_points = points[local_ids]
    distances = np.linalg.norm(local_points[:, None] - local_points[None, :], axis=-1)
    scale_adjacency = base.copy()
    scale_adjacency[0, 1:] = True
    scale_adjacency[1:, 0] = True
    observed = distances[np.triu(scale_adjacency, k=1)]
    positive = observed[observed > np.finfo(float).eps]
    if positive.size == 0:
        positive = distances[0, 1:]
        positive = positive[positive > np.finfo(float).eps]
    if positive.size == 0:
        raise ValueError("cannot define Gaussian scale for duplicate-only candidate pool")
    return float(np.median(positive))


def score_candidate_log(
    source_directory: str | Path,
    *,
    progress: Callable[[int, int], None] | None = None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Replay layer-0 insertions and score every logged construction candidate.

    Scheme B is defined after the standard HNSW insertion has added its selected
    center edges, but before adding a particular rejected edge. Disconnected
    missing-edge endpoints have infinite gain and are represented as ``inf``.
    """

    source_directory = Path(source_directory)
    points = np.loadtxt(source_directory / "points.csv", delimiter=",", ndmin=2)
    n_points = len(points)
    candidates = _read_layer_zero_rows(source_directory / "insertion_candidates.csv")
    changes = _read_layer_zero_changes(source_directory / "insertion_adjacency_changes.csv")
    expected_insertions = set(range(1, n_points))
    if set(candidates) != expected_insertions:
        missing = sorted(expected_insertions - set(candidates))
        extra = sorted(set(candidates) - expected_insertions)
        raise ValueError(
            f"candidate insertion IDs are incomplete: missing={missing}, extra={extra}"
        )

    evolving = np.zeros((n_points, n_points), dtype=bool)
    scored: list[dict[str, object]] = []
    disconnected_b = 0

    for insertion_id in range(1, n_points):
        rows = candidates[insertion_id]
        candidate_ids = [int(row["candidate_id"]) for row in rows]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError(f"duplicate candidate at insertion {insertion_id}")
        invalid_candidate = any(
            not 0 <= candidate < insertion_id for candidate in candidate_ids
        )
        if not candidate_ids or invalid_candidate:
            raise ValueError(f"invalid candidate IDs at insertion {insertion_id}")

        accepted_ids = [
            int(row["candidate_id"]) for row in rows if row["decision"] == "accepted"
        ]
        evolving[insertion_id, accepted_ids] = True
        for change in changes.get(insertion_id, []):
            source, target = int(change["source"]), int(change["target"])
            if not (0 <= source < insertion_id and 0 <= target <= insertion_id):
                raise ValueError(f"invalid adjacency change at insertion {insertion_id}")
            if change["action"] == "added":
                evolving[source, target] = True
            elif change["action"] == "removed":
                if not evolving[source, target]:
                    raise ValueError(
                        f"removing absent edge {source}->{target} at insertion {insertion_id}"
                    )
                evolving[source, target] = False
            else:
                raise ValueError(f"unknown adjacency action {change['action']!r}")

        local_ids = [insertion_id, *candidate_ids]
        directed_local = evolving[np.ix_(local_ids, local_ids)]
        base = directed_local | directed_local.T
        np.fill_diagonal(base, False)
        rho = _insertion_scale(points, local_ids, base)
        base_weights = gaussian_weight_graph(points[local_ids], base, rho=rho)
        base_resistance = effective_resistance_matrix(base_weights)
        component_count = int(connected_components(base, directed=False, return_labels=False))

        scheme_a_adjacency = base.copy()
        scheme_a_adjacency[0, 1:] = True
        scheme_a_adjacency[1:, 0] = True
        scheme_a_weights = gaussian_weight_graph(
            points[local_ids], scheme_a_adjacency, rho=rho
        )
        scheme_a_resistance = effective_resistance_matrix(scheme_a_weights)

        for local_index, row in enumerate(rows, start=1):
            distance = float(row["distance_to_new"])
            if distance < 0:
                raise ValueError("hnswlib squared-L2 distance cannot be negative")
            reconstructed_distance = float(
                np.sum(np.square(points[insertion_id] - points[int(row["candidate_id"])]))
            )
            if not np.isclose(distance, reconstructed_distance, rtol=1e-4, atol=1e-5):
                raise ValueError("logged distance disagrees with squared L2 from points.csv")
            proposed_weight = math.exp(-(distance / rho**2))
            scheme_a_tau = proposed_weight * scheme_a_resistance[0, local_index]
            decision = row["decision"]
            scheme_b_gain = math.nan
            scheme_b_connected = ""
            scheme_c_tau = math.nan
            if decision == "accepted":
                if not base[0, local_index]:
                    raise ValueError("accepted candidate is absent from post-insertion graph")
                scheme_c_tau = proposed_weight * base_resistance[0, local_index]
            else:
                if base[0, local_index]:
                    raise ValueError("rejected candidate is present in post-insertion graph")
                connected = math.isfinite(base_resistance[0, local_index])
                scheme_b_connected = int(connected)
                if connected:
                    scheme_b_gain = proposed_weight * base_resistance[0, local_index]
                else:
                    scheme_b_gain = math.inf
                    disconnected_b += 1
            scored.append(
                {
                    "insertion_id": insertion_id,
                    "candidate_id": int(row["candidate_id"]),
                    "decision": decision,
                    "blocker_id": row["blocker_id"],
                    "distance_to_new": distance,
                    "rho": rho,
                    "local_size": len(local_ids),
                    "base_component_count": component_count,
                    "scheme_a_tau": float(scheme_a_tau),
                    "scheme_b_gain": float(scheme_b_gain),
                    "scheme_b_connected": scheme_b_connected,
                    "scheme_c_tau": float(scheme_c_tau),
                }
            )
        if progress is not None:
            progress(insertion_id, n_points - 1)

    final_expected = _load_final_adjacency(source_directory / "edges.csv", n_points)
    mismatch = np.argwhere(evolving != final_expected)
    if len(mismatch):
        first = mismatch[0]
        raise ValueError(
            "replayed layer-0 graph disagrees with edges.csv: "
            f"{len(mismatch)} cells differ, first={tuple(map(int, first))}"
        )
    a_values = np.array([float(row["scheme_a_tau"]) for row in scored])
    c_values = np.array(
        [float(row["scheme_c_tau"]) for row in scored if row["decision"] == "accepted"]
    )
    if np.any(a_values > 1.0 + 1e-4) or np.any(c_values > 1.0 + 1e-4):
        raise FloatingPointError("existing-edge leverage exceeded one beyond tolerance")
    summary: dict[str, object] = {
        "source_directory": str(source_directory),
        "points": n_points,
        "scored_rows": len(scored),
        "insertions": n_points - 1,
        "final_directed_edges": int(evolving.sum()),
        "replay_matches_final_edges": True,
        "scheme_b_disconnected_rows": disconnected_b,
        "existing_edge_leverage_violations_above_1_plus_1e_4": int(
            np.sum(a_values > 1.0 + 1e-4) + np.sum(c_values > 1.0 + 1e-4)
        ),
    }
    return scored, summary


def write_candidate_scores(rows: list[dict[str, object]], path: str | Path) -> None:
    """Write score rows with stable columns and explicit non-finite values."""

    path = Path(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCORE_FIELDS)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            for field in ("scheme_a_tau", "scheme_b_gain", "scheme_c_tau"):
                value = float(serialized[field])
                if math.isnan(value):
                    serialized[field] = ""
                elif math.isinf(value):
                    serialized[field] = "inf"
            writer.writerow(serialized)
