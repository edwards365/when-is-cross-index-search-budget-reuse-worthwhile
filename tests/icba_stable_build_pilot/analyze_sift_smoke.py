#!/usr/bin/env python3
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "results/icba_stable_build_pilot/smoke_effect"
OUT = ROOT / "results/icba_stable_build_pilot/smoke_analysis"
OUT.mkdir(parents=True, exist_ok=True)


def rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def load(role, graph):
    prefix = BASE / f"{graph}_{role}_b43"
    checkpoints = rows(Path(str(prefix) + "_checkpoints.csv"))
    endpoints = rows(Path(str(prefix) + "_endpoints.csv"))
    grouped = defaultdict(list)
    for row in checkpoints:
        grouped[(int(row["query_row"]), int(row["ef"]))].append(row)
    final_recall = {key: float(value[-1]["recall_at_10"]) for key, value in grouped.items()}
    path_signature = {
        key: tuple((item["expansion_count"], item["top_k_internal"]) for item in value)
        for key, value in grouped.items()
    }
    endpoint_map = {(int(row["query_row"]), int(row["ef"])): row for row in endpoints}
    return final_recall, path_signature, endpoint_map


metric_rows = []
gate = {}
for role in ("design", "calibration"):
    base_recall, base_path, base_endpoint = load(role, "baseline")
    stable_recall, stable_path, stable_endpoint = load(role, "stable")
    keys = sorted(base_recall)
    affected = sum(base_path[key] != stable_path[key] for key in keys) / len(keys)
    for graph, recall_map, endpoint_map in (
        ("baseline", base_recall, base_endpoint),
        ("stable", stable_recall, stable_endpoint),
    ):
        recalls = [recall_map[key] for key in keys]
        feasible = [int(endpoint_map[key]["endpoint_feasible"]) for key in keys]
        bexp = [int(endpoint_map[key]["first_safe_expansion"]) for key in keys if int(endpoint_map[key]["endpoint_feasible"])]
        ndc = sorted(int(endpoint_map[key]["ndc"]) for key in keys)
        bef = []
        for query_id in range(100):
            candidates = [ef for ef in (10, 20, 40) if recall_map[(query_id, ef)] >= 0.9]
            bef.append(min(candidates) if candidates else None)
        metric_rows.extend((
            (role, graph, "affected_trace_rate", affected if graph == "stable" else 0.0),
            (role, graph, "mean_final_recall", statistics.fmean(recalls)),
            (role, graph, "endpoint_feasible_rate", statistics.fmean(feasible)),
            (role, graph, "mean_B_exp_feasible", statistics.fmean(bexp) if bexp else ""),
            (role, graph, "B_ef_feasible_rate", sum(value is not None for value in bef) / len(bef)),
            (role, graph, "mean_B_ef_feasible", statistics.fmean(value for value in bef if value is not None) if any(value is not None for value in bef) else ""),
            (role, graph, "mean_ndc", statistics.fmean(ndc)),
            (role, graph, "p95_ndc", ndc[int(0.95 * (len(ndc) - 1))]),
        ))
    gate[role] = {
        "affected_trace_rate": affected,
        "recall_delta": statistics.fmean(stable_recall.values()) - statistics.fmean(base_recall.values()),
        "endpoint_delta": statistics.fmean(int(stable_endpoint[key]["endpoint_feasible"]) for key in keys) - statistics.fmean(int(base_endpoint[key]["endpoint_feasible"]) for key in keys),
        "mean_ndc_delta": statistics.fmean(int(stable_endpoint[key]["ndc"]) for key in keys) - statistics.fmean(int(base_endpoint[key]["ndc"]) for key in keys),
    }

with (OUT / "smoke_metrics.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(("query_role", "graph", "metric", "value"))
    writer.writerows(metric_rows)
(OUT / "smoke_gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
print(json.dumps(gate, sort_keys=True))
