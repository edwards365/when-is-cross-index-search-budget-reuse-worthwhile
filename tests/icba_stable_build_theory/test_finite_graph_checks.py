import importlib.util
import math
import sys
from pathlib import Path


MODULE = Path(__file__).resolve().parents[2] / "scripts" / "icba_stable_build_theory" / "finite_graph_checks.py"
SPEC = importlib.util.spec_from_file_location("finite_graph_checks", MODULE)
fg = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = fg
SPEC.loader.exec_module(fg)


def test_01_high_overlap_counterexample():
    j, a, b = fg.high_overlap_critical_edge_case(); assert j > .75 and a != b


def test_02_low_overlap_same_budget():
    j, a, b = fg.low_overlap_same_budget_case(); assert j < .5 and a == b


def test_03_all_counterexamples_pass():
    xs = fg.counterexamples(); assert len(xs) == 16 and all(x["passed"] for x in xs)


def test_04_random_search_has_witness():
    assert fg.random_small_graph_search(trials=1000)["witness"]


def test_05_random_search_reproducible():
    assert fg.random_small_graph_search(trials=400) == fg.random_small_graph_search(trials=400)


def test_06_target_at_entry_costs_one():
    r = fg.best_first_budget({"s": ()}, {"s": 0}, "s", "s"); assert r.budget == 1


def test_07_unreachable_is_infinite():
    r = fg.best_first_budget({"s": ()}, {"s": 1, "t": 0}, "s", "t"); assert math.isinf(r.budget)


def test_08_ties_use_node_id():
    r = fg.best_first_budget({"s": ("b", "a"), "a": (), "b": ()}, {"s": 2, "a": 1, "b": 1}, "s", "b"); assert r.trace == ("s", "a", "b")


def test_09_empty_graph_jaccard_one():
    assert fg.edge_jaccard({}, {}) == 1


def test_10_identical_graph_jaccard_one():
    g = {"a": ("b",)}; assert fg.edge_jaccard(g, g) == 1


def test_11_grid_shift_rounds_up():
    assert fg.grid_shift((1, 3, 7), 1, 1) == 3


def test_12_grid_shift_endpoint_infeasible():
    assert math.isinf(fg.grid_shift((1, 3, 7), 7, 1))


def test_13_quantile_tail():
    assert fg.empirical_quantile([0]*95+[100]*5, .96) == 100


def test_14_quantile_boundary():
    assert fg.empirical_quantile([1, 2, 3, 4], .5) == 2


def test_15_consensus_more_edges_wider_bound():
    assert fg.consensus_uniform_error_bound(100, 100, .05) > fg.consensus_uniform_error_bound(100, 10, .05)


def test_16_consensus_more_builds_tighter_bound():
    assert fg.consensus_uniform_error_bound(200, 10, .05) < fg.consensus_uniform_error_bound(100, 10, .05)


def test_17_positive_margin_finite_samples():
    assert math.isfinite(fg.hoeffding_certificate_size(.02, .05, 5))


def test_18_nonpositive_margin_infinite_samples():
    assert math.isinf(fg.hoeffding_certificate_size(0, .05))


def test_19_smaller_margin_more_samples():
    assert fg.hoeffding_certificate_size(.01, .05) > fg.hoeffding_certificate_size(.02, .05)


def test_20_more_candidates_more_samples():
    assert fg.hoeffding_certificate_size(.02, .05, 10) > fg.hoeffding_certificate_size(.02, .05, 1)


def test_21_kl_zero_on_diagonal():
    assert fg.bernoulli_kl(.05, .05) == 0


def test_22_kl_positive_off_diagonal():
    assert fg.bernoulli_kl(.04, .05) > 0


def test_23_positive_break_even():
    assert fg.break_even(100, .5) == 200


def test_24_no_finite_break_even():
    assert math.isinf(fg.break_even(100, 0))


def test_25_sanity_checks_all_hold():
    assert all(fg.theorem_sanity_checks().values())


def test_26_source_target_coupling_with_grid():
    grid=(1,2,4,8); assert all(fg.grid_shift(grid,s,2)>=t for s,t in zip((1,2,4),(2,4,4)))


def test_27_endpoint_is_not_numeric_stability():
    assert math.isinf(fg.grid_shift((1,2),2,1))


def test_28_counterexample_ids_unique():
    ids=[x["case_id"] for x in fg.counterexamples()]; assert len(ids)==len(set(ids))


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
    print(f"{len(tests)} tests passed")
