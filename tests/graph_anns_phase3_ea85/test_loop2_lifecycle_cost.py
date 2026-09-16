import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/graph_anns_phase3_ea85/analyze_loop2_lifecycle_cost.py"
SPEC = importlib.util.spec_from_file_location("lifecycle", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_registered_horizons_and_truth_cost():
    assert MOD.N_GRID == (1000, 10000, 100000, 1000000, 10000000)
    assert MOD.TARGET_BASE_ROWS * (MOD.SELECTION_LABELS + MOD.CERTIFICATION_LABELS) == 100_000_000


def test_bootstrap_is_deterministic():
    values = np.asarray([1.0, 2.0, 4.0])
    assert MOD.bootstrap(values) == MOD.bootstrap(values)
    assert MOD.bootstrap_ratio(values, values) == (1.0, 1.0, 1.0)


def test_no_wall_clock_promotion_or_truth_access():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "EXPLORATORY_NOT_PROMOTED" in source
    assert '"raw_truth_accessed": False' in source
    assert "COMMON_CANCELS_SAME_TARGET_GRAPH" in source
