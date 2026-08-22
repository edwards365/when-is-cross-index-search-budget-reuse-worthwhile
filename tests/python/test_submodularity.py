import numpy as np

from theory.math_validation import (
    diminishing_returns_violations,
    direction_logdet,
    frozen_objective,
)
from theory.search_counterexamples import find_dynamic_leverage_violation


def test_direction_logdet_is_normalized_monotone_submodular():
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [-1.0, 0.2]])

    def objective(mask):
        return direction_logdet(
            vectors, [i for i in range(len(vectors)) if mask & (1 << i)], sigma=0.7
        )

    assert objective(0) == 0.0
    assert not diminishing_returns_violations(len(vectors), objective)
    assert all(
        objective(mask | (1 << v)) >= objective(mask)
        for mask in range(16)
        for v in range(4)
    )


def test_frozen_combination_is_submodular():
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [-1.0, 0.2]])
    leverage = np.array([1.0, 0.3, 0.5, 0.7])
    locality = np.array([0.1, 0.9, 0.4, 0.8])
    def objective(mask):
        return frozen_objective(
            vectors,
            [i for i in range(len(vectors)) if mask & (1 << i)],
            leverage,
            locality,
            (0.5, 2.0, 1.3),
            sigma=0.7,
        )

    assert not diminishing_returns_violations(len(vectors), objective)


def test_declared_dynamic_leverage_objective_is_not_submodular():
    counterexample = find_dynamic_leverage_violation(max_n=5)
    assert counterexample["delta_a"] < counterexample["delta_b"]
