from __future__ import annotations

import math

import numpy as np
import pytest
from narhnsw.progress_conditions import (
    algorithm4_occlusion_threshold,
    beam_admission_threshold,
    multiplicative_path_step_bound,
    multiplicative_progress_threshold,
    strict_progress_threshold,
)


def unit(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


@pytest.mark.parametrize("seed", range(5))
def test_exact_progress_equivalences_random(seed: int) -> None:
    rng = np.random.default_rng(seed)
    for _ in range(1000):
        u = rng.normal(size=8)
        q = u + rng.normal(size=8)
        v = u + rng.normal(size=8)
        r = np.linalg.norm(q - u)
        s = np.linalg.norm(v - u)
        cosine = float(unit(q - u) @ unit(v - u))
        assert (np.linalg.norm(q - v) < r) == (cosine > strict_progress_threshold(s, r))


@pytest.mark.parametrize("eta", [0.0, 0.05, 0.25, 0.8])
def test_multiplicative_progress_equivalence(eta: float) -> None:
    rng = np.random.default_rng(100 + int(eta * 100))
    for _ in range(2000):
        r = rng.uniform(0.1, 5.0)
        s = rng.uniform(0.1, 5.0)
        cosine = rng.uniform(-1.0, 1.0)
        distance = math.sqrt(r * r + s * s - 2.0 * r * s * cosine)
        threshold = multiplicative_progress_threshold(s, r, eta)
        assert (distance <= (1.0 - eta) * r) == (cosine >= threshold)
        if threshold > 1:
            assert distance > (1.0 - eta) * r


def test_beam_admission_equivalence() -> None:
    rng = np.random.default_rng(77)
    for _ in range(2000):
        lam = rng.uniform(0.01, 5.0)
        b = rng.uniform(0.0, 3.0)
        cosine = rng.uniform(-1.0, 1.0)
        normalized_distance = math.sqrt(1.0 + lam * lam - 2.0 * lam * cosine)
        assert (normalized_distance < b) == (cosine > beam_admission_threshold(lam, b))


def test_algorithm4_length_angle_equivalence_and_equal_length_case() -> None:
    rng = np.random.default_rng(88)
    for _ in range(2000):
        s_v = rng.uniform(0.1, 5.0)
        s_w = rng.uniform(0.01, s_v)
        cosine = rng.uniform(-1.0, 1.0)
        v_w = math.sqrt(s_v * s_v + s_w * s_w - 2.0 * s_v * s_w * cosine)
        assert (v_w < s_v) == (cosine > algorithm4_occlusion_threshold(s_w, s_v))
    assert algorithm4_occlusion_threshold(2.0, 2.0) == pytest.approx(0.5)


def test_conditional_path_bound() -> None:
    steps = multiplicative_path_step_bound(100.0, 1.0, 0.1)
    assert (1.0 - 0.1) ** steps * 100.0 <= 1.0
    assert (1.0 - 0.1) ** (steps - 1) * 100.0 > 1.0
