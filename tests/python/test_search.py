import numpy as np
from narhnsw.search import beam_search


def test_beam_search_counts_exact_distance_calls() -> None:
    points = np.arange(6, dtype=float)[:, None]
    adjacency = np.zeros((6, 6), dtype=bool)
    for node in range(5):
        adjacency[node, node + 1] = True
        adjacency[node + 1, node] = True
    labels, ndc, expanded = beam_search(points, adjacency, np.array([5.1]), 0, k=1, ef=2)
    assert labels.tolist() == [5]
    assert ndc == 6
    assert expanded == 6
