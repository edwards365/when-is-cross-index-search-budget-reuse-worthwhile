#!/usr/bin/env python3
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader((root / "results/sigmod_ea_slack_bridge/s1_slack_summary.csv").open()))
out = {}
for operator in sorted({r["operator"] for r in rows}):
    for dataset in sorted({r["dataset"] for r in rows if r["operator"] == operator}):
        lanes = {r["lane"]: r for r in rows if r["operator"] == operator and r["dataset"] == dataset}
        base = float(lanes["first_plus_0"]["incremental_risk"])
        plus1 = float(lanes["first_plus_1"]["incremental_risk"])
        plus2 = float(lanes["first_plus_2"]["incremental_risk"])
        stats = {
            "plus1_risk_reduction_pct": 100.0 * (base - plus1) / base,
            "plus2_risk_reduction_pct": 100.0 * (base - plus2) / base,
            "plus2_action_ratio": float(lanes["first_plus_2"]["requested_action_mean"])
            / float(lanes["first_plus_0"]["requested_action_mean"]),
        }
        if operator == "hnswlib":
            stats.update(
                {
                    "plus2_ndc_ratio": float(lanes["first_plus_2"]["target_ndc_mean"])
                    / float(lanes["first_plus_0"]["target_ndc_mean"]),
                    "plus2_ndc_saving_vs_endpoint_pct": 100.0
                    * (
                        1.0
                        - float(lanes["first_plus_2"]["target_ndc_mean"])
                        / float(lanes["endpoint"]["target_ndc_mean"])
                    ),
                }
            )
        out[f"{operator}|{dataset}"] = stats
print(json.dumps(out, indent=2))
