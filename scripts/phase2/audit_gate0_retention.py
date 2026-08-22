#!/usr/bin/env python
"""Apply frozen GGR selections through hnswlib reciprocal/reverse pruning."""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import tempfile
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import psutil
import yaml
from scipy import sparse
from scipy.sparse.csgraph import connected_components

REPO = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_construction(manifest: dict, count: int) -> tuple[np.ndarray, str]:
    source = REPO / manifest["local_path"]
    if sha256(source) != manifest["sha256"]:
        raise ValueError(f"dataset checksum mismatch: {manifest['name']}")
    with h5py.File(source, "r") as handle:
        points = np.asarray(handle["train"][:count], dtype=np.float32)
    angular = str(manifest["distance"]).startswith("angular")
    if angular:
        norms = np.linalg.norm(points, axis=1, keepdims=True)
        if np.any(norms == 0):
            raise ValueError("angular construction data contain a zero vector")
        points /= norms
    return np.ascontiguousarray(points), "ip" if angular else "l2"


def selected_rows(frame: pd.DataFrame, dataset: str, tolerance: float) -> pd.DataFrame:
    rows = frame[
        (frame["dataset"] == dataset)
        & np.isclose(frame["geometry_tolerance"], tolerance, rtol=0.0, atol=0.0)
    ].copy()
    if rows["center"].duplicated().any() or rows.empty:
        raise ValueError(f"selector rows are missing or duplicated for {dataset}")
    return rows.sort_values("center")


def gini(values: np.ndarray) -> float:
    ordered = np.sort(np.asarray(values, dtype=np.float64))
    total = ordered.sum()
    if total == 0:
        return 0.0
    ranks = np.arange(1, len(ordered) + 1, dtype=np.float64)
    return float((2 * np.dot(ranks, ordered) / total - len(ordered) - 1) / len(ordered))


