#!/usr/bin/env python
"""Generate the frozen 81-run Gate-A build matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config_bytes = args.config.read_bytes()
    config = yaml.safe_load(config_bytes)
    config_hash = hashlib.sha256(config_bytes).hexdigest()
    deterministic = {"original", "geometry", "ggr_0"}
    rows = []
    for dataset in config["datasets"]:
        for build_seed in config["build"]["build_seeds"]:
            for method in config["methods"]:
                seeds = [None] if method in deterministic else config["control_seeds"]
                for control_seed in seeds:
                    run_id = f"{dataset}-{method}-b{build_seed}"
                    if control_seed is not None:
                        run_id += f"-c{control_seed}"
                    rows.append(
                        {
                            "run_id": run_id,
                            "dataset": dataset,
                            "method": method,
                            "build_seed": build_seed,
                            "control_seed": control_seed,
                            "config_sha256": config_hash,
                            "status": "pending",
                        }
                    )
    if len(rows) != 81:
        raise AssertionError(f"expected 81 runs, observed {len(rows)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"config_sha256": config_hash, "runs": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"generated {len(rows)} Gate-A runs; config_sha256={config_hash}")


if __name__ == "__main__":
    main()
