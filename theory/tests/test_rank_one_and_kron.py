import numpy as np

from theory.math_validation import (
    effective_resistance,
    graph_matrices,
    kron_reduction,
    rank_one_pseudoinverse_update,
    spanning_tree_partition,
)


def test_laplacian_is_symmetric_psd_and_pseudoinverse_satisfies_penrose_conditions():
    edges = [(0, 1, 2.0), (1, 2, 3.0), (2, 3, 1.5), (0, 3, 0.7)]
    _, _, laplacian = graph_matrices(4, edges)
    laplacian_plus = np.linalg.pinv(laplacian, hermitian=True)
    assert np.allclose(laplacian, laplacian.T)
    assert np.linalg.eigvalsh(laplacian).min() > -1e-12
    assert np.allclose(laplacian @ np.ones(4), 0.0)
    assert np.allclose(laplacian @ laplacian_plus @ laplacian, laplacian)
    assert np.allclose(laplacian_plus @ laplacian @ laplacian_plus, laplacian_plus)
    assert np.allclose((laplacian @ laplacian_plus).T, laplacian @ laplacian_plus)
    assert np.allclose((laplacian_plus @ laplacian).T, laplacian_plus @ laplacian)


def test_rank_one_addition_and_deletion_updates_and_tree_partition_ratios():
    base = [(0, 1, 2.0), (1, 2, 3.0), (2, 3, 1.5), (0, 3, 0.7)]
    candidate = (0, 2, 1.2)
    _, _, laplacian = graph_matrices(4, base)
    laplacian_plus = np.linalg.pinv(laplacian, hermitian=True)
    contrast = np.array([1.0, 0.0, -1.0, 0.0])
    resistance_before = float(contrast @ laplacian_plus @ contrast)

    augmented = base + [candidate]
    _, _, augmented_laplacian = graph_matrices(4, augmented)
    expected_plus = np.linalg.pinv(augmented_laplacian, hermitian=True)
    updated_plus = rank_one_pseudoinverse_update(
        laplacian_plus, contrast, candidate[2], add=True
    )
    assert np.allclose(updated_plus, expected_plus)
    assert np.isclose(
        spanning_tree_partition(4, augmented) / spanning_tree_partition(4, base),
        1.0 + candidate[2] * resistance_before,
    )

    restored_plus = rank_one_pseudoinverse_update(
        expected_plus, contrast, candidate[2], add=False
    )
    candidate_tau_after_addition = candidate[2] * float(contrast @ expected_plus @ contrast)
    assert np.allclose(restored_plus, laplacian_plus)
    assert np.isclose(
        spanning_tree_partition(4, base) / spanning_tree_partition(4, augmented),
        1.0 - candidate_tau_after_addition,
    )


def test_kron_reduction_exactly_preserves_boundary_resistance():
    edges = [(0, 1, 1.0), (1, 2, 2.0), (2, 3, 1.0), (0, 3, 0.5), (1, 3, 0.8)]
    _, _, laplacian = graph_matrices(4, edges)
    reduced = kron_reduction(laplacian, [0, 3])
    contrast = np.array([1.0, -1.0])
    reduced_resistance = float(
        contrast @ np.linalg.pinv(reduced, hermitian=True) @ contrast
    )
    assert np.isclose(reduced_resistance, effective_resistance(4, edges, 0, 3))
