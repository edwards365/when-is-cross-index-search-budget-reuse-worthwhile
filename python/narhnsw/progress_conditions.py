"""Exact local Euclidean navigation conditions used by GB-MPCC."""

from __future__ import annotations

import math


def strict_progress_threshold(edge_length: float, query_radius: float) -> float:
    """Cosine threshold for ||q-v|| < ||q-u||."""

    if edge_length <= 0 or query_radius <= 0:
        raise ValueError("edge length and query radius must be positive")
    return edge_length / (2.0 * query_radius)


def multiplicative_progress_threshold(
    edge_length: float, query_radius: float, eta: float
) -> float:
    """Cosine threshold for ||q-v|| <= (1-eta)||q-u||."""

    if edge_length <= 0 or query_radius <= 0:
        raise ValueError("edge length and query radius must be positive")
    if not 0 <= eta < 1:
        raise ValueError("eta must be in [0, 1)")
    return edge_length / (2.0 * query_radius) + (
        (2.0 * eta - eta * eta) * query_radius / (2.0 * edge_length)
    )


def beam_admission_threshold(edge_radius_ratio: float, boundary_ratio: float) -> float:
    """Cosine threshold for ||q-v|| < b||q-u||, with lambda=||v-u||/||q-u||."""

    if edge_radius_ratio <= 0 or boundary_ratio < 0:
        raise ValueError("lambda must be positive and b must be nonnegative")
    return (
        1.0 + edge_radius_ratio * edge_radius_ratio - boundary_ratio * boundary_ratio
    ) / (2.0 * edge_radius_ratio)


def algorithm4_occlusion_threshold(shorter_length: float, candidate_length: float) -> float:
    """Cosine threshold equivalent to ||v-w|| < ||v-u||."""

    if shorter_length <= 0 or candidate_length <= 0:
        raise ValueError("edge lengths must be positive")
    if shorter_length > candidate_length:
        raise ValueError("Algorithm 4 processes the shorter/equal edge first")
    return shorter_length / (2.0 * candidate_length)


def multiplicative_path_step_bound(r0: float, r_min: float, eta: float) -> int:
    """Conditional number of eta-progress steps sufficient to reach r_min."""

    if r0 <= 0 or r_min <= 0 or r_min > r0:
        raise ValueError("require 0 < r_min <= r0")
    if not 0 < eta < 1:
        raise ValueError("eta must be in (0, 1)")
    return math.ceil(math.log(r0 / r_min) / -math.log1p(-eta))
