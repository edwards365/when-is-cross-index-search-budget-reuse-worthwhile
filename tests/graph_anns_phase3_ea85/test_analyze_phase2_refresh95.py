import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[2] / "scripts/graph_anns_phase3_ea85/analyze_phase2_refresh95.py"
SPEC = importlib.util.spec_from_file_location("refresh95", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_cp_upper_zero_failures_requires_enough_samples():
    assert MOD.cp_upper(0, 500) < 0.05
    assert MOD.cp_upper(0, 58) > 0.05
    assert MOD.cp_upper(0, 59) < 0.05


def test_minimal_action_uses_first_success_and_endpoint_for_bot():
    recalls = np.array([
        [0.9, 0.8, 0.7],
        [1.0, 0.9, 0.8],
        [1.0, 1.0, 0.9],
        [1.0, 1.0, 0.9],
        [1.0, 1.0, 0.9],
        [1.0, 1.0, 0.9],
        [1.0, 1.0, 0.9],
    ])
    assert MOD.minimal_action_indices(recalls).tolist() == [1, 2, 6]


def test_source_pool_is_leave_one_build_out_maximum():
    minima = {seed: np.array([i % 7, (i + 1) % 7]) for i, seed in enumerate(MOD.SEEDS)}
    pooled = MOD.source_pool_indices(minima, MOD.SEEDS[-1])
    expected = np.max(np.stack([minima[s] for s in MOD.SEEDS[:-1]]), axis=0)
    assert np.array_equal(pooled, expected)


def test_shift_clamps_to_endpoint():
    assert MOD.shift_indices(np.array([0, 5, 6]), 2).tolist() == [2, 6, 6]


def test_choose_shift_is_smallest_certifiable_shift():
    recalls = np.zeros((7, 500))
    recalls[2:, :] = 1.0
    base = np.zeros(500, dtype=int)
    shift, ucb, failures = MOD.choose_shift(recalls, base)
    assert shift == 2
    assert failures == 0
    assert ucb < 0.05


def test_sequential_profile_cost_stops_at_registered_rung():
    dists = np.array([[1, 10], [2, 20], [4, 40]], dtype=float)
    assert MOD.sequential_profile_cost(dists, np.array([1, 2])) == 3 + 70
