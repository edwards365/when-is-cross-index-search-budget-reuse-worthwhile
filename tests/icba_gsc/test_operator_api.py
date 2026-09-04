from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts" / "icba_gsc"))
from operator_api import (  # noqa: E402
    assert_same_degree,
    response_aware_insertion_order,
    response_weighted_prune,
    rollback_graph,
)


def graph() -> np.ndarray:
    return np.array([[0, 1, 1, 0], [1, 0, 1, 0], [1, 1, 0, 1], [0, 0, 1, 0]], dtype=bool)


def test_rollback_isolated_and_input_unchanged() -> None:
    original = graph()
    copy = rollback_graph(original)
    copy[0, 1] = False
    assert original[0, 1]
    assert_same_degree(original, graph())


def test_o4_preserves_degree() -> None:
    original = graph()
    pools = [[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]]
    candidate = response_weighted_prune(original, [0.1, 0.2, 0.9, 0.4], candidate_pools=pools)
    assert_same_degree(original, candidate)


def test_o4_has_no_self_loops() -> None:
    original = graph()
    candidate = response_weighted_prune(original, [0.1, 0.2, 0.9, 0.4])
    assert not np.any(np.diag(candidate))


def test_o4_ties_end_at_node_id() -> None:
    original = np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]], dtype=bool)
    candidate = response_weighted_prune(original, [0.0, 1.0, 1.0])
    assert np.flatnonzero(candidate[0]).tolist() == [1, 2]


def test_o4_rejects_short_pool() -> None:
    with pytest.raises(ValueError):
        response_weighted_prune(graph(), [0.1, 0.2, 0.3, 0.4], candidate_pools=[[1], [0, 2], [0, 1, 3], [2]])


def test_o6_preserves_neighbor_sets() -> None:
    rows = [[1, 2, 3], [0, 2], [2, 3]]
    result = response_aware_insertion_order(rows, [0.3, 0.1, 0.9, 0.2], reorder_fraction=0.5)
    assert [set(x) for x in result] == [set(x) for x in rows]


def test_o6_is_deterministic_and_bounded() -> None:
    rows = [[1, 2, 3, 0]]
    result = response_aware_insertion_order(rows, [0.3, 0.1, 0.9, 0.2], reorder_fraction=0.5)
    assert result == [[2, 1, 3, 0]]


def test_o6_rejects_invalid_fraction() -> None:
    with pytest.raises(ValueError):
        response_aware_insertion_order([[1]], [0.0, 1.0], reorder_fraction=1.1)


def test_graph_validation_rejects_self_loop() -> None:
    with pytest.raises(ValueError):
        rollback_graph(np.array([[1]], dtype=bool))
