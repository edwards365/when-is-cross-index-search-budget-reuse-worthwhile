#!/usr/bin/env python3
import csv
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
MAIN = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
STATS = ROOT / "results/icba_stable_build_pilot/smoke_design_traces/cfsr_edge_statistics.csv"
BASE_EDGES = ROOT / "build_indexes/icba_stable_build_pilot/sift_smoke/baseline_b43/edges.csv"
SHADOW_EDGES = [
    MAIN / "results/gate_a/raw/sift_100k-original-b7/edges.csv",
    MAIN / "results/gate_a/raw/sift_100k-original-b17/edges.csv",
]
POINTS = ROOT / "build_inputs/icba_stable_build_pilot/sift_100k/points.f32bin"
OUT = ROOT / "results/icba_stable_build_pilot/smoke_repair_plan"
M = 16


def adjacency(path: Path):
    result = defaultdict(list)
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            source = int(row.get("source_label", row.get("source_internal")))
            target = int(row.get("target_label", row.get("target_internal")))
            if source != target:
                result[source].append(target)
    return result


baseline = adjacency(BASE_EDGES)
shadows = [adjacency(path) for path in SHADOW_EDGES]
stats = {}
with STATS.open(newline="") as handle:
    for row in csv.DictReader(handle):
        edge = (int(row["source_label"]), int(row["target_label"]))
        stats[edge] = {
            "critical": float(row["critical_frequency"]),
            "backup": float(row["backup_utility"]),
            "frontier": float(row["frontier_margin"]),
            "intruder": float(row["intruder_association"]),
        }

with POINTS.open("rb") as handle:
    rows, dimensions = struct.unpack("<QQ", handle.read(16))
points = np.memmap(POINTS, dtype="<f4", mode="r", offset=16, shape=(rows, dimensions))


def ranks(values):
    ordered = sorted(range(len(values)), key=lambda index: (values[index], index))
    result = [0.0] * len(values)
    denominator = max(1, len(values) - 1)
    for rank, index in enumerate(ordered):
        result[index] = rank / denominator
    return result


def diverse(source, ordered, protected):
    selected = list(protected)
    source_point = points[source]
    rejected = []
    for target in ordered:
        if target in selected or target == source:
            continue
        d_source = float(np.dot(points[target] - source_point, points[target] - source_point))
        keep = True
        for prior in selected:
            delta = points[target] - points[prior]
            if float(np.dot(delta, delta)) < d_source:
                keep = False
                break
        (selected if keep else rejected).append(target)
        if len(selected) == M:
            return selected
    for target in rejected:
        if target not in selected:
            selected.append(target)
        if len(selected) == M:
            return selected
    return selected


OUT.mkdir(parents=True, exist_ok=True)
base_plan = OUT / "baseline_plan.csv"
treatment_plan = OUT / "cfsr_lite_plan.csv"
audit_path = OUT / "selection_audit.csv"
changed_sources = 0
protected_total = 0
with base_plan.open("w", newline="") as base_handle, treatment_plan.open("w", newline="") as treatment_handle, audit_path.open("w", newline="") as audit_handle:
    base_writer, treatment_writer, audit = csv.writer(base_handle), csv.writer(treatment_handle), csv.writer(audit_handle)
    audit.writerow(("source_label", "target_label", "role", "score", "critical", "backup", "presence", "frontier", "intruder"))
    sources = sorted({source for source, _ in stats})
    for source in sources:
        base = list(dict.fromkeys(baseline.get(source, [])))
        if len(base) < M:
            continue
        candidates = set(base)
        for shadow in shadows:
            candidates.update(shadow.get(source, []))
        candidates.update(target for edge_source, target in stats if edge_source == source)
        candidates.discard(source)
        candidates = sorted(candidates)
        metrics = []
        for target in candidates:
            item = stats.get((source, target), {"critical": 0.0, "backup": 0.0, "frontier": 0.0, "intruder": 0.0})
            metrics.append((item["critical"], item["backup"], sum(target in shadow.get(source, []) for shadow in shadows) / len(shadows), item["frontier"], item["intruder"]))
        ranked = [ranks([item[column] for item in metrics]) for column in range(5)]
        scores = [0.45 * ranked[0][i] + 0.20 * ranked[1][i] + 0.20 * ranked[2][i] + 0.10 * ranked[3][i] - 0.05 * ranked[4][i] for i in range(len(candidates))]
        critical_candidates = [i for i, item in enumerate(metrics) if item[0] > 0]
        mandatory = candidates[max(critical_candidates, key=lambda i: (metrics[i][0], scores[i], -candidates[i]))] if critical_candidates else None
        backup_candidates = [i for i, item in enumerate(metrics) if item[1] > 0 and candidates[i] != mandatory]
        backup = candidates[max(backup_candidates, key=lambda i: (metrics[i][1], scores[i], -candidates[i]))] if backup_candidates else None
        protected = [value for value in (mandatory, backup) if value is not None]
        ordered = [candidates[i] for i in sorted(range(len(candidates)), key=lambda i: (-scores[i], candidates[i]))]
        selected = diverse(source, ordered, protected)
        if len(selected) != M:
            continue
        base_selected = base[:M]
        if set(selected) == set(base_selected):
            continue
        changed_sources += 1
        protected_total += len(protected)
        for target in base_selected:
            base_writer.writerow((source, target))
        for target in selected:
            treatment_writer.writerow((source, target))
            i = candidates.index(target)
            role = "mandatory" if target == mandatory else "backup" if target == backup else "diversity"
            audit.writerow((source, target, role, scores[i], *metrics[i]))

print(f"changed_sources={changed_sources} protected_edges={protected_total}")
if changed_sources == 0:
    raise SystemExit("repair plan has no changed source")
