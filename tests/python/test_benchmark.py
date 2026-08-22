import numpy as np
from narhnsw.benchmark import recall_at_k


def test_recall_at_k() -> None:
    expected = np.array([[1, 2], [3, 4]])
    observed = np.array([[2, 8], [4, 3]])
    np.testing.assert_allclose(recall_at_k(expected, observed), [0.5, 1.0])
