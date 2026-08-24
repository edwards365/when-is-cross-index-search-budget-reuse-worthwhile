#!/usr/bin/env python3
"""Build, audit, evaluate, compress, and delete every frozen E0 temporary index."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


MINIMUM_FREE_BYTES = 10 * 2**30
ANGLE_PAIR_SAMPLE = 20_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_disk(path: Path) -> int:
    free = shutil.disk_usage(path).free
    if free < MINIMUM_FREE_BYTES:
        raise OSError(f"free disk {free / 2**30:.3f} GiB is below frozen 10 GiB gate")
    return free


def run_checked(command: list[str], stdout_path: Path, stderr_path: Path) -> float:
    started = time.perf_counter()
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        process = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
    elapsed = time.perf_counter() - started
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command)
    return elapsed


def read_edges(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.loadtxt(path, delimiter=",", skiprows=1, dtype=np.int32)
    if data.ndim != 2 or data.shape[1] != 2:
        raise ValueError(f"invalid edge matrix {path}")
    return data[:, 0], data[:, 1]


def read_mapping(path: Path, points: int) -> np.ndarray:
    data = np.loadtxt(path, delimiter=",", skiprows=1, dtype=np.int64)
    if data.shape != (points, 2) or not np.array_equal(data[:, 0], np.arange(points)):
        raise ValueError("invalid internal-to-external mapping")
    if len(np.unique(data[:, 1])) != points:
        raise ValueError("mapping is not a permutation")
    return data[:, 1]


def read_plan(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.loadtxt(path, delimiter=",", skiprows=1, dtype=np.int32)
    if data.ndim != 2 or data.shape[1] != 2:
        raise ValueError(f"invalid plan matrix {path}")
    return data[:, 0], data[:, 1]


def distribution(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    if not len(values):
        return {key: 0.0 for key in ("mean", "p50", "p95", "p99", "minimum", "maximum")}
    return {
        "mean": float(values.mean()),
        "p50": float(np.quantile(values, 0.50)),
        "p95": float(np.quantile(values, 0.95)),
        "p99": float(np.quantile(values, 0.99)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
    }


def adjacency_sets(source: np.ndarray, target: np.ndarray, points: int) -> list[set[int]]:
    adjacent = [set() for _ in range(points)]
    for left, right in zip(source.tolist(), target.tolist(), strict=True):
        adjacent[left].add(right)
        adjacent[right].add(left)
    return adjacent


def local_clustering(adjacent: list[set[int]]) -> np.ndarray:
    values = np.zeros(len(adjacent), dtype=np.float64)
    for node, neighbors in enumerate(adjacent):
        degree = len(neighbors)
        if degree < 2:
            continue
        links_twice = sum(len(neighbors & adjacent[other]) for other in neighbors)
        values[node] = links_twice / (degree * (degree - 1))
    return values


def sample_pairwise_angles(
    vectors: np.ndarray,
    mapping: np.ndarray,
    outgoing: list[list[int]],
    seed: int,
) -> np.ndarray:
    eligible = np.asarray([index for index, neighbors in enumerate(outgoing) if len(neighbors) >= 2])
    if not len(eligible):
        return np.empty(0, dtype=np.float64)
    generator = np.random.default_rng(seed)
    sources = generator.choice(eligible, size=ANGLE_PAIR_SAMPLE, replace=True)
    triples: list[tuple[int, int, int]] = []
    for source in sources:
        first, second = generator.choice(outgoing[int(source)], size=2, replace=False)
        triples.append((int(source), int(first), int(second)))
    angles = np.empty(len(triples), dtype=np.float64)
    for start in range(0, len(triples), 2048):
        block = np.asarray(triples[start : start + 2048], dtype=np.int64)
        centers = np.asarray(vectors[mapping[block[:, 0]]], dtype=np.float64)
        left = np.asarray(vectors[mapping[block[:, 1]]], dtype=np.float64) - centers
        right = np.asarray(vectors[mapping[block[:, 2]]], dtype=np.float64) - centers
        cosine = np.sum(left * right, axis=1) / (
            np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1)
        )
        angles[start : start + len(block)] = np.arccos(np.clip(cosine, -1.0, 1.0))
    return angles


def graph_audit(
    work: Path,
    plan_path: Path,
    vectors: np.ndarray,
    run_id: str,
    method: str,
) -> dict[str, Any]:
    points = len(vectors)
    source, target = read_edges(work / "layer0_edges.csv")
    mapping = read_mapping(work / "internal_to_external.csv", points)
    plan_source, plan_target = read_plan(plan_path)
    if source.min() < 0 or target.min() < 0 or source.max() >= points or target.max() >= points:
        raise ValueError("final graph endpoint out of range")
    encoded = source.astype(np.int64) * points + target
    if len(np.unique(encoded)) != len(encoded) or np.any(source == target):
        raise ValueError("final graph has duplicate or self edges")
    final_set = set(encoded.tolist())
    planned_encoded = plan_source.astype(np.int64) * points + plan_target
    planned_set = set(planned_encoded.tolist())
    reciprocal_set = set((plan_target.astype(np.int64) * points + plan_source).tolist())
    union = planned_set | final_set

    directed = csr_matrix(
        (np.ones(len(source), dtype=np.uint8), (source, target)), shape=(points, points)
    )
    weak_count, weak_labels = connected_components(directed, directed=True, connection="weak")
    strong_count, strong_labels = connected_components(directed, directed=True, connection="strong")
    if weak_count != 1:
        raise RuntimeError(f"{run_id}/{method}: weak connectivity broken")
    out_degree = np.bincount(source, minlength=points)
    in_degree = np.bincount(target, minlength=points)
    if out_degree.max() > 32:
        raise RuntimeError(f"{run_id}/{method}: layer-0 degree exceeds 32")
    reciprocal = sum((int(right) * points + int(left)) in final_set for left, right in zip(source, target, strict=True))

    outgoing: list[list[int]] = [[] for _ in range(points)]
    for left, right in zip(source.tolist(), target.tolist(), strict=True):
        outgoing[left].append(right)
    undirected = adjacency_sets(source, target, points)
    clustering = local_clustering(undirected)

    edge_lengths = np.empty(len(source), dtype=np.float64)
    for start in range(0, len(source), 100_000):
        stop = min(start + 100_000, len(source))
        left = np.asarray(vectors[mapping[source[start:stop]]], dtype=np.float64)
        right = np.asarray(vectors[mapping[target[start:stop]]], dtype=np.float64)
        edge_lengths[start:stop] = np.linalg.norm(left - right, axis=1)
    stable_seed = int.from_bytes(hashlib.sha256(f"{run_id}/{method}".encode()).digest()[:8], "little")
    angles = sample_pairwise_angles(vectors, mapping, outgoing, stable_seed)
    metadata = json.loads((work / "metadata.json").read_text(encoding="utf-8"))
    source_final = len(planned_set & final_set)
    reciprocal_final = len(reciprocal_set & final_set)
    return {
        "status": "PASS",
        "run_id": run_id,
        "method": method,
        "points": points,
        "directed_edges": len(final_set),
        "planned_edges": len(planned_set),
        "planned_final_directed_edge_jaccard": len(planned_set & final_set) / len(union),
        "source_edge_immediate_retention": metadata["source_edges_retained_immediately"] / len(planned_set),
        "source_edge_final_retention": source_final / len(planned_set),
        "reciprocal_edge_immediate_retention": metadata["reciprocal_edges_retained_immediately"] / len(planned_set),
        "reciprocal_edge_final_retention": reciprocal_final / len(planned_set),
        "weak_component_count": int(weak_count),
        "strong_component_count": int(strong_count),
        "largest_weak_component_fraction": float(np.bincount(weak_labels).max() / points),
        "largest_strong_component_fraction": float(np.bincount(strong_labels).max() / points),
        "out_degree": distribution(out_degree),
        "in_degree": distribution(in_degree),
        "reciprocal_directed_fraction": reciprocal / len(final_set),
        "local_clustering": distribution(clustering),
        "edge_length": distribution(edge_lengths),
        "pairwise_angle_radians": distribution(angles),
        "pairwise_angle_sample_size": len(angles),
        "upper_layer_checksum_equal": bool(metadata["upper_checksum_equal"]),
        "upper_layer_checksum": int(metadata["upper_checksum_after"]),
        "no_self_edges": True,
        "no_duplicate_edges": True,
        "maximum_layer0_degree_32": True,
        "formal_test_members_accessed": False,
    }


def compress(source: Path, destination: Path) -> None:
    with source.open("rb") as input_stream, gzip.open(destination, "wb", compresslevel=6) as output:
        shutil.copyfileobj(input_stream, output, length=4 * 1024 * 1024)


def method_plan(root: Path, run_id: str, method: str) -> Path:
    if method == "original_algorithm4":
        return root / "audits" / f"{run_id}-original-plan.csv"
    return root / "plans" / run_id / f"{method}.csv"


def execute_job(
    job: dict[str, Any],
    protocol: dict[str, Any],
    replay: Path,
    evaluator: Path,
    inputs: dict[str, dict[str, Any]],
    output: Path,
    stop: threading.Event,
) -> dict[str, Any]:
    run_id = str(job["run_id"])
    method = str(job["method"])
    final = output / "runs" / run_id / method
    complete = final / "COMPLETE.json"
    if complete.is_file():
        record = json.loads(complete.read_text(encoding="utf-8"))
        if record.get("status") != "complete" or not record.get("temporary_index_deleted"):
            raise ValueError(f"{run_id}/{method}: invalid existing completion marker")
        return record
    if stop.is_set():
        raise RuntimeError("E0 matrix stopped before this graph started")
    if final.exists():
        raise FileExistsError(f"refusing partial existing output {final}")
    check_disk(output)
    work = output / ".work" / f"{run_id}--{method}"
    if work.exists():
        raise FileExistsError(f"refusing stale work directory {work}")
    work.parent.mkdir(parents=True, exist_ok=True)
    dataset = job["dataset"]
    input_record = inputs[dataset["id"]]
    plan = method_plan(output, run_id, method)
    if not plan.is_file():
        raise FileNotFoundError(plan)
    metric = "ip" if dataset["normalized"] else "l2"
    build_seconds = run_checked(
        [
            str(replay.resolve()),
            str(Path(input_record["path"]).resolve()),
            str(dataset["vectors"]),
            str(dataset["dimensions"]),
            str(job["seed"]),
            str(protocol["base_hnsw"]["M"]),
            str(protocol["base_hnsw"]["ef_construction"]),
            metric,
            str(plan.resolve()),
            str(work.resolve()),
        ],
        work.parent / f"{run_id}--{method}.build.stdout.log",
        work.parent / f"{run_id}--{method}.build.stderr.log",
    )
    query_csv = work / "query_metrics.csv"
    search_seconds = run_checked(
        [
            str(evaluator.resolve()),
            str((work / "index.bin").resolve()),
            str(Path(job["queries"]).resolve()),
            str(Path(job["truth"]).resolve()),
            metric,
            ",".join(map(str, protocol["search"]["ef_search"])),
            str(protocol["search"]["warmup_queries"]),
            str(protocol["search"]["latency_rounds"]),
            f"{run_id}-{method}",
            str(query_csv.resolve()),
        ],
        work.parent / f"{run_id}--{method}.search.stdout.log",
        work.parent / f"{run_id}--{method}.search.stderr.log",
    )
    vectors = np.memmap(
        input_record["path"],
        dtype=np.float32,
        mode="r",
        shape=(int(input_record["points"]), int(input_record["dimensions"])),
    )
    audit = graph_audit(work, plan, vectors, run_id, method)
    if not audit["upper_layer_checksum_equal"]:
        raise RuntimeError(f"{run_id}/{method}: upper checksum mismatch")
    del vectors

    final.mkdir(parents=True)
    (final / "graph_metrics.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    shutil.copy2(work / "metadata.json", final / "construction_metadata.json")
    compress(work / "layer0_edges.csv", final / "layer0_edges.csv.gz")
    compress(work / "internal_to_external.csv", final / "internal_to_external.csv.gz")
    compress(query_csv, final / "query_metrics.csv.gz")
    index_bytes = (work / "index.bin").stat().st_size
    (work / "index.bin").unlink()
    if (work / "index.bin").exists():
        raise RuntimeError("temporary index deletion failed")
    record = {
        "status": "complete",
        "run_id": run_id,
        "dataset": dataset["id"],
        "build_seed": job["seed"],
        "method": method,
        "metric": metric,
        "plan_sha256": sha256(plan),
        "build_seconds": build_seconds,
        "search_seconds": search_seconds,
        "temporary_index_bytes": index_bytes,
        "temporary_index_deleted": True,
        "graph_metrics_sha256": sha256(final / "graph_metrics.json"),
        "query_metrics_sha256": sha256(final / "query_metrics.csv.gz"),
        "formal_test_members_accessed": False,
        "validation_dev_accessed": False,
        "e1_authorized": False,
    }
    complete.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.rmtree(work)
    check_disk(output)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_e0.yaml"))
    parser.add_argument(
        "--inputs", type=Path, default=Path("results/gb_mpcc/r0_inputs/manifest.json")
    )
    parser.add_argument(
        "--search-inputs", type=Path, default=Path("results/gb_mpcc/e0/search_inputs/manifest.json")
    )
    parser.add_argument("--replay", type=Path, default=Path("build-r0/hnsw_replay_layer0_plan"))
    parser.add_argument("--evaluator", type=Path, default=Path("build-r0/hnsw_e0_evaluate_index"))
    parser.add_argument("--output", type=Path, default=Path("results/gb_mpcc/e0"))
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()

    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if (
        protocol["status"] != "frozen_before_graph_construction"
        or protocol["firewall"]["formal_test_access"] != "forbidden"
        or protocol["firewall"]["validation_dev_access"] != "forbidden"
        or protocol["firewall"]["query_or_truth_may_affect_construction"] is not False
        or protocol["authorization_after_e0"]["formal_test"] is not False
    ):
        raise PermissionError("E0 protocol/firewall is not frozen closed")
    if args.workers != protocol["execution"]["maximum_parallel_graphs"] or args.workers != 3:
        raise ValueError("E0 matrix requires exactly the frozen maximum of three workers")
    if not args.replay.is_file() or not args.evaluator.is_file():
        raise FileNotFoundError("E0 native executable missing")
    train_manifest = json.loads(args.inputs.read_text(encoding="utf-8"))
    search_manifest = json.loads(args.search_inputs.read_text(encoding="utf-8"))
    if train_manifest["formal_test_members_accessed"] or search_manifest["formal_test_members_accessed"]:
        raise PermissionError("input manifest violates formal-test firewall")
    if search_manifest["validation_dev_accessed"] or search_manifest["construction_accessed_queries_or_truth"]:
        raise PermissionError("search-input manifest violates E0 query firewall")
    inputs = {str(record["dataset"]): record for record in train_manifest["inputs"]}
    search = {str(record["dataset"]): record for record in search_manifest["datasets"]}
    for record in inputs.values():
        if sha256(Path(record["path"])) != record["fbin_sha256"]:
            raise ValueError("frozen train input checksum mismatch")
    for record in search.values():
        if sha256(Path(record["queries"])) != record["queries_sha256"] or sha256(
            Path(record["truth"])
        ) != record["truth_sha256"]:
            raise ValueError("frozen search input checksum mismatch")

    args.output.mkdir(parents=True, exist_ok=True)
    check_disk(args.output)
    datasets = {str(record["id"]): record for record in protocol["datasets"]}
    jobs: list[dict[str, Any]] = []
    for dataset_id in protocol["execution"]["datasets_order"]:
        for seed in protocol["execution"]["seeds_order"]:
            for method in protocol["execution"]["methods_order"]:
                jobs.append(
                    {
                        "dataset": datasets[dataset_id],
                        "seed": int(seed),
                        "run_id": f"{dataset_id}-b{seed}",
                        "method": str(method),
                        "queries": search[dataset_id]["queries"],
                        "truth": search[dataset_id]["truth"],
                    }
                )
    if len(jobs) != len(protocol["base_hnsw"]["build_seeds"]) * len(datasets) * 13:
        raise RuntimeError("E0 job matrix is not 117 graphs")

    records: list[dict[str, Any]] = []
    stop = threading.Event()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                execute_job,
                job,
                protocol,
                args.replay,
                args.evaluator,
                inputs,
                args.output,
                stop,
            ): job
            for job in jobs
        }
        for future in as_completed(futures):
            try:
                record = future.result()
            except BaseException:
                stop.set()
                for pending in futures:
                    pending.cancel()
                raise
            records.append(record)
            print(
                json.dumps(
                    {
                        "complete": len(records),
                        "expected": len(jobs),
                        "run_id": record["run_id"],
                        "method": record["method"],
                        "free_gib": check_disk(args.output) / 2**30,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    if len(records) != 117:
        raise RuntimeError("E0 graph matrix incomplete")
    checksums_by_run: dict[str, set[int]] = {}
    for record in records:
        metrics = json.loads(
            (args.output / "runs" / record["run_id"] / record["method"] / "graph_metrics.json").read_text(
                encoding="utf-8"
            )
        )
        checksums_by_run.setdefault(record["run_id"], set()).add(metrics["upper_layer_checksum"])
    if any(len(values) != 1 for values in checksums_by_run.values()):
        raise RuntimeError("upper-layer checksum differs between methods")
    summary = {
        "status": "E0_GRAPH_MATRIX_COMPLETE",
        "graphs": len(records),
        "expected_graphs": 117,
        "all_temporary_indexes_deleted": all(row["temporary_index_deleted"] for row in records),
        "all_graph_invariants_passed": True,
        "upper_checksums_equal_within_run": True,
        "formal_test_members_accessed": False,
        "validation_dev_accessed": False,
        "e1_authorized": False,
        "records": sorted(records, key=lambda row: (row["run_id"], row["method"])),
    }
    (args.output / "graph_matrix_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "records"}))


if __name__ == "__main__":
    main()
