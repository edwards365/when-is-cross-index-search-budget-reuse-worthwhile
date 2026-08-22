import numpy as np
from narhnsw.datasets import narrow_bridge


def test_narrow_bridge_is_deterministic_and_ground_truth_valid() -> None:
    first = narrow_bridge(200, dim=4, seed=9)
    second = narrow_bridge(200, dim=4, seed=9)
    np.testing.assert_array_equal(first.base, second.base)
    np.testing.assert_array_equal(first.ground_truth, second.ground_truth)
    assert first.base.shape == (200, 4)
    assert first.ground_truth.shape[1] == 10
    assert np.all(first.ground_truth >= 0)
    assert np.all(first.ground_truth < len(first.base))
