import numpy as np
import pytest
from narhnsw.e0_plans import (
    empirical_progress_masks_fast,
    exact_local_neighbors,
    reference_empirical_progress_masks,
    stable_mpcc_select,
)


def test_exact_neighbors_use_stable_smaller_label_tie_break() -> None:
    angles = np.linspace(0.0, 2.0 * np.pi, 20, endpoint=False)
    points = np.column_stack((np.cos(angles), np.sin(angles)))
    neighbors, scales = exact_local_neighbors(points, 16, block_size=3)
    assert neighbors.shape == (20, 16)
    assert np.all(scales > 0)
    # Labels 1 and 19 are equidistant from label 0; stable column order wins.
    assert tuple(neighbors[0, :2]) == (1, 19)
    assert all(source not in row for source, row in enumerate(neighbors))


def test_exact_neighbors_reject_nonpositive_scale() -> None:
    with pytest.raises(ValueError, match="16th-neighbor scale"):
        exact_local_neighbors(np.zeros((20, 2)), 16)


def test_fast_empirical_masks_are_bit_exact_to_reference() -> None:
    generator = np.random.default_rng(91)
    center = generator.normal(size=7)
    candidates = center + generator.normal(size=(13, 7))
    local = center + generator.normal(size=(64, 7))
    fast, _, _ = empirical_progress_masks_fast(
        center, candidates, local, 1.7, 2048, np.random.default_rng(20260824)
    )
    reference = reference_empirical_progress_masks(
        center, candidates, local, 1.7, 2048, np.random.default_rng(20260824)
    )
    assert np.array_equal(fast, reference)


def test_stable_mpcc_ties_use_length_then_external_label() -> None:
    masks = np.array([[1, 0], [1, 0], [0, 1], [0, 1]], dtype=bool)
    distances = np.array([2.0, 1.0, 3.0, 3.0])
    labels = np.array([2, 9, 8, 4])
    assert stable_mpcc_select(masks, 2, distances, labels) == (1, 3)
    assert stable_mpcc_select(masks, 3, distances, labels, backbone=(0,)) == (0, 3, 1)
