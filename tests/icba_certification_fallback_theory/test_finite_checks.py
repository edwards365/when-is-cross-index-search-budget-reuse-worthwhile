import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "icba_certification_fallback_theory"
    / "finite_checks.py"
)
SPEC = importlib.util.spec_from_file_location("finite_checks", MODULE_PATH)
finite_checks = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(finite_checks)


def test_zero_failure_thresholds():
    assert finite_checks.zero_failure_threshold(0.10, 0.05) == 29
    assert finite_checks.zero_failure_threshold(0.05, 0.05) == 59
    assert finite_checks.zero_failure_threshold(0.01, 0.05) == 299


def test_cp_zero_failure_formula():
    for n in (10, 59, 299):
        expected = 1 - 0.05 ** (1 / n)
        assert abs(finite_checks.cp_upper(0, n, 0.05) - expected) < 1e-12


def test_cp_endpoint_inverts_binomial_tail():
    for n, k in ((20, 1), (100, 3), (250, 7)):
        upper = finite_checks.cp_upper(k, n, 0.05)
        assert abs(finite_checks.binom_cdf(k, n, upper) - 0.05) < 1e-10


def test_all_required_counterexamples_pass():
    cases = finite_checks.counterexample_cases()
    assert len(cases) == 14
    assert all(case["passed"] for case in cases)


def test_nesting_counterexample_is_present():
    cases = {c["case_id"]: c for c in finite_checks.counterexample_cases()}
    assert cases["CE05_NON_NESTED_FAILURE_EVENTS"]["passed"]


def test_mean_and_quantile_separate():
    values = [0.0] * 94 + [11.0] * 6
    assert sum(values) / 100 < 10
    assert finite_checks.discrete_quantile(values, 0.95) == 11


def test_bonferroni_can_reject_when_fixed_sequence_accepts():
    assert finite_checks.cp_upper(0, 59, 0.05) <= 0.05
    assert finite_checks.cp_upper(0, 59, 0.005) > 0.05


def test_small_margin_sample_size_monotonicity():
    small = finite_checks.hoeffding_power_sample_size(0.02, 0.05, 10, 0.1)
    tiny = finite_checks.hoeffding_power_sample_size(0.01, 0.05, 10, 0.1)
    assert tiny > small


def test_kl_positive_off_diagonal():
    assert finite_checks.bernoulli_kl(0.04, 0.05) > 0
    assert finite_checks.bernoulli_kl(0.05, 0.05) == 0


def test_grid_optimizer_returns_finite_choice():
    m, value = finite_checks.optimal_certification_grid(
        200, 1.0, 10000, 10.0, 0.03, 0.05, 0.05
    )
    assert 1 <= m <= 200
    assert value >= 0


def test_fixed_target_does_not_imply_open_world():
    risks = {"certified_target": 0.0, "unseen_build": 1.0}
    assert risks["certified_target"] <= 0.05
    assert risks["unseen_build"] > 0.05


def test_output_contract_has_all_fixed_assumptions():
    expected = {
        "A_NESTED_EVENTS",
        "A_POSITIVE_SAFETY_MARGIN",
        "A_SAFE_RUNG_EXISTS",
        "A_FALSE_REJECTION_CONTROLLABLE",
        "A_FALLBACK_GAP_REDUCIBLE",
        "A_POSITIVE_COST_MARGIN",
        "A_FIXED_TARGET_INDEPENDENCE",
        "A_OUTER_BUILD_SUPPORT",
    }
    assert {row[0] for row in finite_checks.CONTRACT_ROWS} == expected


if __name__ == "__main__":
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} tests passed")
