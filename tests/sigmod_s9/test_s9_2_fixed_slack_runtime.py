import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "sigmod_s9" / "analyze_s9_2_fixed_slack_runtime.py"
SPEC = importlib.util.spec_from_file_location("s9_2_fixed_slack", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def synthetic_block(name, scale=1.0):
    wall = np.tile(np.asarray([80, 70, 60, 50, 50, 100], dtype=float), (10, 1)) * scale
    return {
        "build": name,
        "counts": Counter({256: 23}),
        "wall_all": wall,
        "cpu_all": wall.copy(),
        "candidate_wall": wall[:, 4],
        "endpoint_wall": wall[:, 5],
        "candidate_cpu": wall[:, 4],
        "endpoint_cpu": wall[:, 5],
    }


def test_exact_half_runtime_gain_and_tail():
    summary, per_build = MOD.analyze_dataset(
        "synthetic", [synthetic_block("b0"), synthetic_block("b1", 1.2)], 50, 991
    )
    assert abs(summary["wall_gain"] - 0.5) < 1e-12
    assert abs(summary["process_cpu_gain"] - 0.5) < 1e-12
    assert abs(summary["p95_ratio"] - 0.5) < 1e-12
    assert abs(summary["p99_ratio"] - 0.5) < 1e-12
    assert summary["mean_gate_pass"]
    assert summary["p95_noninferiority_gate_pass"]
    assert summary["loto_gate_pass"]
    assert len(per_build) == 2
    json.dumps(summary)


def test_expansion_respects_source_direction_counts():
    block = synthetic_block("b0")
    block["counts"] = Counter({256: 22, 512: 1})
    expanded = MOD.expanded_candidate([block], "wall")
    assert expanded.size == 10 * 23
    assert np.count_nonzero(expanded == 50) == 10 * 22
    assert np.count_nonzero(expanded == 100) == 10
