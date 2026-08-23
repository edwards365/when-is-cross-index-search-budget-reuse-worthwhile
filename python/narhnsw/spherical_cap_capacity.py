"""Spherical-cap mass and conservative finite-degree capacity bounds."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import betainc


def spherical_cap_mass(dimension: int, threshold: ArrayLike) -> NDArray[np.float64]:
    """Uniform S^(d-1) mass of {omega: <omega,d> > t} for t in [0,1]."""

    if dimension < 2:
        raise ValueError("dimension must be at least two")
    value = np.asarray(threshold, dtype=np.float64)
    if np.any(value < 0) or np.any(value > 1) or not np.isfinite(value).all():
        raise ValueError("threshold must lie in [0, 1]")
    return 0.5 * betainc((dimension - 1.0) / 2.0, 0.5, 1.0 - value * value)


def union_bound_capacity(dimension: int, thresholds: ArrayLike) -> float:
    """min(1, sum of individual cap masses)."""

    return min(1.0, float(np.sum(spherical_cap_mass(dimension, thresholds))))


def hoeffding_error_bound(samples: int, delta: float, comparisons: int = 1) -> float:
    """Union-bound epsilon with failure probability delta over fixed comparisons."""

    if samples <= 0 or comparisons <= 0 or not 0 < delta < 1:
        raise ValueError("invalid samples, comparisons, or delta")
    return float(np.sqrt(np.log(2.0 * comparisons / delta) / (2.0 * samples)))


def smooth_proxy_lipschitz(tau: float, max_scaled_edge: float, rho_min: float) -> float:
    """Conservative Lipschitz constant under ||domega||_2 + |drho|."""

    if tau <= 0 or max_scaled_edge < 0 or rho_min <= 0:
        raise ValueError("invalid smooth-proxy parameters")
    return max(1.0, max_scaled_edge / (2.0 * rho_min * rho_min)) / tau
