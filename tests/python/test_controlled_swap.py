import numpy as np
import pandas as pd
import pytest
from narhnsw.controlled_swap import apply_ordered_swaps, graph_to_adjacency
from narhnsw.search import ordered_beam_search


def test_ordered_swap_preserves_positions_degrees_and_original_input():
    neighbors = [[1, 2], [0], [0], []]
    swaps = pd.DataFrame([{"source": 0, "removed": 2, "added": 3}])
    repaired = apply_ordered_swaps(neighbors, swaps)
    assert repaired == [[1, 3], [0], [0], []]
    assert neighbors == [[1, 2], [0], [0], []]
    assert graph_to_adjacency(repaired).sum() == 4


def test_ordered_swap_rejects_existing_addition():
    with pytest.raises(ValueError, match="invalid directed swap"):
        apply_ordered_swaps([[1], [0]], pd.DataFrame([{"source": 0, "removed": 1, "added": 1}]))


def test_ordered_beam_search_counts_float32_distances():
    points = np.array([[0.0], [1.0], [2.0]], dtype=np.float32)
    labels, ndc, expanded = ordered_beam_search(
        points, [[1], [0, 2], [1]], np.array([2.1], dtype=np.float32), 0, k=1, ef=1
    )
    assert labels.tolist() == [2]
    assert ndc == 3
    assert expanded == 3
