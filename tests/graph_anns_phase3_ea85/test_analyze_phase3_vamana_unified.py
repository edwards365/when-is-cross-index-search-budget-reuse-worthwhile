import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[2] / "scripts/graph_anns_phase3_ea85/analyze_phase3_vamana_unified.py"
SPEC = importlib.util.spec_from_file_location("p3_vamana", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_target_summary_uses_target_build_as_cluster():
    rows = [
        {"target": "V07", "risk": "1", "ctrans": "12", "cref": "10"},
        {"target": "V07", "risk": "0", "ctrans": "8", "cref": "10"},
        {"target": "V08", "risk": "0", "ctrans": "10", "cref": "10"},
    ]
    out = MOD.target_summary(rows, "V07")
    assert out["rows"] == 2
    assert out["transport_risk"] == 0.5
    assert out["cost_tax_ratio_of_means"] == 0.0


def test_build_bootstrap_is_deterministic():
    rows = [
        {"transport_risk": 0.1, "cost_tax_ratio_of_means": 0.01},
        {"transport_risk": 0.2, "cost_tax_ratio_of_means": 0.02},
        {"transport_risk": 0.3, "cost_tax_ratio_of_means": 0.03},
    ]
    assert MOD.build_bootstrap(rows, reps=50, seed=991) == MOD.build_bootstrap(rows, reps=50, seed=991)
