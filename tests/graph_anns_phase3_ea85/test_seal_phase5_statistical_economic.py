import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/graph_anns_phase3_ea85/seal_phase5_statistical_economic.py"
SPEC = importlib.util.spec_from_file_location("p5", SCRIPT)
P5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P5)


def test_n_grid_is_frozen():
    assert P5.N_GRID == (1000, 10000, 100000, 1000000, 10000000)


def test_finite_rejects_infinity_and_text():
    assert P5.finite("11.1")
    assert not P5.finite("inf")
    assert not P5.finite("NOT_ESTIMABLE")


def test_script_forbids_lifecycle_overclaim():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "search-only and full lifecycle must remain separate" not in text  # protocol owns rule
    assert "NOT_ESTIMABLE_TRUTH_REBUILD_CONTROL_NOT_HARMONIZED" in text
    assert "broad method SOTA" in text
