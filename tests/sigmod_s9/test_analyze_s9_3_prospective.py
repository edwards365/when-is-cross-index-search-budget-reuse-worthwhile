import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "scripts" / "sigmod_s9" / "analyze_s9_3_prospective.py"
SPEC = importlib.util.spec_from_file_location("s9p3_analysis", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_cp_upper_zero_failures_matches_closed_form():
    expected = 1.0 - 0.025 ** (1.0 / 500.0)
    assert abs(MODULE.cp_upper(0, 500, 0.025) - expected) < 1e-12


def test_next_rung_clips_at_endpoint():
    assert MODULE.next_rung(64, MODULE.GRID) == 128
    assert MODULE.next_rung(512, MODULE.GRID) == 512
