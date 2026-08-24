import numpy as np
import pytest
from narhnsw.e0_plans import exact_local_neighbors


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
