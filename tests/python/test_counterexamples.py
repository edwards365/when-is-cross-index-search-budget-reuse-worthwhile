import numpy as np

from theory.math_validation import effective_resistance, projection_and_leverages, pure_greedy_path
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


def test_union_symmetrization_can_invent_reverse_traversal():
    directed = {(0, 1), (1, 2)}
    union_undirected = {tuple(sorted(edge)) for edge in directed}
    assert (0, 1) in union_undirected
    assert (1, 0) not in directed


def test_augmented_star_candidate_leverages_are_all_one():
    edges = [(0, 1, 1.0), (0, 2, 1.0), (0, 3, 1.0)]
    _, scores = projection_and_leverages(4, edges)
    assert np.allclose(scores, np.ones(3), atol=1e-10)


def test_high_leverage_budget_choice_can_remove_only_progress_edge():
    points = np.array([[0.0], [1.0], [-5.0]])
    query = np.array([2.0])
    distances = np.linalg.norm(points - query, axis=1)
    assert distances[1] < distances[0] < distances[2]
    resistance_scores = np.array([0.4, 1.0])
    selected = int(np.argmax(resistance_scores)) + 1
    assert selected == 2
    assert distances[selected] > distances[0]


def test_high_dimensional_first_direction_marginals_are_identical():
    rng = np.random.default_rng(17)
    directions = rng.normal(size=(64, 512))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    sigma = 0.7
    first_marginals = np.log1p(np.sum(directions * directions, axis=1) / sigma**2)
    assert np.ptp(first_marginals) < 1e-12
