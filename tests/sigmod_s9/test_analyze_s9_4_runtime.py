import importlib.util
from pathlib import Path

import pandas as pd


MODULE_PATH = Path(__file__).parents[2] / "scripts" / "sigmod_s9" / "analyze_s9_4_runtime.py"
SPEC = importlib.util.spec_from_file_location("s9p4_runtime_analysis", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_identity_metrics():
    frame = pd.DataFrame({"wall_ns": [1., 2.], "endpoint_wall_ns": [1., 2.], "cpu_ns": [1., 2.], "endpoint_cpu_ns": [1., 2.], "ndc": [1., 2.], "endpoint_ndc": [1., 2.]})
    result = MODULE.metrics(frame)
    assert result["wall_gain"] == 0.0
    assert result["p95_wall_ratio"] == 1.0
