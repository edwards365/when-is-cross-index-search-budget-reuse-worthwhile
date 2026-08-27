"""Finite-environment overlap--separation lower-bound utilities."""
from __future__ import annotations


def normalize(weights):
    total = sum(weights)
    if total <= 0:
        raise ValueError("positive mass required")
    return [float(x) / total for x in weights]


def validate_inputs(p0, p1, active, delta):
    if len(p0) != len(p1):
        raise ValueError("aligned visible state spaces required")
    if delta < 0:
        raise ValueError("delta must be nonnegative")
    if any(i < 0 or i >= len(p0) for i in active):
        raise ValueError("active-set index outside state space")
    if abs(sum(p0) - 1.0) > 1e-9 or abs(sum(p1) - 1.0) > 1e-9:
        raise ValueError("probabilities must sum to one")


def total_variation(p0, p1):
    if len(p0) != len(p1):
        raise ValueError("aligned state spaces required")
    return 0.5 * sum(abs(a - b) for a, b in zip(p0, p1))


def overlap_separation_bound(p0, p1, active, delta, lam):
    validate_inputs(p0, p1, active, delta)
    if lam < 0:
        raise ValueError("lambda must be nonnegative")
    rho = min(sum(p0[i] for i in active), sum(p1[i] for i in active))
    return 0.5 * min(lam, 1.0) * delta * max(0.0, rho - total_variation(p0, p1))


def point_loss(action, sufficient_budget, lam):
    return lam * max(sufficient_budget - action, 0.0) + max(action - sufficient_budget, 0.0)


def first_crossing(quality, tau):
    return next((i for i, q in enumerate(quality) if q >= tau), None)


def stable_crossing(quality, tau):
    return next((i for i in range(len(quality)) if all(q >= tau for q in quality[i:])), None)
