import numpy as np
import pytest
from narhnsw.graph import validate_adjacency
from narhnsw.repair import rewire_directed_graph, two_hop_candidate_pool


def fixture_graph() -> tuple[np.ndarray, np.ndarray]:
    points = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [2.0, 0.0]])
    adjacency = np.zeros((6, 6), dtype=bool)
    for node, neighbors in enumerate([[1, 2], [0, 5], [0, 3], [2, 4], [3, 5], [4, 1]]):
        adjacency[node, neighbors] = True
    return points, adjacency


def test_two_hop_pool_excludes_center() -> None:
    _, adjacency = fixture_graph()
    pool = two_hop_candidate_pool(adjacency, 0)
    assert 0 not in pool
    assert set([1, 2]).issubset(pool)


@pytest.mark.parametrize(
    "variant",
    [
        "original",
        "random",
        "distance",
        "geometry",
        "resistance",
        "resistance_direction",
        "ggr",
    ],
)
def test_variants_preserve_every_degree_and_total_budget(variant: str) -> None:
    points, adjacency = fixture_graph()
    repaired, metadata = rewire_directed_graph(points, adjacency, variant, seed=7, max_candidates=6)
    np.testing.assert_array_equal(repaired.sum(axis=1), adjacency.sum(axis=1))
    assert repaired.sum() == adjacency.sum()
    assert metadata["variant"] == variant
    assert validate_adjacency(repaired, max_degree=2)["directed_edges"] == 12
