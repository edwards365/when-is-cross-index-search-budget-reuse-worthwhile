import numpy as np
from narhnsw.ground_truth import exact_top_k


def test_exact_l2_top_k_matches_direct_stable_sort() -> None:
    rng = np.random.default_rng(17)
    base = rng.normal(size=(31, 5)).astype(np.float32)
    queries = rng.normal(size=(7, 5)).astype(np.float32)
    labels, distances = exact_top_k(
        base, queries, 4, metric="l2", query_batch=3, base_batch=9
    )
    direct = np.square(queries[:, None].astype(np.float64) - base.astype(np.float64)).sum(
        axis=2
    )
    expected = np.argsort(direct, axis=1, kind="stable")[:, :4]
    assert np.array_equal(labels, expected)
    assert np.allclose(distances, np.take_along_axis(direct, expected, axis=1))


def test_exact_angular_top_k_uses_normalized_inner_product() -> None:
    rng = np.random.default_rng(29)
    base = rng.normal(size=(23, 6)).astype(np.float64)
    queries = rng.normal(size=(5, 6)).astype(np.float64)
    base /= np.linalg.norm(base, axis=1, keepdims=True)
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)
    labels, distances = exact_top_k(
        base, queries, 3, metric="angular", query_batch=2, base_batch=7
    )
    direct = 1.0 - queries @ base.T
    expected = np.argsort(direct, axis=1, kind="stable")[:, :3]
    assert np.array_equal(labels, expected)
    assert np.allclose(distances, np.take_along_axis(direct, expected, axis=1))
