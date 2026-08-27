"""Finite-library Environment-Confidence Safe Envelope (ECSE).

This module is deliberately small: it implements a preregistered Bernoulli
sentinel model used for the synthetic closure, not a learned Graph-ANNS model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache


@lru_cache(maxsize=None)
def binom_pmf(x: int, n: int, p: float) -> float:
    if not 0 <= x <= n or not 0 <= p <= 1:
        return 0.0
    if p == 0:
        return float(x == 0)
    if p == 1:
        return float(x == n)
    return math.comb(n, x) * p**x * (1-p)**(n-x)


@lru_cache(maxsize=None)
def exact_equal_tail_accepts(successes: int, n: int, p: float, alpha: float) -> bool:
    """Conservative exact two-sided binomial acceptance test."""
    lower = sum(binom_pmf(i, n, p) for i in range(successes + 1))
    upper = sum(binom_pmf(i, n, p) for i in range(successes, n + 1))
    return lower > alpha / 2 and upper > alpha / 2


@dataclass(frozen=True)
class BernoulliEnvironment:
    name: str
    sentinel_p: float
    budgets: tuple[float, ...]


def nested_confidence_path(environments, observations, checkpoints, alpha=0.05):
    """Alpha-spent nested confidence sets at fixed checkpoints.

    Bonferroni spending across the nonzero checkpoints gives simultaneous
    true-environment coverage at least 1-alpha for a correctly specified
    finite Bernoulli library.
    """
    checkpoints = tuple(checkpoints)
    if not checkpoints or checkpoints[0] != 0 or any(a >= b for a, b in zip(checkpoints, checkpoints[1:])):
        raise ValueError("checkpoints must be strictly increasing and start at zero")
    if len(observations) < checkpoints[-1]:
        raise ValueError("insufficient sentinel observations")
    names = {e.name for e in environments}
    current = set(names)
    path = {0: frozenset(current)}
    per_check_alpha = alpha / max(1, len(checkpoints) - 1)
    for k in checkpoints[1:]:
        successes = sum(observations[:k])
        accepted = {e.name for e in environments
                    if exact_equal_tail_accepts(successes, k, e.sentinel_p, per_check_alpha)}
        current &= accepted
        path[k] = frozenset(current)
    return path


def ecse_allocation(environment_map, confidence_set, query_type, safe_endpoint):
    if not confidence_set:
        return safe_endpoint, True
    values = []
    for name in confidence_set:
        env = environment_map.get(name)
        if env is None or query_type >= len(env.budgets):
            return safe_endpoint, True
        values.append(env.budgets[query_type])
    return max(values), False


def ambiguity_diameter(environment_map, confidence_set, query_type):
    if not confidence_set:
        return 0.0
    values = [environment_map[name].budgets[query_type] for name in confidence_set]
    return max(values) - min(values)


def total_cost(mean_execution_cost, sentinel_cost, truth_cost, cert_cost, workload):
    if workload <= 0:
        raise ValueError("positive workload required")
    return mean_execution_cost + (sentinel_cost + truth_cost + cert_cost) / workload
