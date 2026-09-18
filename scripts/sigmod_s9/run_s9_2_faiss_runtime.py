#!/usr/bin/env python3
"""Pinned, interleaved Faiss-HNSW runtime replay for SIGMOD S9-2."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import platform
import random
import statistics
import time
from collections import defaultdict
from pathlib import Path

import faiss
import numpy as np


GRID = (16, 32, 64, 128, 256, 512)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stable_seed(*parts: object) -> int:
    payload = "|".join(map(str, (991, *parts))).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")


def action_order(build: str, query_id: int, repetition: int) -> list[int]:
    actions = list(GRID)
    random.Random(stable_seed("action", build, query_id, repetition)).shuffle(actions)
    return actions


def ndc() -> int:
    stats = faiss.cvar.hnsw_stats
    legacy, current = int(stats.n3), int(stats.ndis)
    if legacy > 0 and current == 0:
        return legacy
    if current > 0:
        return current
    raise RuntimeError("Faiss HNSW distance counter unavailable")


def coefficient_of_variation(values: list[int]) -> float:
    mean = statistics.fmean(values)
    return statistics.stdev(values) / mean if len(values) > 1 and mean > 0 else 0.0


def read_frozen(path: Path) -> dict[tuple[int, int], dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle)
        return {(int(row["query_id"]), int(row["ef"])): row for row in rows}


def timer_overhead_ns(repetitions: int = 10000) -> dict[str, float]:
    wall, cpu = [], []
    for _ in range(repetitions):
        c0 = time.process_time_ns()
        w0 = time.perf_counter_ns()
        w1 = time.perf_counter_ns()
        c1 = time.process_time_ns()
        wall.append(w1 - w0)
        cpu.append(c1 - c0)
    return {"wall_median_ns": statistics.median(wall), "cpu_median_ns": statistics.median(cpu)}


def read_optional(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except OSError:
        return None


def environment(required_cpu: int) -> dict[str, object]:
    affinity = sorted(os.sched_getaffinity(0))
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "faiss": getattr(faiss, "__version__", "unknown"),
        "pid": os.getpid(),
        "affinity": affinity,
        "required_cpu": required_cpu,
        "affinity_exact": affinity == [required_cpu],
        "loadavg": list(os.getloadavg()),
        "governor": read_optional(Path(f"/sys/devices/system/cpu/cpu{required_cpu}/cpufreq/scaling_governor")),
        "frequency_khz": read_optional(Path(f"/sys/devices/system/cpu/cpu{required_cpu}/cpufreq/scaling_cur_freq")),
        "timer_overhead": timer_overhead_ns(),
        "thread_env": {name: os.environ.get(name) for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
    }


def selected_query_ids(role: str, count: int) -> list[int]:
    start = 0 if role == "target_certification" else 500
    return list(range(start, start + count))


def warmup_query_ids(role: str, count: int) -> list[int]:
    """Return the frozen number of warm-up IDs, independent of smoke size."""
    return selected_query_ids(role, count)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--frozen-raw", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--role", choices=("target_certification", "target_evaluation"), default="target_evaluation")
    ap.add_argument("--query-count", type=int, default=20)
    ap.add_argument("--repetitions", type=int, default=3)
    ap.add_argument("--warmup-queries", type=int, default=20)
    ap.add_argument("--builds-per-dataset", type=int, default=1)
    ap.add_argument("--required-cpu", type=int, default=2)
    args = ap.parse_args()

    args.output.mkdir(parents=True, exist_ok=False)
    env = environment(args.required_cpu)
    if not env["affinity_exact"]:
        raise SystemExit(f"expected exact CPU affinity [{args.required_cpu}], got {env['affinity']}")
    for name, value in env["thread_env"].items():
        if value != "1":
            raise SystemExit(f"{name} must equal 1, got {value!r}")

    prereg = json.loads(args.manifest.read_text())
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for entry in prereg["faiss_indexes"]:
        grouped[entry["dataset"]].append(entry)
    entries = []
    for dataset in sorted(grouped):
        entries.extend(sorted(grouped[dataset], key=lambda item: item["build_id"])[: args.builds_per_dataset])
    random.Random(stable_seed("build-order")).shuffle(entries)

    faiss.omp_set_num_threads(1)
    query_ids = selected_query_ids(args.role, args.query_count)
    summaries = []
    total_mismatches = 0
    for entry in entries:
        dataset, build = entry["dataset"], entry["build_id"]
        index_path = Path(entry["path"])
        if sha256(index_path) != entry["sha256"]:
            raise SystemExit(f"index hash mismatch: {build}")
        queries = np.load(args.inputs / f"{dataset}.queries.npy").astype(np.float32, copy=False)
        truth = np.load(args.inputs / f"{dataset}.truth.npy")
        frozen = read_frozen(args.frozen_raw / f"{build}.csv.gz")
        index = faiss.read_index(str(index_path))
        core = faiss.downcast_index(index.index) if hasattr(index, "index") else faiss.downcast_index(index)

        warm_ids = warmup_query_ids(args.role, args.warmup_queries)
        for ef in GRID:
            core.hnsw.efSearch = ef
            for query_id in warm_ids:
                index.search(queries[query_id].reshape(1, -1), 10)

        rows: list[dict[str, object]] = []
        cell_wall: dict[tuple[int, int], list[int]] = defaultdict(list)
        mismatches = []
        for repetition in range(args.repetitions):
            ordered_queries = list(query_ids)
            random.Random(stable_seed("query", build, repetition)).shuffle(ordered_queries)
            for query_id in ordered_queries:
                query = queries[query_id]
                expected_truth = set(map(int, truth[query_id]))
                for order, ef in enumerate(action_order(build, query_id, repetition)):
                    core.hnsw.efSearch = ef
                    faiss.cvar.hnsw_stats.reset()
                    cpu0 = time.process_time_ns()
                    wall0 = time.perf_counter_ns()
                    _, labels = index.search(query.reshape(1, -1), 10)
                    wall_ns = time.perf_counter_ns() - wall0
                    cpu_ns = time.process_time_ns() - cpu0
                    found = labels[0].astype(int)
                    recall = len(set(map(int, found)) & expected_truth) / 10.0
                    distance_count = ndc()
                    topk = ";".join(map(str, found))
                    baseline = frozen[(query_id, ef)]
                    exact = (
                        topk == baseline["topk"]
                        and abs(recall - float(baseline["recall"])) < 1e-12
                        and distance_count == int(baseline["ndc"])
                    )
                    if not exact:
                        mismatches.append({"query_id": query_id, "ef": ef, "repetition": repetition})
                    cell_wall[(query_id, ef)].append(wall_ns)
                    rows.append({
                        "dataset": dataset,
                        "build": build,
                        "query_id": query_id,
                        "role": args.role,
                        "repetition": repetition,
                        "action_order": order,
                        "ef": ef,
                        "recall": recall,
                        "ndc": distance_count,
                        "wall_ns": wall_ns,
                        "process_cpu_ns": cpu_ns,
                        "topk_sha256": hashlib.sha256(topk.encode()).hexdigest(),
                        "native_exact": int(exact),
                    })

        output = args.output / f"{build}.csv.gz"
        with gzip.open(output, "wt", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        cvs = [coefficient_of_variation(values) for values in cell_wall.values()]
        block_totals: dict[int, list[int]] = defaultdict(list)
        for ef in GRID:
            for repetition in range(args.repetitions):
                block_totals[ef].append(sum(
                    int(row["wall_ns"]) for row in rows
                    if int(row["ef"]) == ef and int(row["repetition"]) == repetition
                ))
        block_cvs = [coefficient_of_variation(values) for values in block_totals.values()]
        summary = {
            "dataset": dataset,
            "build": build,
            "rows": len(rows),
            "cells": len(cell_wall),
            "mismatches": len(mismatches),
            "median_cell_cv_diagnostic": float(np.median(cvs)),
            "p95_cell_cv_diagnostic": float(np.quantile(cvs, 0.95)),
            "median_action_block_cv": float(np.median(block_cvs)),
            "max_action_block_cv": float(max(block_cvs)),
            "complete_fraction": len(rows) / (args.query_count * len(GRID) * args.repetitions),
            "output_sha256": sha256(output),
        }
        summaries.append(summary)
        total_mismatches += len(mismatches)
        print(json.dumps(summary), flush=True)

    block_medians = [item["median_action_block_cv"] for item in summaries]
    block_maxima = [item["max_action_block_cv"] for item in summaries]
    gate = {
        "status": "PASS" if total_mismatches == 0 and min(item["complete_fraction"] for item in summaries) >= 0.99 and max(block_medians) <= 0.05 and max(block_maxima) <= 0.10 else "FAIL",
        "mode": "SMOKE" if args.builds_per_dataset == 1 and args.query_count <= 20 else "FULL",
        "manifest_sha256": sha256(args.manifest),
        "environment": env,
        "settings": {
            "role": args.role,
            "query_count": args.query_count,
            "repetitions": args.repetitions,
            "warmup_queries": args.warmup_queries,
            "builds_per_dataset": args.builds_per_dataset,
            "grid": list(GRID),
        },
        "summaries": summaries,
        "total_mismatches": total_mismatches,
        "loadavg_after": list(os.getloadavg()),
    }
    (args.output / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    print(json.dumps({"status": gate["status"], "mismatches": total_mismatches, "builds": len(summaries)}))
    if gate["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
