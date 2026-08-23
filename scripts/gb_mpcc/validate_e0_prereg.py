#!/usr/bin/env python3
"""Validate the E0 preregistration and its corrected-R0 authorization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_e0.yaml"))
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    decision = json.loads(Path(protocol["parent_r0_decision_path"]).read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_graph_construction":
        raise ValueError("E0 protocol is not frozen")
    if decision["decision"] != "PASS_TO_GRAPH_E0" or not decision["e0_authorized"]:
        raise PermissionError("corrected R0 did not authorize E0")
    if decision["formal_test_authorized"] or decision["formal_test_members_accessed"]:
        raise PermissionError("R0 formal-test firewall failure")
    if protocol["firewall"]["formal_test_access"] != "forbidden":
        raise PermissionError("E0 formal-test firewall is open")
    if protocol["methods"]["primary_R"] not in protocol["methods"]["r_values"]:
        raise ValueError("primary R is outside the frozen ablation set")
    if protocol["methods"]["distinct_graphs_per_dataset_seed"] != 13:
        raise ValueError("method matrix size changed")
    expected = 3 * 3 * protocol["methods"]["distinct_graphs_per_dataset_seed"]
    if protocol["methods"]["total_graph_runs"] != expected:
        raise ValueError("total graph matrix is inconsistent")
    if protocol["execution"]["minimum_free_disk_gib"] < 10:
        raise ValueError("disk safety gate was weakened")
    print(
        json.dumps(
            {
                "status": "valid",
                "gate": protocol["gate"],
                "total_graph_runs": expected,
                "formal_test_access": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
