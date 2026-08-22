import inspect

import numpy as np
import pytest
from narhnsw.ggr import geometry_guarded_resistance_selection, geometry_objective


def fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    center = np.zeros(2)
    candidates = np.array(
        [[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [0.8, 0.8]]
    )
    leverage = np.array([0.1, 0.2, 0.3, 0.4, 2.0])
    return center, candidates, leverage


def test_ggr_is_query_independent_by_interface() -> None:
    parameters = inspect.signature(geometry_guarded_resistance_selection).parameters
    forbidden = {"query", "queries", "trace", "ground_truth", "failure"}
    assert forbidden.isdisjoint(parameters)


def test_geometry_objective_matches_greedy_start_and_guard() -> None:
    center, candidates, leverage = fixture()
    result = geometry_guarded_resistance_selection(
        center, candidates, leverage, 3, epsilon=0.01
    )
    assert result.geometry_base == pytest.approx(
        geometry_objective(center, candidates, result.geometry_selected)
    )
    assert result.geometry_final + result.geometry_allowance >= 0.99 * result.geometry_base


def test_ggr_preserves_cardinality_and_improves_frozen_leverage() -> None:
    center, candidates, leverage = fixture()
    result = geometry_guarded_resistance_selection(
        center, candidates, leverage, 3, epsilon=0.2
    )
    assert len(result.selected) == 3
    assert len(set(result.selected)) == 3
    assert result.leverage_final >= result.leverage_initial
    for swap in result.swaps:
        assert swap.leverage_after > swap.leverage_before + result.leverage_tolerance


def test_ggr_is_deterministic_and_terminates_at_registered_cap() -> None:
    args = (*fixture(), 3)
    first = geometry_guarded_resistance_selection(*args, epsilon=0.2)
    second = geometry_guarded_resistance_selection(*args, epsilon=0.2)
    assert first == second
    assert len(first.swaps) <= 3 * (5 - 3)
    assert first.termination in {"local_optimum", "max_swaps"}


def test_zero_epsilon_never_exceeds_numerical_geometry_loss() -> None:
    center, candidates, leverage = fixture()
    result = geometry_guarded_resistance_selection(center, candidates, leverage, 3)
    assert result.geometry_final + result.geometry_allowance >= result.geometry_base


def test_empty_candidate_set_returns_empty_selection() -> None:
    result = geometry_guarded_resistance_selection(
        np.zeros(2), np.empty((0, 2)), np.empty(0), 0
    )
    assert result.selected == ()
    assert result.geometry_final == 0.0
    assert result.termination == "local_optimum"


def test_geometry_guard_uses_registered_mixed_tolerance() -> None:
    center, candidates, leverage = fixture()
    result = geometry_guarded_resistance_selection(
        center,
        candidates,
        leverage,
        3,
        geometry_tolerance=2e-10,
        leverage_tolerance=3e-11,
    )
    assert result.geometry_allowance == pytest.approx(
        2e-10 * (1.0 + abs(result.geometry_base))
    )
    assert result.leverage_tolerance == 3e-11


def test_zero_tolerance_accepts_no_geometry_decrease() -> None:
    center, candidates, leverage = fixture()
    result = geometry_guarded_resistance_selection(
        center,
        candidates,
        leverage,
        3,
        geometry_tolerance=0.0,
        leverage_tolerance=0.0,
    )
    assert result.geometry_final >= result.geometry_base


@pytest.mark.parametrize("epsilon", [-0.1, 1.0, np.inf])
def test_ggr_rejects_invalid_epsilon(epsilon: float) -> None:
    center, candidates, leverage = fixture()
    with pytest.raises(ValueError, match="epsilon"):
        geometry_guarded_resistance_selection(
            center, candidates, leverage, 3, epsilon=epsilon
        )
