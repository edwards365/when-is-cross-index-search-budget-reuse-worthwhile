import numpy as np

from theory.math_validation import (
    exhaustive_cardinality_optimum,
    frozen_objective,
    greedy_cardinality,
)


def test_frozen_greedy_matches_theoretical_factor_against_exhaustive_optimum():
    rng = np.random.default_rng(17)
    for _ in range(20):
        ground_size, dimension, budget = 9, 5, 4
        vectors = rng.normal(size=(ground_size, dimension))
        leverage = rng.uniform(size=ground_size)
        locality = rng.uniform(size=ground_size)

        def objective(
            mask,
            current_ground_size=ground_size,
            current_vectors=vectors,
            current_leverage=leverage,
            current_locality=locality,
        ):
            selected = [i for i in range(current_ground_size) if mask & (1 << i)]
            return frozen_objective(
                current_vectors,
                selected,
                current_leverage,
                current_locality,
                (0.7, 1.3, 0.5),
                sigma=0.8,
            )

        _, greedy_value = greedy_cardinality(ground_size, budget, objective)
        _, optimum_value = exhaustive_cardinality_optimum(ground_size, budget, objective)
        finite_bound = 1.0 - (1.0 - 1.0 / budget) ** budget
        assert greedy_value + 1e-10 >= finite_bound * optimum_value
