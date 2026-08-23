import numpy as np
import pytest
from narhnsw.resistance import (
    direction_coverage,
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


def test_grounded_solver_matches_moore_penrose_reference() -> None:
    weights = np.array(
        [
            [0.0, 1.2, 0.4, 0.0],
            [1.2, 0.0, 0.7, 0.3],
            [0.4, 0.7, 0.0, 1.1],
            [0.0, 0.3, 1.1, 0.0],
        ]
    )
    laplacian = np.diag(weights.sum(axis=1)) - weights
    reference_inverse = np.linalg.pinv(laplacian, hermitian=True)
    diagonal = np.diag(reference_inverse)
    reference = diagonal[:, None] + diagonal[None, :] - 2.0 * reference_inverse

    np.testing.assert_allclose(
        effective_resistance_matrix(weights), reference, rtol=1e-12, atol=1e-12
    )


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


def test_direction_logdet_is_monotone_submodular_on_tiny_instance() -> None:
    directions = np.array([[1.0, 0.0], [0.0, 1.0], [np.sqrt(0.5), np.sqrt(0.5)]], dtype=float)

    def value(indices: frozenset[int]) -> float:
        rows = directions[sorted(indices)] if indices else np.empty((0, 2))
        return direction_coverage(rows, sigma=0.7)

    universe = frozenset(range(len(directions)))
    subsets = [
        frozenset(i for i in universe if mask & (1 << i)) for mask in range(1 << len(universe))
    ]
    for left in subsets:
        for right in subsets:
            if not left.issubset(right):
                continue
            assert value(left) <= value(right) + 1e-12
            for item in universe - right:
                gain_left = value(left | {item}) - value(left)
                gain_right = value(right | {item}) - value(right)
                assert gain_left + 1e-12 >= gain_right
