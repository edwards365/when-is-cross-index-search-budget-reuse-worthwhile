import importlib.util
import itertools
import math
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "icba_micro_closure" / "lower_bound.py"
SPEC = importlib.util.spec_from_file_location("icba_lower_bound", MODULE)
LB = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(LB)


def test_preregistered_sizes_and_budget_levels():
    for n in range(2, 9):
        for levels in range(2, 7):
            actions = [i / (levels - 1) for i in range(levels)]
            p0 = LB.normalize([i + 1 for i in range(n)])
            p1 = LB.normalize([n - i for i in range(n)])
            b0 = [actions[i % levels] for i in range(n)]
            b1 = [min(1.0, x + 1 / (levels - 1)) for x in b0]
            delta = 1 / (levels - 1)
            active = [i for i in range(n) if b1[i] - b0[i] >= delta - 1e-12]
            bound = LB.overlap_separation_bound(p0, p1, active, delta, 1.0)
            for z in active:
                for a in actions:
                    lhs = LB.point_loss(a, b0[z], 1.0) + LB.point_loss(a, b1[z], 1.0)
                    assert lhs + 1e-12 >= delta
            assert bound >= 0.0


def test_randomized_policies_do_not_break_pointwise_bound():
    weights = [0.1, 0.2, 0.7]
    actions = [0.0, 0.5, 1.0]
    b0, b1, lam = 0.1, 0.8, 0.4
    mixed = sum(w * (LB.point_loss(a, b0, lam) + LB.point_loss(a, b1, lam))
                for w, a in zip(weights, actions))
    assert mixed + 1e-12 >= min(lam, 1.0) * (b1 - b0)


def test_tv_zero_positive_and_tv_one_zero():
    p = [0.5, 0.5]
    assert LB.overlap_separation_bound(p, p, [0, 1], 0.5, 1.0) == 0.25
    assert LB.overlap_separation_bound([1, 0], [0, 1], [0, 1], 0.5, 1.0) == 0.0


def test_delta_zero_and_zero_mass_are_zero():
    p = [0.5, 0.5]
    assert LB.overlap_separation_bound(p, p, [0, 1], 0.0, 1.0) == 0.0
    assert LB.overlap_separation_bound(p, p, [], 0.5, 1.0) == 0.0


def test_fully_aliased_single_type_is_sharp():
    # Equal-prior two-environment game with endpoints 0 and Delta.
    delta = 0.6
    values = []
    for a in [i / 1000 for i in range(1001)]:
        values.append(max(LB.point_loss(a, 0.0, 1.0), LB.point_loss(a, delta, 1.0)))
    exact = min(values)
    assert abs(exact - delta / 2) <= 0.001


def test_nonmonotone_quality_requires_stable_tail():
    quality = [0.91, 0.89, 0.92]
    assert LB.first_crossing(quality, 0.9) == 0
    assert LB.stable_crossing(quality, 0.9) == 2


def test_right_censoring_is_not_max_budget_label():
    assert LB.stable_crossing([0.7, 0.8, 0.89], 0.9) is None


def test_unaligned_histograms_rejected():
    try:
        LB.validate_inputs([0.5, 0.5], [0.5], [0], 0.1)
    except ValueError:
        pass
    else:
        raise AssertionError("unaligned environments must be rejected")
