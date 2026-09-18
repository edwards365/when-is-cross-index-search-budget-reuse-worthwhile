import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[2] / "scripts" / "sigmod_ea_limitation_closure" / "audit_grid_risk_sensitivity.py"
SPEC = importlib.util.spec_from_file_location("sensitivity", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_minima_uses_first_passing_and_endpoint_for_unresolved():
    recalls = np.array([[0.8, 0.8], [0.9, 0.8], [1.0, 0.8]])
    assert np.array_equal(MODULE.minima(recalls, 0.9), np.array([1, 2]))


def test_condition_names_are_unique_and_primary_first():
    names = [row[0] for row in MODULE.CONDITIONS]
    assert names[0] == "primary"
    assert len(names) == len(set(names))
