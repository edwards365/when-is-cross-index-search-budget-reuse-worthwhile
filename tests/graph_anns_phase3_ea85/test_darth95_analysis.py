#!/usr/bin/env python3
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/graph_anns_phase3_ea85/analyze_darth95_bridge.py"
SPEC = importlib.util.spec_from_file_location("darth95", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_cp_upper_zero_failures_is_above_zero():
    value = MODULE.cp_upper(0, 500)
    assert 0.0 < value < 0.01


def test_cp_upper_rejects_many_failures():
    assert MODULE.cp_upper(30, 500) > 0.05


def test_registered_primary_unit_and_reps():
    assert MODULE.REPS == 5000
    assert MODULE.RNG_SEED == 991
    assert len(MODULE.SEEDS) == 10
