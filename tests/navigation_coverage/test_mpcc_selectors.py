import numpy as np
from narhnsw.mpcc_selectors import (
    frozen_directions,
    frozen_radii,
    length_aware_angle_select,
    maxmin_angle_select,
    mpcc_select,
    progress_masks,
    shuffled_mpcc_select,
)


def test_frozen_states_and_progress_masks_are_deterministic() -> None:
    local = np.eye(4)
    first = np.random.default_rng(9)
    second = np.random.default_rng(9)
    radii_a, labels_a = frozen_radii(11, first)
    radii_b, labels_b = frozen_radii(11, second)
    directions_a = frozen_directions("empirical_direction", local, 11, first)
    directions_b = frozen_directions("empirical_direction", local, 11, second)
    assert np.array_equal(radii_a, radii_b)
    assert np.array_equal(labels_a, labels_b)
    assert np.array_equal(directions_a, directions_b)
    center = np.zeros(4)
    masks = progress_masks(center, local, 1.0, directions_a, radii_a)
    assert masks.shape == (4, 11)


def test_angle_selectors_fill_budget_deterministically() -> None:
    center = np.zeros(2)
    candidates = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -2.0]])
    labels = np.array([1, 2, 3, 4])
    assert maxmin_angle_select(center, candidates, labels, 3) == (0, 2, 1)
    first = length_aware_angle_select(center, candidates, labels, 3)
    second = length_aware_angle_select(center, candidates, labels, 3)
    assert first == second
    assert len(set(first)) == 3


def test_mpcc_backbone_is_retained() -> None:
    masks = np.array(
        [[True, False, False], [False, True, False], [False, False, True]], dtype=bool
    )
    assert mpcc_select(masks, 2, (1,))[0] == 1


def test_shuffled_mpcc_returns_original_candidate_coordinates() -> None:
    masks = np.eye(5, dtype=bool)
    seed = 31
    expected_permutation = np.random.default_rng(seed).permutation(len(masks))
    selected = shuffled_mpcc_select(masks, 2, np.random.default_rng(seed))
    assert selected == tuple(int(item) for item in expected_permutation[:2])
