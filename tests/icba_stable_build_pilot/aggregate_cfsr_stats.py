#!/usr/bin/env python3
import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRACE = ROOT / "results/icba_stable_build_pilot/smoke_design_traces"
OUT = ROOT / "results/icba_stable_build_pilot/smoke_design_traces/cfsr_edge_statistics.csv"

valid = set()
for path in sorted(TRACE.glob("shadow_*_endpoints.csv")):
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["endpoint_feasible"] == "1":
                valid.add((row["build_id"], row["query_row"], row["ef"]))

critical = defaultdict(int)
backup = defaultdict(int)
intruder = defaultdict(int)
seen_per_trace = defaultdict(int)
labels = {}
for path in sorted(TRACE.glob("shadow_*_introduction_edges.csv")):
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            trace = (row["build_id"], row["query_row"], row["ef"])
            if trace not in valid:
                continue
            edge = (int(row["source_internal"]), int(row["target_internal"]))
            labels[edge] = (int(row["source_label"]), int(row["target_label"]))
            if row["before_first_safe"] == "1":
                critical[edge] += 1
                if seen_per_trace[trace] > 0:
                    backup[edge] += 1
                seen_per_trace[trace] += 1
            else:
                intruder[edge] += 1

denominator = len(valid)
if denominator == 0:
    raise SystemExit("no feasible design traces")
with OUT.open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow((
        "source_internal", "target_internal", "source_label", "target_label",
        "critical_count", "critical_frequency", "backup_count", "backup_utility",
        "intruder_count", "intruder_association", "frontier_margin",
    ))
    for edge in sorted(set(critical) | set(backup) | set(intruder)):
        source_label, target_label = labels[edge]
        writer.writerow((
            *edge, source_label, target_label, critical[edge],
            critical[edge] / denominator, backup[edge], backup[edge] / denominator,
            intruder[edge], intruder[edge] / denominator, 0.0,
        ))
print(f"valid_traces={denominator} edges={len(labels)} critical_edges={len(critical)}")
