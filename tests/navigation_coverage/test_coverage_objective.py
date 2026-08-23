from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
from narhnsw.coverage_objective import (
    greedy_incremental_hard_coverage,
    hard_coverage,
    incremental_hard_coverage,
    smooth_coverage,
    smooth_scores,
)
from narhnsw.spherical_cap_capacity import (
    hoeffding_error_bound,
    smooth_proxy_lipschitz,
    spherical_cap_mass,
    union_bound_capacity,
)


def powerset(size: int) -> list[frozenset[int]]:
    return [
        frozenset(values)
        for count in range(size + 1)
        for values in itertools.combinations(range(size), count)
    ]


@pytest.mark.parametrize("smooth", [False, True])
def test_exhaustive_normalized_monotone_submodular(smooth: bool) -> None:
    rng = np.random.default_rng(20260824)
    values = rng.random((5, 12))
    objective = (
        (lambda selected: smooth_coverage(values, selected))
        if smooth
        else (lambda selected: hard_coverage(values > 0.55, selected))
    )
    subsets = powerset(5)
    assert objective(frozenset()) == 0.0
    for left in subsets:
        for right in subsets:
            if left <= right:
                assert objective(left) <= objective(right) + 1e-15
                for element in set(range(5)) - set(right):
                    left_gain = objective(left | {element}) - objective(left)
                    right_gain = objective(right | {element}) - objective(right)
                    assert left_gain + 1e-15 >= right_gain


def test_frozen_backbone_increment_is_submodular_and_greedy_bound_holds() -> None:
    rng = np.random.default_rng(4)
    masks = rng.random((7, 30)) > 0.65
    backbone = (0, 1)
    candidates = tuple(range(2, 7))
    for left in powerset(len(candidates)):
        mapped_left = {candidates[index] for index in left}
        for right in powerset(len(candidates)):
            mapped_right = {candidates[index] for index in right}
            if mapped_left <= mapped_right:
                for element in set(candidates) - mapped_right:
                    left_gain = incremental_hard_coverage(
                        masks, backbone, mapped_left | {element}
                    ) - incremental_hard_coverage(masks, backbone, mapped_left)
                    right_gain = incremental_hard_coverage(
                        masks, backbone, mapped_right | {element}
                    ) - incremental_hard_coverage(masks, backbone, mapped_right)
                    assert left_gain + 1e-15 >= right_gain
    greedy = greedy_incremental_hard_coverage(masks, backbone, candidates, 3)
    greedy_value = incremental_hard_coverage(masks, backbone, greedy)
    optimum = max(
        incremental_hard_coverage(masks, backbone, selected)
        for selected in itertools.combinations(candidates, 3)
    )
    assert greedy_value + 1e-15 >= (1.0 - 1.0 / math.e) * optimum


def test_smooth_scores_and_capacity_formulas() -> None:
    margins = np.array([-0.2, 0.0, 0.025, 0.05, 0.2])
    assert smooth_scores(margins, 0.05).tolist() == [0.0, 0.0, 0.5, 1.0, 1.0]
    assert spherical_cap_mass(3, 0.0) == pytest.approx(0.5)
    assert spherical_cap_mass(3, 0.5) == pytest.approx(0.25)
    assert spherical_cap_mass(3, 1.0) == pytest.approx(0.0)
    assert union_bound_capacity(3, [0.5, 0.5]) == pytest.approx(0.5)
    assert hoeffding_error_bound(2048, 0.05, 1) > 0
    assert smooth_proxy_lipschitz(0.05, 3.0, 0.5) == pytest.approx(120.0)
