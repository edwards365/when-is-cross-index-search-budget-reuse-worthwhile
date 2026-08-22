import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def test_gate_a_config_is_development_only_and_frozen_matrix_is_complete() -> None:
    config = yaml.safe_load(
        (REPO / "configs/gate_a/gate_a_100k.yaml").read_text(encoding="utf-8")
    )
    matrix = json.loads(
        (REPO / "manifests/gate_a/run_matrix.json").read_text(encoding="utf-8")
    )
    assert config["formal"] is False
    assert config["firewall"] == "sealed"
    assert config["enabled_hdf5_members"] == ["train"]
    assert len(matrix["runs"]) == 81
    keys = {
        (
            row["dataset"],
            row["method"],
            row["build_seed"],
            row["control_seed"],
        )
        for row in matrix["runs"]
    }
    assert len(keys) == 81
