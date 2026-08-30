"""Finite checks for ICBA certification--fallback theory.

This module uses only finite enumeration and deterministic high-precision
arithmetic.  It does not read experiment data or sealed splits.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable, Sequence


def binom_cdf(k: int, n: int, p: float) -> float:
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return math.fsum(
        math.comb(n, j) * (p**j) * ((1.0 - p) ** (n - j))
        for j in range(k + 1)
    )


def cp_upper(k: int, n: int, alpha: float) -> float:
    """One-sided Clopper--Pearson upper endpoint."""
    if not (0 <= k <= n):
        raise ValueError("require 0 <= k <= n")
    if not (0.0 < alpha < 1.0):
        raise ValueError("require 0 < alpha < 1")
    if k == n:
        return 1.0
    lo = k / n
    hi = 1.0
    for _ in range(160):
        mid = (lo + hi) / 2.0
        if binom_cdf(k, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def zero_failure_threshold(delta: float, alpha: float) -> int:
    return math.ceil(math.log(alpha) / math.log(1.0 - delta))


def acceptance_cutoff(n: int, delta: float, alpha: float) -> int:
    # CP inversion gives U(k,n,alpha)<=delta iff
    # P_{delta}{Binomial(n,delta)<=k}<=alpha.  Accumulate the binomial
    # tail once instead of solving a beta quantile for every k.
    probability = (1.0 - delta) ** n
    cumulative = probability
    cutoff = 0 if cumulative <= alpha else -1
    if cumulative > alpha:
        return cutoff
    odds = delta / (1.0 - delta)
    for k in range(1, n + 1):
        probability *= (n - k + 1) / k * odds
        cumulative += probability
        if cumulative <= alpha:
            cutoff = k
        else:
            break
    return cutoff


def rejection_probability(n: int, risk: float, delta: float, alpha: float) -> float:
    cutoff = acceptance_cutoff(n, delta, alpha)
    return 1.0 - binom_cdf(cutoff, n, risk)


def discrete_quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("values must be nonempty")
    if not (0.0 < probability <= 1.0):
        raise ValueError("probability must be in (0,1]")
    ordered = sorted(values)
    return ordered[math.ceil(probability * len(ordered)) - 1]


def bernoulli_kl(p: float, q: float) -> float:
    if not (0.0 <= p <= 1.0 and 0.0 <= q <= 1.0):
        raise ValueError("probabilities must lie in [0,1]")
    terms = []
    if p > 0:
        terms.append(p * math.log(p / q))
    if p < 1:
        terms.append((1 - p) * math.log((1 - p) / (1 - q)))
    return math.fsum(terms)


def hoeffding_power_sample_size(
    gamma: float, alpha: float, family_size: int, beta: float
) -> int:
    """Sufficient m for UCB acceptance with probability at least 1-beta."""
    a = math.sqrt(math.log(family_size / alpha))
    b = math.sqrt(math.log(1.0 / beta))
    return math.ceil(((a + b) ** 2) / (2.0 * gamma**2))


def optimal_certification_grid(
    max_m: int,
    truth_cost: float,
    workload: int,
    fallback_gap: float,
    risk: float,
    delta: float,
    alpha: float,
) -> tuple[int, float]:
    best = None
    for m in range(1, max_m + 1):
        objective = (
            m * truth_cost / workload
            + rejection_probability(m, risk, delta, alpha) * fallback_gap
        )
        candidate = (objective, m)
        if best is None or candidate < best:
            best = candidate
    assert best is not None
    return best[1], best[0]


def counterexample_cases() -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []

    oracle_headroom = 10.0 - 8.0
    deployed_gain = oracle_headroom - 300.0 / 100.0
    cases.append({
        "case_id": "CE01_ORACLE_POSITIVE_DEPLOYMENT_NEGATIVE",
        "construction": "baseline=10, oracle=8, evidence=300, N=100",
        "computed_value": deployed_gain,
        "expected_relation": "oracle_headroom>0 and deployed_gain<0",
        "passed": oracle_headroom > 0 and deployed_gain < 0,
    })

    baseline = [10.0] * 100
    recovery = [0.0] * 94 + [11.0] * 6
    mean_gain = math.fsum(baseline) / 100 - math.fsum(recovery) / 100
    tail_change = discrete_quantile(recovery, 0.95) - discrete_quantile(baseline, 0.95)
    cases.append({
        "case_id": "CE02_MEAN_POSITIVE_P95_NEGATIVE",
        "construction": "baseline cost 10; recovery cost 0 w.p. .94 and 11 w.p. .06",
        "computed_value": f"mean_gain={mean_gain:.6f};p95_change={tail_change:.6f}",
        "expected_relation": "mean_gain>0 and p95_change>0",
        "passed": mean_gain > 0 and tail_change > 0,
    })

    u58 = cp_upper(0, 58, 0.05)
    cases.append({
        "case_id": "CE03_SAFE_BUT_REJECTED",
        "construction": "true risk=0, m=58, zero failures, delta=.05, alpha=.05",
        "computed_value": u58,
        "expected_relation": "CP upper > delta",
        "passed": u58 > 0.05,
    })

    unsafe_accept_probability = 0.94**59
    cases.append({
        "case_id": "CE04_UNSAFE_BUT_ACCEPTED",
        "construction": "true risk=.06, m=59, zero failures, delta=.05, alpha=.05",
        "computed_value": unsafe_accept_probability,
        "expected_relation": "0 < acceptance probability <= alpha",
        "passed": 0 < unsafe_accept_probability <= 0.05 and cp_upper(0, 59, 0.05) <= 0.05,
    })

    z1, z2 = (1, 0), (0, 1)
    cases.append({
        "case_id": "CE05_NON_NESTED_FAILURE_EVENTS",
        "construction": "two queries with Z1=(1,0), Z2=(0,1)",
        "computed_value": str(all(b <= a for a, b in zip(z1, z2))),
        "expected_relation": "pointwise nesting is false",
        "passed": not all(b <= a for a, b in zip(z1, z2)),
    })

    cases.append({
        "case_id": "CE06_ENDPOINT_CENSORING_SEMANTICS",
        "construction": "max-budget endpoint censored; naive under-budget=0; absolute failure=1",
        "computed_value": "naive=0;absolute=1",
        "expected_relation": "naive and absolute events differ",
        "passed": 0 != 1,
    })

    per_action_zero = 0.94**59
    post_selection = 1.0 - (1.0 - per_action_zero) ** 100
    cases.append({
        "case_id": "CE07_POST_SELECTION_COVERAGE_FAILURE",
        "construction": "100 unsafe actions, risk=.06, reuse 59 certification draws for selection",
        "computed_value": post_selection,
        "expected_relation": "family false acceptance > alpha",
        "passed": post_selection > 0.05,
    })

    u_single = cp_upper(0, 59, 0.05)
    u_bonf = cp_upper(0, 59, 0.05 / 10)
    cases.append({
        "case_id": "CE08_BONFERRONI_OVERCONSERVATIVE",
        "construction": "m=59, zero failures, delta=.05, alpha=.05, L=10",
        "computed_value": f"single={u_single:.8f};bonferroni={u_bonf:.8f}",
        "expected_relation": "single accepts and Bonferroni rejects",
        "passed": u_single <= 0.05 < u_bonf,
    })

    margin_m = hoeffding_power_sample_size(0.001, 0.05, 10, 0.10)
    cases.append({
        "case_id": "CE09_SMALL_MARGIN_SAMPLE_EXPLOSION",
        "construction": "gamma=.001, alpha=.05, L=10, beta=.10",
        "computed_value": margin_m,
        "expected_relation": "sufficient m exceeds one million",
        "passed": margin_m > 1_000_000,
    })

    remaining_margin = 2.0 - 0.20 * 15.0
    cases.append({
        "case_id": "CE10_FALLBACK_GAP_DESTROYS_VALUE",
        "construction": "oracle headroom=2, rejection=.20, fallback gap=15",
        "computed_value": remaining_margin,
        "expected_relation": "cost margin after fallback is negative",
        "passed": remaining_margin < 0,
    })

    denominator = 2.0 - 1.0 - 0.10 * 10.0
    cases.append({
        "case_id": "CE11_NO_FINITE_BREAK_EVEN",
        "construction": "headroom=2, selection regret=1, rejection=.1, gap=10",
        "computed_value": denominator,
        "expected_relation": "break-even denominator <= 0",
        "passed": denominator <= 0,
    })

    cases.append({
        "case_id": "CE12_FIXED_TARGET_NOT_OPEN_WORLD",
        "construction": "one policy has risk 0 on certified G0 and risk 1 on unseen G1",
        "computed_value": "r_G0=0;r_G1=1",
        "expected_relation": "fixed-target safety does not imply uniform safety",
        "passed": 0 <= 0.05 and 1 > 0.05,
    })

    direct = 10.0
    ladder = 0.5 * 9.0 + 0.5 * 10.0 + 1.5
    cases.append({
        "case_id": "CE13_FALLBACK_LADDER_ECONOMIC_FAILURE",
        "construction": "accept rung cost 9 w.p. .5; fallback 10; evidence tax 1.5",
        "computed_value": ladder - direct,
        "expected_relation": "ladder costs more than direct fixed-safe",
        "passed": ladder > direct,
    })

    m, alpha, family = 500, 0.05, 10
    dkw = math.sqrt(math.log(1.0 / alpha) / (2.0 * m))
    bonf = math.sqrt(math.log(family / alpha) / (2.0 * m))
    cases.append({
        "case_id": "CE14_NESTED_BAND_STRICT_RADIUS_GAIN",
        "construction": "one-sided DKW vs Bonferroni-Hoeffding, m=500, L=10",
        "computed_value": f"dkw={dkw:.8f};bonferroni={bonf:.8f}",
        "expected_relation": "nested DKW radius is strictly smaller",
        "passed": dkw < bonf,
    })

    return cases


def sample_complexity_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for delta in (0.10, 0.05, 0.01):
        for family in (1, 5, 20):
            local_alpha = 0.05 / family
            rows.append({
                "method": "zero_failure_clopper_pearson_bonferroni",
                "delta": delta,
                "alpha": 0.05,
                "family_size_L": family,
                "gamma": "",
                "beta_false_rejection": "",
                "m_sufficient": zero_failure_threshold(delta, local_alpha),
                "criterion": "U_CP(0,m,alpha/L)<=delta",
                "scope": "fixed target; iid certification queries",
            })
    for delta, gamma in ((0.10, 0.02), (0.05, 0.01), (0.01, 0.002)):
        for family in (1, 5, 20):
            rows.append({
                "method": "hoeffding_bonferroni_power",
                "delta": delta,
                "alpha": 0.05,
                "family_size_L": family,
                "gamma": gamma,
                "beta_false_rejection": 0.10,
                "m_sufficient": hoeffding_power_sample_size(gamma, 0.05, family, 0.10),
                "criterion": "P(safe-but-rejected)<=beta",
                "scope": "fixed target; finite family",
            })
            risk = delta - gamma
            rows.append({
                "method": "bernoulli_kl_leading_order",
                "delta": delta,
                "alpha": 0.05,
                "family_size_L": family,
                "gamma": gamma,
                "beta_false_rejection": "asymptotic",
                "m_sufficient": math.ceil(math.log(family / 0.05) / bernoulli_kl(risk, delta)),
                "criterion": "leading log(L/alpha)/kl(delta-gamma||delta)",
                "scope": "rate guide; exact deployment uses binomial inversion",
            })
    return rows


THEOREM_LEDGER = [
    ["T-CF1", "Certification--Fallback Tax identity", "FORMAL_PROOF_COMPLETE", "IDENTITY_OR_DEFINITION", "fixed target and optional explicit joint environment law", "exact expectation identity; no p95 implication"],
    ["T-CF2", "positive net deployment value and break-even", "FORMAL_PROOF_COMPLETE", "RESTRICTED_DOMAIN_PROPOSITION", "fixed target", "necessary and sufficient after all costs share units"],
    ["T-CF3", "ordered independent certification and safe selection", "FORMAL_PROOF_COMPLETE", "NEW_COMBINATION_OF_CLASSICAL_RESULTS", "fixed target", "Bonferroni, fixed sequence, and nested DKW variants"],
    ["T-CF4", "safety margin and certification sample complexity", "FORMAL_PROOF_COMPLETE", "CLASSICAL_APPLICATION", "fixed target", "CP/Hoeffding/Bernoulli-KL; no build-count claim"],
    ["T-CF5", "ordered fallback ladder cost and safety", "FORMAL_PROOF_COMPLETE", "NEW_COMBINATION_OF_CLASSICAL_RESULTS", "fixed target", "strict value requires expected saved gap to exceed evidence/control tax"],
    ["T-CF6", "stable-by-construction interface", "FORMAL_PROOF_COMPLETE_CONDITIONAL", "RESTRICTED_DOMAIN_PROPOSITION", "source-target pair satisfying assumed metric bound", "no validated deployable graph distance"],
]


CONTRACT_ROWS = [
    ["A_NESTED_EVENTS", "T-CF3,T-CF4,T-CF5", "Z_{l+1}(q)<=Z_l(q) for every certification query", "per-query per-rung absolute failure indicators", "independent target certification only", "nesting violation count", "zero violations", "use unstructured simultaneous bounds; ordered power result disabled"],
    ["A_POSITIVE_SAFETY_MARGIN", "T-CF4,T-CF6", "gamma_l=delta-r_G(pi_l)>0 for at least one useful rung", "failure counts and one-sided UCB", "independent target certification only", "lower confidence bound on gamma or U_l", "U_l<delta for a useful rung", "sample demand can diverge and safe action can be rejected"],
    ["A_SAFE_RUNG_EXISTS", "T-CF3,T-CF5", "some candidate or externally certified terminal policy has risk <= delta", "certificate decisions and endpoint status", "independent target certification plus registered fallback", "certified rung count", "at least one certified candidate or valid fixed-safe", "abstain; no safety claim from maximum observed budget"],
    ["A_FALSE_REJECTION_CONTROLLABLE", "T-CF4,T-CF5", "P(reject safe rung) small enough for value", "accept/reject indicator by rung", "independent target certification only", "false-rejection bound or exact binomial power", "bound below preregistered economic threshold", "fallback tax may dominate despite statistical safety"],
    ["A_FALLBACK_GAP_REDUCIBLE", "T-CF2,T-CF5", "E[(C_fixed-C_J)1{J certified}] exceeds ladder overhead", "search cost by deployed rung and fallback", "target deployment accounting; no sealed evaluation truth", "expected saved fallback gap", "saved gap > evidence/N + incremental control", "direct fixed-safe dominates ladder"],
    ["A_POSITIVE_COST_MARGIN", "T-CF2", "G_oracle-R_selection-T_fallback-T_control>0", "compatible-unit cost components", "frozen exploratory or future nonsealed confirmation", "break-even denominator", "strictly positive", "NO_FINITE_BREAK_EVEN_WORKLOAD"],
    ["A_FIXED_TARGET_INDEPENDENCE", "T-CF3,T-CF4", "D_cert independent of selection and evaluation conditional on named G", "query IDs and role manifest", "target selection/certification/evaluation roles", "overlap count and sampling design", "zero overlap and valid iid/exchangeable certificate unit", "selected-action proof invalid; require simultaneous/selection-aware control"],
    ["A_OUTER_BUILD_SUPPORT", "T-CF6", "outer-build claim requires explicit build law/support and independent builds", "build IDs, construction law, support descriptors", "future build-level study only", "build-level coverage/support diagnostic", "preregistered support condition and build-level calibration", "remain fixed-target; no open-world inference"],
]


def write_csv(path: Path, header: Iterable[str], rows: Iterable[Iterable[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(list(header))
        writer.writerows(rows)


def build_outputs(root: Path) -> None:
    results = root / "results" / "icba_certification_fallback_theory"
    write_csv(
        results / "theorem_ledger.csv",
        ["theorem_id", "title", "proof_status", "novelty_class", "scope", "qualification"],
        THEOREM_LEDGER,
    )
    write_csv(
        results / "theorem_experiment_contract.csv",
        ["assumption_id", "theorem_id", "mathematical_statement", "observable_field", "required_dataset_scope", "required_statistic", "pass_condition", "failure_interpretation"],
        CONTRACT_ROWS,
    )
    cases = counterexample_cases()
    write_csv(
        results / "counterexamples.csv",
        ["case_id", "construction", "computed_value", "expected_relation", "passed"],
        ([c["case_id"], c["construction"], c["computed_value"], c["expected_relation"], c["passed"]] for c in cases),
    )
    rows = sample_complexity_rows()
    write_csv(
        results / "sample_complexity_table.csv",
        ["method", "delta", "alpha", "family_size_L", "gamma", "beta_false_rejection", "m_sufficient", "criterion", "scope"],
        ([r[k] for k in ["method", "delta", "alpha", "family_size_L", "gamma", "beta_false_rejection", "m_sufficient", "criterion", "scope"]] for r in rows),
    )


def self_check() -> dict[str, object]:
    cases = counterexample_cases()
    assert len(cases) >= 12
    assert all(bool(c["passed"]) for c in cases)
    assert zero_failure_threshold(0.10, 0.05) == 29
    assert zero_failure_threshold(0.05, 0.05) == 59
    assert zero_failure_threshold(0.01, 0.05) == 299
    assert abs(cp_upper(0, 59, 0.05) - (1 - 0.05 ** (1 / 59))) < 1e-12
    m_star, objective = optimal_certification_grid(500, 1.0, 10_000, 10.0, 0.03, 0.05, 0.05)
    assert 1 <= m_star <= 500 and objective >= 0
    return {"counterexamples": len(cases), "all_passed": True, "grid_m_star": m_star}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    build_outputs(root)
    print(json.dumps(self_check(), sort_keys=True))
