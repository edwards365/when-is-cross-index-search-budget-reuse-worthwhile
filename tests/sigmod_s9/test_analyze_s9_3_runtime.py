import importlib.util
from pathlib import Path

import pandas as pd


MODULE_PATH = Path(__file__).parents[2] / "scripts" / "sigmod_s9" / "analyze_s9_3_runtime.py"
SPEC = importlib.util.spec_from_file_location("s9p3_runtime", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_metrics_zero_when_selected_is_endpoint():
    values = pd.DataFrame({
        "wall_ns": [10.0, 20.0], "endpoint_wall_ns": [10.0, 20.0],
        "cpu_ns": [9.0, 18.0], "endpoint_cpu_ns": [9.0, 18.0],
        "ndc": [100.0, 200.0], "endpoint_ndc": [100.0, 200.0],
    })
    result = MODULE.metrics(values)
    assert result["wall_gain"] == 0.0
    assert result["p95_wall_ratio"] == 1.0
