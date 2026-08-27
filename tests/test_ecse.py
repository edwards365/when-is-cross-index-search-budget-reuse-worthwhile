import importlib.util
import itertools
import sys
from pathlib import Path


MODULE = Path(__file__).parents[1] / "src" / "icba_micro_closure" / "ecse.py"
SPEC = importlib.util.spec_from_file_location("ecse", MODULE)
E = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = E
SPEC.loader.exec_module(E)


def library():
    envs = [
        E.BernoulliEnvironment("low", 0.2, (0.2, 0.5, 0.8)),
        E.BernoulliEnvironment("mid", 0.5, (0.4, 0.6, 0.9)),
        E.BernoulliEnvironment("high", 0.8, (0.6, 0.8, 1.0)),
    ]
    return envs, {x.name: x for x in envs}


def test_confidence_sets_are_nested():
    envs, _ = library()
    path = E.nested_confidence_path(envs, [1, 0] * 128, (0, 8, 16, 32, 64, 128, 256))
    keys = sorted(path)
    assert all(path[b] <= path[a] for a, b in zip(keys, keys[1:]))


def test_envelope_nonincreasing_for_nested_sets():
    _, env = library()
    sets = [frozenset(env), frozenset({"mid", "high"}), frozenset({"mid"})]
    allocations = [E.ecse_allocation(env, s, 1, 1.0)[0] for s in sets]
    assert allocations == sorted(allocations, reverse=True)


def test_empty_set_fails_closed():
    _, env = library()
    allocation, fallback = E.ecse_allocation(env, frozenset(), 0, 1.0)
    assert fallback and allocation == 1.0


def test_true_environment_in_set_implies_envelope_safety():
    _, env = library()
    for target in env:
        for subset_size in range(1, 4):
            for names in itertools.combinations(env, subset_size):
                if target not in names:
                    continue
                names = frozenset(names)
                for q in range(3):
                    allocation, _ = E.ecse_allocation(env, names, q, 1.0)
                    assert allocation >= env[target].budgets[q]


def test_nonnested_sets_can_increase_envelope_counterexample():
    _, env = library()
    low = E.ecse_allocation(env, frozenset({"low"}), 0, 1.0)[0]
    high = E.ecse_allocation(env, frozenset({"high"}), 0, 1.0)[0]
    assert high > low


def test_probe_adjusted_cost_can_increase():
    assert E.total_cost(0.5, 100, 0, 0, 100) > E.total_cost(0.6, 0, 0, 0, 100)


def test_exact_confidence_constructor_has_conservative_coverage_small_n():
    alpha = 0.05
    envs = [E.BernoulliEnvironment(f"t{p}", p, (0.5,)) for p in (0.2, 0.5, 0.8)]
    for target in envs:
        failure = 0.0
        n = 8
        for x in range(n + 1):
            probability = E.binom_pmf(x, n, target.sentinel_p)
            obs = [1] * x + [0] * (n - x)
            path = E.nested_confidence_path(envs, obs, (0, n), alpha)
            if target.name not in path[n]:
                failure += probability
        assert failure <= alpha + 1e-12


def test_mutually_singular_two_environment_class_identifies_exactly():
    envs = [E.BernoulliEnvironment("zero", 0.0, (0.2, 0.8)),
            E.BernoulliEnvironment("one", 1.0, (0.6, 1.0))]
    for target, observation in ((envs[0], 0), (envs[1], 1)):
        path = E.nested_confidence_path(envs, [observation] * 8, (0, 8), 0.05)
        assert path[8] == frozenset({target.name})
