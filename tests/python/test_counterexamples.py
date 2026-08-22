import numpy as np

from theory.math_validation import effective_resistance, pure_greedy_path
from theory.search_counterexamples import fixed_navigation_examples


def test_high_resistance_edge_can_point_away_from_query():
    example = fixed_navigation_examples()["high_resistance_no_navigation"]
    assert np.isclose(example["leverage"], 1.0)
    assert example["distance_change"] > 0


def test_low_resistance_edge_can_be_the_only_greedy_shortcut():
    example = fixed_navigation_examples()["low_resistance_high_navigation"]
    assert example["leverage"] < 0.34
    assert example["path_without"] == [0]
    assert example["path_with"] == [0, 1]


def test_local_reference_graph_can_overestimate_global_resistance():
    local = [(0, 1, 1.0)]
    global_edges = local + [(0, 2, 1.0), (2, 1, 1.0), (0, 3, 1.0), (3, 1, 1.0)]
    assert np.isclose(effective_resistance(2, local, 0, 1), 1.0)
    assert np.isclose(effective_resistance(4, global_edges, 0, 1), 0.5)


def test_tiny_conductance_edge_can_change_unweighted_navigation():
    coordinates = np.array([[0.0, 0.0], [0.0, 2.0], [2.0, 0.0]])
    query = np.array([2.1, 0.0])
    base_adjacency = {0: {1}, 1: {0, 2}, 2: {1}}
    augmented_adjacency = {0: {1, 2}, 1: {0, 2}, 2: {0, 1}}
    assert pure_greedy_path(coordinates, base_adjacency, query, 0) == [0]
    assert pure_greedy_path(coordinates, augmented_adjacency, query, 0) == [0, 2]
