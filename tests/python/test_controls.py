import inspect

import numpy as np
from narhnsw.controls import (
    geometry_safe_random_selection,
    shuffled_resistance_selection,
)


def fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(41)
    center = np.zeros(5)
    candidates = rng.normal(size=(12, 5))
    leverage = np.linspace(0.01, 1.0, len(candidates))
    return center, candidates, leverage


def test_geometry_safe_random_is_deterministic_and_matches_budget() -> None:
    center, candidates, _ = fixture()
    first = geometry_safe_random_selection(
        center, candidates, 6, requested_swaps=4, seed=313, epsilon=0.05
    )
    repeated = geometry_safe_random_selection(
        center, candidates, 6, requested_swaps=4, seed=313, epsilon=0.05
    )
    assert first == repeated
    assert first.termination == "matched_swap_budget"
    assert len(first.swaps) == 4
    assert len(first.selected) == 6
    assert len(set(first.selected)) == 6
    assert first.geometry_final + first.geometry_allowance >= 0.95 * first.geometry_base


def test_geometry_safe_random_uses_no_resistance_or_query_input() -> None:
    parameters = inspect.signature(geometry_safe_random_selection).parameters
    assert "leverage" not in parameters
    assert "query" not in parameters
    assert "ground_truth" not in parameters


def test_shuffled_resistance_is_a_deterministic_within_pool_permutation() -> None:
    center, candidates, leverage = fixture()
    first = shuffled_resistance_selection(
        center, candidates, leverage, 6, seed=991, epsilon=0.0
    )
    repeated = shuffled_resistance_selection(
        center, candidates, leverage, 6, seed=991, epsilon=0.0
    )
    assert first == repeated
    assert sorted(first.permutation) == list(range(len(candidates)))
    assert first.permutation != tuple(range(len(candidates)))
    assert len(first.selection.selected) == 6
    assert first.selection.geometry_final + first.selection.geometry_allowance >= (
        first.selection.geometry_base
    )
