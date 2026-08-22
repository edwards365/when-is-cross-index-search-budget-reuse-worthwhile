import numpy as np

from theory.math_validation import (
    complete_edges,
    cycle_edges,
    double_clique_edges,
    effective_resistance,
    graph_matrices,
    parallel_two_hop_edges,
    path_edges,
    projection_and_leverages,
    sampled_spanning_tree_frequencies,
    spanning_tree_marginals,
)


def test_known_graph_resistances_and_leverages():
    for n in (2, 4, 7):
        _, tau = projection_and_leverages(n, path_edges(n))
        assert np.allclose(tau, 1.0)

    n = 7
    cycle = cycle_edges(n)
    assert np.isclose(effective_resistance(n, cycle, 0, 1), (n - 1) / n)
    complete = complete_edges(n)
    assert np.isclose(effective_resistance(n, complete, 0, 1), 2 / n)

    double = double_clique_edges(4)
    _, tau = projection_and_leverages(8, double)
    assert np.isclose(tau[-1], 1.0)


def test_laplacian_and_projection_identities():
    n, edges = parallel_two_hop_edges(4)
    _, _, laplacian = graph_matrices(n, edges)
    laplacian_plus = np.linalg.pinv(laplacian, hermitian=True)
    projector, tau = projection_and_leverages(n, edges)
    assert np.allclose(laplacian @ np.ones(n), 0.0)
    assert np.allclose(laplacian @ laplacian_plus @ laplacian, laplacian)
    assert np.allclose(projector @ projector, projector)
    assert np.isclose(np.trace(projector), n - 1)
    assert np.isclose(np.sum(tau), n - 1)


def test_parallel_paths_and_rayleigh_monotonicity():
    resistances = []
    for path_count in range(5):
        n, edges = parallel_two_hop_edges(path_count)
        resistances.append(effective_resistance(n, edges, 0, 1))
    assert np.allclose(resistances, [1 / (1 + count / 2) for count in range(5)])
    assert all(left > right for left, right in zip(resistances[:-1], resistances[1:], strict=True))


def test_weighted_spanning_tree_marginals_equal_leverages():
    edges = [(0, 1, 2.0), (1, 2, 3.0), (0, 2, 5.0)]
    _, tau = projection_and_leverages(3, edges)
    exact = spanning_tree_marginals(3, edges)
    sampled = sampled_spanning_tree_frequencies(3, edges, samples=20_000, seed=7)
    assert np.allclose(exact, tau)
    assert np.allclose(sampled, tau, atol=0.015)
