import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[2] / "scripts" / "sigmod_ea_limitation_closure" / "audit_equal_information_baselines.py"
SPEC = importlib.util.spec_from_file_location("audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


class Dummy:
    EFS = np.array([10, 20, 40])

    @staticmethod
    def cp_upper(failures, n, confidence):
        del n, confidence
        return [0.01, 0.08, 0.12][failures]


def test_target_global_selects_first_passing_action():
    recalls = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 1.0]])
    assert AUDIT.target_global_action(Dummy, recalls) == 1


def test_source_global_requires_every_source_build():
    source = {
        1: np.array([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]]),
        2: np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 1.0]]),
        3: np.array([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]]),
    }
    assert AUDIT.source_global_action(Dummy, source, target_seed=3) == 1


def test_crossed_bootstrap_is_deterministic():
    values = {"x": np.arange(12, dtype=float).reshape(3, 4)}
    first = AUDIT.crossed_draws(values, reps=20, seed=991)["x"]
    second = AUDIT.crossed_draws(values, reps=20, seed=991)["x"]
    assert np.array_equal(first, second)
