import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[2] / "scripts/graph_anns_phase3_ea85/analyze_phase4_deep1m.py"
SPEC = importlib.util.spec_from_file_location("p4", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_minimum_indices_marks_endpoint_censoring():
    recalls = np.array([[0.9, 0.8], [1.0, 0.8], [1.0, 0.8], [1.0, 0.8], [1.0, 0.8], [1.0, 0.8]])
    idx, finite = MOD.minimum_indices(recalls)
    assert idx.tolist() == [1, 5]
    assert finite.tolist() == [True, False]


def test_build_bootstrap_deterministic():
    rows = [{"x": 0.1}, {"x": 0.2}, {"x": 0.3}]
    assert MOD.build_bootstrap(rows, "x", reps=50) == MOD.build_bootstrap(rows, "x", reps=50)
