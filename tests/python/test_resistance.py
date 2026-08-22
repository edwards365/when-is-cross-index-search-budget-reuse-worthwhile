import numpy as np
import pytest
from narhnsw.resistance import (
    edge_leverage_scores,
    effective_resistance_matrix,
    gaussian_weight_graph,
    greedy_neighbor_selection,
)


def test_weighted_tree_edges_have_unit_leverage() -> None:
    weights = np.array([[0.0, 2.0, 0.0], [2.0, 0.0, 4.0], [0.0, 4.0, 0.0]])
    resistance = effective_resistance_matrix(weights)
    leverage = edge_leverage_scores(weights, resistance)
    assert resistance[0, 2] == pytest.approx(0.75)
    assert leverage[0, 1] == pytest.approx(1.0)
    assert leverage[1, 2] == pytest.approx(1.0)


def test_triangle_edge_leverage_is_two_thirds() -> None:
    weights = np.ones((3, 3)) - np.eye(3)
    leverage = edge_leverage_scores(weights)
    np.testing.assert_allclose(leverage[weights > 0], 2 / 3)


def test_disconnected_pairs_are_infinite() -> None:
    weights = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=float)
    resistance = effective_resistance_matrix(weights)
    assert np.isinf(resistance[0, 2])
    assert resistance[2, 2] == 0


def test_asymmetric_weights_are_rejected() -> None:
    with pytest.raises(ValueError, match="symmetric"):
        effective_resistance_matrix(np.array([[0.0, 1.0], [0.0, 0.0]]))


def test_gaussian_graph_is_symmetric() -> None:
    points = np.array([[0.0], [1.0], [2.0]])
    adjacency = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=bool)
    weights = gaussian_weight_graph(points, adjacency, rho=1)
    np.testing.assert_allclose(weights, weights.T)


def test_direction_term_avoids_duplicate_direction() -> None:
    center = np.array([0.0, 0.0])
    candidates = np.array([[1.0, 0.0], [2.0, 0.0], [0.0, 1.0]])
    selected, trace = greedy_neighbor_selection(
        center, candidates, np.zeros(3), 2, alpha=0, beta=1, gamma=0, sigma=0.5
    )
    assert selected == [0, 2]
    assert all(item.total_gain >= 0 for item in trace)