def graph_metrics(path: Path, count: int) -> tuple[dict[str, float], set[tuple[int, int]]]:
    edges = pd.read_csv(path)
    sources = edges["source"].to_numpy(dtype=np.int64)
    targets = edges["target"].to_numpy(dtype=np.int64)
    edge_set = set(zip(sources.tolist(), targets.tolist(), strict=True))
    directed = sparse.csr_matrix(
        (np.ones(len(edges), dtype=np.int8), (sources, targets)), shape=(count, count)
    )
    directed.data[:] = 1
    union = (directed + directed.T).astype(bool).astype(np.int8)
    union.setdiag(0)
    union.eliminate_zeros()
    outdegree = np.asarray(directed.sum(axis=1)).ravel()
    indegree = np.asarray(directed.sum(axis=0)).ravel()
    reciprocal_directed = directed.multiply(directed.T).nnz
    components, _ = connected_components(union, directed=False)
    degrees = np.asarray(union.sum(axis=1)).ravel()
    triangle_twice = np.asarray(union.multiply(union @ union).sum(axis=1)).ravel()
    denominators = degrees * (degrees - 1)
    clustering = np.divide(
        triangle_twice,
        denominators,
        out=np.zeros_like(triangle_twice, dtype=np.float64),
        where=denominators > 0,
    )
    metrics = {
        "directed_edges": float(len(edge_set)),
        "outdegree_mean": float(outdegree.mean()),
        "outdegree_std": float(outdegree.std()),
        "indegree_mean": float(indegree.mean()),
        "indegree_std": float(indegree.std()),
        "indegree_p95": float(np.quantile(indegree, 0.95)),
        "indegree_p99": float(np.quantile(indegree, 0.99)),
        "indegree_max": float(indegree.max()),
        "indegree_gini": gini(indegree),
        "reciprocal_directed_fraction": float(reciprocal_directed / len(edge_set)),
        "weak_components": float(components),
        "mean_local_clustering": float(clustering.mean()),
    }
    return metrics, edge_set


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("raw output directory exists and will not be overwritten")
    if not args.executable.is_file():
        raise FileNotFoundError(args.executable)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    selector_dir = REPO / config["selector_run"]
    centers = pd.read_csv(selector_dir / "per_center.csv")
    swaps = pd.read_csv(selector_dir / "per_swap.csv")
    tolerance = float(config["geometry_tolerance"])
    process = psutil.Process()
    peak_rss = process.memory_info().rss
    all_edges: list[pd.DataFrame] = []
    topology_rows: list[dict[str, float | str]] = []
    receipts = []
    started = time.perf_counter()
    args.output.mkdir(parents=True)

    for manifest_name in config["datasets"]:
        manifest_path = REPO / manifest_name
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        points, metric = load_construction(manifest, config["construction_vectors"])
        audited_centers = selected_rows(centers, manifest["name"], tolerance)
        changed_mask = [
            set(json.loads(row.geometry_selected_targets))
            != set(json.loads(row.final_selected_targets))
            for row in audited_centers.itertuples()
        ]
        dataset_centers = audited_centers[np.asarray(changed_mask)].copy()
        dataset_swaps = swaps[
            (swaps["dataset"] == manifest["name"])
            & np.isclose(swaps["geometry_tolerance"], tolerance, rtol=0.0, atol=0.0)
        ]
        terminal_incoming: set[tuple[int, int]] = set()
        for row in dataset_centers.itertuples():
            geometry_targets = set(json.loads(row.geometry_selected_targets))
            final_targets = set(json.loads(row.final_selected_targets))
            terminal_incoming.update(
                (int(row.center), int(target)) for target in final_targets - geometry_targets
            )
        safe_name = manifest["name"].replace("/", "_")
        edge_path = args.output / f"{safe_name}_retention.csv"
        with tempfile.TemporaryDirectory(prefix="narhnsw-gate0-") as temporary:
            temporary_path = Path(temporary)
            point_path = temporary_path / "points.f32bin"
            base_plan_path = temporary_path / "geometry_plan.csv"
            treatment_plan_path = temporary_path / "ggr_plan.csv"
            with point_path.open("wb") as handle:
                handle.write(struct.pack("<QQ", len(points), points.shape[1]))
                points.tofile(handle)
            with base_plan_path.open("w", encoding="utf-8", newline="") as base_handle, (
                treatment_plan_path.open("w", encoding="utf-8", newline="")
            ) as treatment_handle:
                for row in dataset_centers.itertuples():
                    base_targets = json.loads(row.geometry_selected_targets)
                    treatment_targets = json.loads(row.final_selected_targets)
                    if len(base_targets) != config["M"] or len(treatment_targets) != config["M"]:
                        raise ValueError("frozen selection does not contain M targets")
                    for target in base_targets:
                        base_handle.write(f"{int(row.center)},{int(target)}\n")
                    for target in treatment_targets:
                        treatment_handle.write(f"{int(row.center)},{int(target)}\n")
            command = [
                str(args.executable.resolve()),
                str(point_path),
                str(base_plan_path),
                str(treatment_plan_path),
                metric,
                str(config["M"]),
                str(config["ef_construction"]),
                str(config["seed"]),
                str(edge_path.resolve()),
            ]
            run_started = time.perf_counter()
            child = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            child_process = psutil.Process(child.pid)
            child_peak_rss = 0
            while child.poll() is None:
                try:
                    child_peak_rss = max(child_peak_rss, child_process.memory_info().rss)
                except psutil.NoSuchProcess:
                    pass
                time.sleep(0.01)
            stdout, stderr = child.communicate()
            if child.returncode:
                raise subprocess.CalledProcessError(child.returncode, command, stdout, stderr)
            run_seconds = time.perf_counter() - run_started
        edge_frame = pd.read_csv(edge_path)
        edge_frame.insert(0, "dataset", manifest["name"])
        edge_frame["is_terminal_ggr_incoming"] = [
            (int(row.source), int(row.target)) in terminal_incoming
            for row in edge_frame.itertuples()
        ]
        edge_frame.to_csv(edge_path, index=False)
        all_edges.append(edge_frame)
        before_path = edge_path.with_name(f"{edge_path.stem}_before_edges.csv")
        after_path = edge_path.with_name(f"{edge_path.stem}_after_edges.csv")
        before_metrics, before_edges = graph_metrics(before_path, len(points))
        after_metrics, after_edges = graph_metrics(after_path, len(points))
        directed_union = before_edges | after_edges
        directed_jaccard = len(before_edges & after_edges) / len(directed_union)
        before_support = {tuple(sorted(edge)) for edge in before_edges}
        after_support = {tuple(sorted(edge)) for edge in after_edges}
        support_jaccard = len(before_support & after_support) / len(
            before_support | after_support
        )
        for metric in before_metrics:
            topology_rows.append(
                {
                    "dataset": manifest["name"],
                    "metric": metric,
                    "before": before_metrics[metric],
                    "after": after_metrics[metric],
                    "delta": after_metrics[metric] - before_metrics[metric],
                }
            )
        topology_rows.extend(
            [
                {
                    "dataset": manifest["name"],
                    "metric": "directed_edge_jaccard",
                    "before": 1.0,
                    "after": directed_jaccard,
                    "delta": directed_jaccard - 1.0,
                },
                {
                    "dataset": manifest["name"],
                    "metric": "undirected_support_jaccard",
                    "before": 1.0,
                    "after": support_jaccard,
                    "delta": support_jaccard - 1.0,
                },
            ]
        )
        receipts.append(
            {
                "dataset": manifest["name"],
                "source_sha256": manifest["sha256"],
                "audited_centers": len(audited_centers),
                "planned_centers": len(dataset_centers),
                "accepted_ggr_swaps": len(dataset_swaps),
                "terminal_ggr_incoming_edges": len(terminal_incoming),
                "cpp_stdout": stdout.strip(),
                "run_seconds": run_seconds,
                "peak_cpp_rss_bytes": child_peak_rss,
            }
        )
        peak_rss = max(peak_rss, process.memory_info().rss)

    edge_rows = pd.concat(all_edges, ignore_index=True)
    incoming_rows = edge_rows[edge_rows["is_terminal_ggr_incoming"]].copy()
    summary = (
        incoming_rows.groupby("dataset")
        .agg(
            terminal_ggr_incoming_edges=("is_terminal_ggr_incoming", "size"),
            effectual_incoming_edges=("proposed_added", "sum"),
            outgoing_retained_immediate=("source_to_target_immediate", "sum"),
            reciprocal_retained_immediate=("target_to_source_immediate", "sum"),
            outgoing_retained_final=("source_to_target_final", "sum"),
            reciprocal_retained_final=("target_to_source_final", "sum"),
        )
        .reset_index()
    )
    summary["effectual_swap_fraction"] = (
        summary["effectual_incoming_edges"] / summary["terminal_ggr_incoming_edges"]
    )
    summary["final_reciprocal_fraction"] = (
        summary["reciprocal_retained_final"] / summary["terminal_ggr_incoming_edges"]
    )
    summary.to_csv(args.output / "summary.csv", index=False)
    pd.DataFrame(topology_rows).to_csv(args.output / "topology.csv", index=False)
    metadata = {
        "run_id": config["run_id"],
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "formal_test_members_accessed": False,
        "integration_scope": (
            "paired independent post-build level-0 fixed-selection mutual connection"
        ),
        "selector_source": config["selector_run"],
        "geometry_tolerance": tolerance,
        "receipts": receipts,
        "peak_python_rss_bytes": peak_rss,
        "total_seconds": time.perf_counter() - started,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    print(summary.to_string(index=False))
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
