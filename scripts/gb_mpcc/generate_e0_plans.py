#!/usr/bin/env python3
"""Generate the frozen, query-independent Graph Gate E0 selection plans."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import time
from collections import defaultdict
from itertools import groupby
from pathlib import Path
from typing import Any, TextIO

import numpy as np
import yaml
from narhnsw.e0_plans import empirical_progress_masks_fast, stable_mpcc_select
from narhnsw.ggr import geometry_guarded_resistance_selection
from narhnsw.mpcc_selectors import maxmin_angle_select, random_backbone_select
from narhnsw.resistance import (
    effective_resistance_matrix,
    gaussian_weight_graph,
    greedy_neighbor_selection,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def layer0_groups(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        rows = (row for row in csv.DictReader(stream) if int(row["layer"]) == 0)
        for insertion_id, group in groupby(rows, key=lambda row: int(row["insertion_id"])):
            yield insertion_id, list(group)


def read_mapping(path: Path, points: int) -> np.ndarray:
    mapping = np.full(points, -1, dtype=np.int64)
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            mapping[int(row["internal_id"])] = int(row["external_label"])
    if np.any(mapping < 0) or len(np.unique(mapping)) != points:
        raise ValueError(f"invalid insertion mapping: {path}")
    return mapping


def read_changes(path: Path) -> dict[int, list[tuple[int, int, str]]]:
    result: defaultdict[int, list[tuple[int, int, str]]] = defaultdict(list)
    for insertion_id, rows in layer0_groups(path):
        result[insertion_id].extend(
            (int(row["source"]), int(row["target"]), row["action"]) for row in rows
        )
    return dict(result)


def insertion_leverage(
    vectors: np.ndarray,
    mapping: np.ndarray,
    insertion_id: int,
    candidate_ids: list[int],
    adjacency: list[set[int]],
) -> np.ndarray:
    local_ids = [insertion_id, *candidate_ids]
    local_index = {node: index for index, node in enumerate(local_ids)}
    local_set = set(local_ids)
    base = np.zeros((len(local_ids), len(local_ids)), dtype=bool)
    for source in local_ids:
        for target in adjacency[source] & local_set:
            base[local_index[source], local_index[target]] = True
    base |= base.T
    base[0, 1:] = True
    base[1:, 0] = True
    np.fill_diagonal(base, False)
    external = mapping[np.asarray(local_ids)]
    local_points = np.asarray(vectors[external], dtype=np.float64)
    distances = np.linalg.norm(local_points[:, None] - local_points[None, :], axis=-1)
    observed = distances[np.triu(base, k=1)]
    positive = observed[observed > np.finfo(float).eps]
    if not len(positive):
        raise ValueError("cannot define Scheme-A Gaussian scale")
    weights = gaussian_weight_graph(local_points, base, rho=float(np.median(positive)))
    resistance = effective_resistance_matrix(weights)
    leverage = weights[0, 1:] * resistance[0, 1:]
    if np.any(~np.isfinite(leverage)) or np.any(leverage < 0):
        raise FloatingPointError("nonfinite Scheme-A candidate leverage")
    return leverage


def method_names(r_values: list[int]) -> list[str]:
    result = ["geometry", "maxmin_angle", "ggr_0"]
    for radius in r_values:
        result.extend(
            [
                f"geometry_backbone_random_R{radius}",
                f"geometry_backbone_mpcc_shuffled_R{radius}",
                f"geometry_backbone_mpcc_R{radius}",
            ]
        )
    return result


def select_event(
    *,
    vectors: np.ndarray,
    mapping: np.ndarray,
    neighbor_ids: np.ndarray,
    local_scales: np.ndarray,
    adjacency: list[set[int]],
    insertion_id: int,
    rows: list[dict[str, str]],
    build_seed: int,
    state_samples: int,
    r_values: list[int],
    random_offset: int,
    shuffled_offset: int,
) -> tuple[dict[str, tuple[int, ...]], tuple[int, ...]]:
    candidate_ids = [int(row["candidate_id"]) for row in rows]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate pool contains a duplicate")
    accepted = {int(row["candidate_id"]) for row in rows if row["decision"] == "accepted"}
    algorithm4 = tuple(
        index for index, candidate in enumerate(candidate_ids) if candidate in accepted
    )
    budget = len(algorithm4)
    external_source = int(mapping[insertion_id])
    external_candidates = mapping[np.asarray(candidate_ids)]
    center = np.asarray(vectors[external_source], dtype=np.float64)
    candidates = np.asarray(vectors[external_candidates], dtype=np.float64)
    distances = np.linalg.norm(candidates - center, axis=1)
    leverage = insertion_leverage(vectors, mapping, insertion_id, candidate_ids, adjacency)

    geometry_list, _ = greedy_neighbor_selection(
        center,
        candidates,
        np.zeros(len(candidates)),
        budget,
        alpha=0.0,
        beta=1.0,
        gamma=1.0,
        sigma=0.5,
        labels=external_candidates,
    )
    geometry = tuple(geometry_list)
    ggr = geometry_guarded_resistance_selection(
        center,
        candidates,
        leverage,
        budget,
        epsilon=0.0,
        geometry_tolerance=1e-12,
        leverage_tolerance=1e-12,
        labels=external_candidates,
    )
    if ggr.geometry_selected != geometry:
        raise AssertionError("GGR geometry baseline diverged from Geometry")
    event_seed = 202608240000 + build_seed * 1000003 + external_source
    local_points = np.asarray(vectors[neighbor_ids[external_source]], dtype=np.float64)
    masks, _, _ = empirical_progress_masks_fast(
        center,
        candidates,
        local_points,
        float(local_scales[external_source]),
        state_samples,
        np.random.default_rng(event_seed),
    )
    selections: dict[str, tuple[int, ...]] = {
        "geometry": geometry,
        "maxmin_angle": maxmin_angle_select(center, candidates, external_candidates, budget),
        "ggr_0": ggr.selected,
    }
    for radius in r_values:
        backbone = algorithm4[: max(0, budget - radius)]
        random_name = f"geometry_backbone_random_R{radius}"
        shuffled_name = f"geometry_backbone_mpcc_shuffled_R{radius}"
        mpcc_name = f"geometry_backbone_mpcc_R{radius}"
        selections[random_name] = random_backbone_select(
            len(candidates),
            budget,
            backbone,
            np.random.default_rng(event_seed + random_offset),
        )
        permutation = np.random.default_rng(event_seed + shuffled_offset).permutation(len(masks))
        selections[shuffled_name] = stable_mpcc_select(
            masks[permutation], budget, distances, external_candidates, backbone
        )
        selections[mpcc_name] = stable_mpcc_select(
            masks, budget, distances, external_candidates, backbone
        )
    return selections, algorithm4


def run(args: argparse.Namespace) -> None:
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if protocol["firewall"]["formal_test_access"] != "forbidden":
        raise PermissionError("E0 formal-test firewall is open")
    if protocol["design_dev"]["construction_access"] != "forbidden":
        raise PermissionError("E0 query-construction firewall is open")
    minimum_free_bytes = int(protocol["execution"]["minimum_free_disk_gib"]) * 1024**3
    if shutil.disk_usage(Path(".")).free < minimum_free_bytes:
        raise OSError("E0 disk safety stop before plan generation")
    if args.dataset not in {item["id"] for item in protocol["datasets"]}:
        raise ValueError("dataset is outside the frozen matrix")
    if args.seed not in protocol["base_hnsw"]["build_seeds"]:
        raise ValueError("build seed is outside the frozen matrix")
    inputs = json.loads(args.inputs.read_text(encoding="utf-8"))
    if inputs["formal_test_members_accessed"]:
        raise PermissionError("input manifest violates the formal-test firewall")
    input_record: dict[str, Any] = next(
        item for item in inputs["inputs"] if item["dataset"] == args.dataset
    )
    points = int(input_record["points"])
    vectors = np.memmap(
        input_record["path"],
        dtype=np.float32,
        mode="r",
        shape=(points, int(input_record["dimensions"])),
    )
    raw = args.raw / f"{args.dataset}-b{args.seed}"
    mapping = read_mapping(raw / "internal_to_external.csv", points)
    changes = read_changes(raw / "insertion_adjacency_changes.csv.gz")
    cache = np.load(args.neighbors / f"{args.dataset}.npz")
    neighbor_ids = cache["neighbor_external_labels"]
    local_scales = cache["local_scales"]
    r_values = [int(value) for value in protocol["methods"]["r_values"]]
    names = method_names(r_values)
    if len(names) + 1 != int(protocol["methods"]["distinct_graphs_per_dataset_seed"]):
        raise AssertionError("E0 method matrix is incomplete")
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    streams: dict[str, TextIO] = {}
    writers: dict[str, csv.writer] = {}
    for name in names:
        streams[name] = (args.output / f"{name}.csv").open("w", encoding="utf-8", newline="")
        writers[name] = csv.writer(streams[name])
        writers[name].writerow(["source", "target"])

    adjacency = [set() for _ in range(points)]
    events = 0
    edge_counts = {name: 0 for name in names}
    changed_events = {name: 0 for name in names}
    start = time.perf_counter()
    try:
        for insertion_id, rows in layer0_groups(raw / "insertion_candidates.csv.gz"):
            accepted_ids = [
                int(row["candidate_id"]) for row in rows if row["decision"] == "accepted"
            ]
            adjacency[insertion_id].update(accepted_ids)
            for source, target, action in changes.get(insertion_id, []):
                if action == "added":
                    adjacency[source].add(target)
                elif action == "removed":
                    adjacency[source].remove(target)
                else:
                    raise ValueError(f"unknown adjacency action: {action}")
            selections, algorithm4 = select_event(
                vectors=vectors,
                mapping=mapping,
                neighbor_ids=neighbor_ids,
                local_scales=local_scales,
                adjacency=adjacency,
                insertion_id=insertion_id,
                rows=rows,
                build_seed=args.seed,
                state_samples=int(protocol["state_distribution"]["state_samples"]),
                r_values=r_values,
                random_offset=int(protocol["methods"]["matched_random_seed_offset"]),
                shuffled_offset=int(protocol["methods"]["matched_shuffled_seed_offset"]),
            )
            candidate_ids = [int(row["candidate_id"]) for row in rows]
            for name in names:
                selected = selections[name]
                if len(selected) != len(algorithm4) or len(set(selected)) != len(selected):
                    raise AssertionError(f"{name}: budget or uniqueness failure")
                if any(not 0 <= index < len(candidate_ids) for index in selected):
                    raise AssertionError(f"{name}: selection outside candidate pool")
                if "backbone" in name:
                    radius = int(name.rsplit("R", 1)[1])
                    backbone = algorithm4[: max(0, len(algorithm4) - radius)]
                    if selected[: len(backbone)] != backbone:
                        raise AssertionError(f"{name}: frozen backbone changed")
                for index in selected:
                    writers[name].writerow([insertion_id, candidate_ids[index]])
                edge_counts[name] += len(selected)
                changed_events[name] += set(selected) != set(algorithm4)
            events += 1
            if events % 250 == 0:
                if shutil.disk_usage(args.output).free < minimum_free_bytes:
                    raise OSError("E0 disk safety stop during plan generation")
                print(
                    f"{args.dataset}-b{args.seed}: planned {events} insertions",
                    flush=True,
                )
            if args.maximum_insertions and events >= args.maximum_insertions:
                break
    finally:
        for stream in streams.values():
            stream.close()

    expected_events = points - 1
    complete = not args.maximum_insertions and events == expected_events
    if not args.maximum_insertions and not complete:
        raise RuntimeError(f"plan covers {events}/{expected_events} insertions")
    plan_hashes = {name: sha256(args.output / f"{name}.csv") for name in names}
    metadata = {
        "status": "complete" if complete else "smoke_complete",
        "dataset": args.dataset,
        "build_seed": args.seed,
        "insertions": events,
        "expected_insertions": expected_events,
        "methods": names,
        "method_count_with_original": len(names) + 1,
        "edge_counts": edge_counts,
        "changed_events_vs_algorithm4": changed_events,
        "plan_sha256": plan_hashes,
        "elapsed_seconds": time.perf_counter() - start,
        "candidate_source": str(raw / "insertion_candidates.csv.gz"),
        "local_neighbor_cache": str(args.neighbors / f"{args.dataset}.npz"),
        "accessed_sources": ["frozen_train_prefix_fbin", "candidate_logs", "local_neighbor_cache"],
        "query_independent": True,
        "formal_test_members_accessed": False,
        "e1_authorized": False,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, sort_keys=True), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=["sift_10k", "glove100_10k", "arxiv_nomic_10k"])
    parser.add_argument("seed", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_e0.yaml"))
    parser.add_argument(
        "--inputs", type=Path, default=Path("results/gb_mpcc/r0_inputs/manifest.json")
    )
    parser.add_argument("--raw", type=Path, default=Path("results/gb_mpcc/r0_candidates"))
    parser.add_argument(
        "--neighbors", type=Path, default=Path("results/gb_mpcc/e0/local_neighbors")
    )
    parser.add_argument("--maximum-insertions", type=int)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
