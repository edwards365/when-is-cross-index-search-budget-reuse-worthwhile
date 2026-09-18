import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "scripts" / "sigmod_s9" / "analyze_s9_4_arms.py"
SPEC = importlib.util.spec_from_file_location("s9p4_arms", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_cp_upper_zero_failures():
    expected = 1.0 - 0.025 ** (1.0 / 500.0)
    assert abs(MODULE.cp_upper(0, 500, 0.025) - expected) < 1e-12


def test_arm_partition():
    assert len(MODULE.DEPLOYABLE) == 5
    assert "B2_SOURCE_ONE_RUNG_CERTIFIED" in MODULE.DEPLOYABLE
    assert "O1_EVALUATION_ORACLE" not in MODULE.DEPLOYABLE
