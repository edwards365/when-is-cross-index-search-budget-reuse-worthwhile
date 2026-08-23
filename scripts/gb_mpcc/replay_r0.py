#!/usr/bin/env python3
"""Offline structural Replay Gate R0 on frozen HNSW construction candidates.

This program reads only exported train-prefix vectors and candidate recorder output.
It never builds or saves an index and has no code path for HDF5 test/ground truth.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Iterator
from itertools import groupby
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from narhnsw.controls import geometry_safe_random_selection
from narhnsw.ggr import geometry_guarded_resistance_selection
from narhnsw.mpcc_selectors import (
    frozen_directions,
    frozen_radii,
    length_aware_angle_select,
    maxmin_angle_select,
    mpcc_select,
    progress_masks,
    random_backbone_select,
    shuffled_backbone_mpcc_select,
    shuffled_mpcc_select,
)
from narhnsw.resistance import (
    effective_resistance_matrix,
    gaussian_weight_graph,
    greedy_neighbor_selection,
)

SELECTORS = (
    "algorithm4",
    "geometry",
    "maxmin_angle",
    "length_aware_angle",
    "ggr_0",
    "geometry_safe_random",
    "mpcc_shuffled",
    "geometry_backbone_random",
    "geometry_backbone_mpcc_shuffled",
    "pure_mpcc",
    "geometry_backbone_mpcc",
)


def grouped_rows(path: Path) -> Iterator[tuple[int, list[dict[str, str]]]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        rows = (row for row in csv.DictReader(stream) if int(row["layer"]) == 0)
        for insertion_id, group in groupby(rows, key=lambda row: int(row["insertion_id"])):
            yield insertion_id, list(group)


def sampled_insertions(path: Path, dataset: str, seed: int, maximum: int) -> set[int]:
    eligible: list[tuple[bytes, int]] = []
    for insertion_id, rows in grouped_rows(path):
        candidates = {int(row["candidate_id"]) for row in rows}
        accepted = [row for row in rows if row["decision"] == "accepted"]
        if len(candidates) >= 16 and accepted:
            payload = f"{dataset}:{seed}:{insertion_id}".encode()
            eligible.append((hashlib.sha256(payload).digest(), insertion_id))
    eligible.sort()
    return {item[1] for item in eligible[:maximum]}


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
    for insertion_id, rows in grouped_rows(path):
        result[insertion_id].extend(
            (int(row["source"]), int(row["target"]), row["action"]) for row in rows
        )
    return dict(result)


def insertion_scale(points: np.ndarray, adjacency: np.ndarray) -> float:
    distances = np.linalg.norm(points[:, None] - points[None, :], axis=-1)
    observed = distances[np.triu(adjacency, k=1)]
    positive = observed[observed > np.finfo(float).eps]
    if not len(positive):
        raise ValueError("cannot define Scheme-A Gaussian scale")
    return float(np.median(positive))


def jaccard(first: tuple[int, ...], second: tuple[int, ...]) -> float:
    left, right = set(first), set(second)
    return len(left & right) / len(left | right) if left or right else 1.0


def hard_coverage(masks: np.ndarray, selected: tuple[int, ...]) -> float:
    return float(np.logical_or.reduce(masks[list(selected)], axis=0).mean()) if selected else 0.0


def selection_metrics(
    center: np.ndarray,
    candidates: np.ndarray,
    selected: tuple[int, ...],
    algorithm4: tuple[int, ...],
    geometry: tuple[int, ...],
    masks: dict[str, np.ndarray],
    eta_mask: np.ndarray,
    bin_labels: np.ndarray,
    directions: np.ndarray,
    radii: np.ndarray,
    local_scale: float,
) -> dict[str, float | int]:
    chosen = list(selected)
    delta = candidates - center
    lengths = np.linalg.norm(delta, axis=1)
    unit = delta / lengths[:, None]
    empirical = masks["empirical_direction"]
    covered = (
        np.logical_or.reduce(empirical[chosen], axis=0) if chosen else np.zeros(len(radii), bool)
    )
    query_states = center + local_scale * radii[:, None] * directions
    if chosen:
        center_distance = local_scale * radii
        selected_distance = np.linalg.norm(
            query_states[:, None, :] - candidates[chosen][None, :, :], axis=2
        )
        progress = np.maximum(0.0, 1.0 - selected_distance.min(axis=1) / center_distance)
        selected_unit = unit[chosen]
        pairwise = selected_unit @ selected_unit.T
        upper = pairwise[np.triu_indices(len(chosen), k=1)]
    else:
        progress = np.zeros(len(radii))
        upper = np.array([], dtype=np.float64)
    result: dict[str, float | int] = {
        "selected_count": len(selected),
        "algorithm4_jaccard": jaccard(selected, algorithm4),
        "geometry_jaccard": jaccard(selected, geometry),
        "changed_edge_fraction": 1.0
        - len(set(selected) & set(algorithm4)) / max(1, len(algorithm4)),
        "hard_progress_coverage": float(covered.mean()),
        "hard_progress_near": float(covered[bin_labels == 0].mean()),
        "hard_progress_medium": float(covered[bin_labels == 1].mean()),
        "hard_progress_far": float(covered[bin_labels == 2].mean()),
        "multiplicative_progress_eta_0_05": hard_coverage(eta_mask, selected),
        "best_progress_rate": float(progress.mean()),
        "edge_length_mean_scaled": float(lengths[chosen].mean() / local_scale),
        "edge_length_median_scaled": float(np.median(lengths[chosen]) / local_scale),
        "pairwise_cosine_mean": float(upper.mean()) if len(upper) else math.nan,
        "pairwise_cosine_max": float(upper.max()) if len(upper) else math.nan,
    }
    for model, model_masks in masks.items():
        result[f"{model}_coverage"] = hard_coverage(model_masks, selected)
    return result


def replay_run(
    dataset: dict[str, Any],
    seed: int,
    protocol: dict[str, Any],
    input_record: dict[str, Any],
    raw_root: Path,
) -> list[dict[str, Any]]:
    dataset_id = str(dataset["id"])
    run_id = f"{dataset_id}-b{seed}"
    run = raw_root / run_id
    candidate_path = run / "insertion_candidates.csv.gz"
    selected_insertions = sampled_insertions(
        candidate_path,
        dataset_id,
        seed,
        int(protocol["replay_sampling"]["maximum_events_per_dataset_seed"]),
    )
    points = int(input_record["points"])
    dimensions = int(input_record["dimensions"])
    vectors = np.memmap(
        input_record["path"], dtype=np.float32, mode="r", shape=(points, dimensions)
    )
    mapping = read_mapping(run / "internal_to_external.csv", points)
    changes = read_changes(run / "insertion_adjacency_changes.csv.gz")
    adjacency = [set() for _ in range(points)]
    output: list[dict[str, Any]] = []

    for insertion_id, rows in grouped_rows(candidate_path):
        candidate_ids = [int(row["candidate_id"]) for row in rows]
        accepted_ids = [int(row["candidate_id"]) for row in rows if row["decision"] == "accepted"]
        adjacency[insertion_id].update(accepted_ids)
        for source, target, action in changes.get(insertion_id, []):
            if action == "added":
                adjacency[source].add(target)
            elif action == "removed":
                if target not in adjacency[source]:
                    raise ValueError(f"{run_id}: removing absent edge {source}->{target}")
                adjacency[source].remove(target)
            else:
                raise ValueError(f"unknown adjacency action {action}")
        if insertion_id not in selected_insertions:
            continue

        external_center = int(mapping[insertion_id])
        external_candidates = mapping[np.asarray(candidate_ids)]
        center = np.asarray(vectors[external_center], dtype=np.float64)
        candidate_points = np.asarray(vectors[external_candidates], dtype=np.float64)
        labels = external_candidates.astype(np.int64)
        accepted_set = set(accepted_ids)
        algorithm4 = tuple(
            index for index, item in enumerate(candidate_ids) if item in accepted_set
        )
        budget = len(algorithm4)

        all_delta = np.asarray(vectors, dtype=np.float64) - center
        all_distances = np.einsum("ij,ij->i", all_delta, all_delta)
        all_distances[external_center] = np.inf
        nearest = np.argpartition(all_distances, 64)[:64]
        nearest = nearest[np.argsort(all_distances[nearest], kind="stable")]
        local_scale = float(np.sqrt(all_distances[nearest[15]]))
        local_displacements = np.asarray(vectors[nearest], dtype=np.float64) - center

        local_ids = [insertion_id, *candidate_ids]
        local_index = {node: index for index, node in enumerate(local_ids)}
        base = np.zeros((len(local_ids), len(local_ids)), dtype=bool)
        local_set = set(local_ids)
        for source in local_ids:
            for target in adjacency[source] & local_set:
                base[local_index[source], local_index[target]] = True
        base |= base.T
        base[0, 1:] = True
        base[1:, 0] = True
        np.fill_diagonal(base, False)
        local_points = np.vstack([center, candidate_points])
        scheme_rho = insertion_scale(local_points, base)
        weights = gaussian_weight_graph(local_points, base, rho=scheme_rho)
        resistance = effective_resistance_matrix(weights)
        leverage = weights[0, 1:] * resistance[0, 1:]
        if np.any(~np.isfinite(leverage)):
            raise FloatingPointError(f"{run_id}/{insertion_id}: nonfinite Scheme-A leverage")

        event_seed = 202608240000 + seed * 1000003 + external_center
        state_masks: dict[str, np.ndarray] = {}
        empirical_directions: np.ndarray | None = None
        radii: np.ndarray | None = None
        bin_labels: np.ndarray | None = None
        for offset, model in enumerate(protocol["state_distribution"]["models"]):
            rng = np.random.default_rng(event_seed + offset * 10000019)
            model_radii, model_bins = frozen_radii(
                int(protocol["state_distribution"]["state_samples"]), rng
            )
            directions = frozen_directions(model, local_displacements, len(model_radii), rng)
            state_masks[model] = progress_masks(
                center, candidate_points, local_scale, directions, model_radii
            )
            if model == "empirical_direction":
                radii, bin_labels, empirical_directions = model_radii, model_bins, directions
        assert radii is not None and bin_labels is not None and empirical_directions is not None
        empirical_masks = state_masks["empirical_direction"]
        eta_mask = progress_masks(
            center, candidate_points, local_scale, empirical_directions, radii, eta=0.05
        )

        geometry_list, _ = greedy_neighbor_selection(
            center,
            candidate_points,
            np.zeros(len(rows)),
            budget,
            alpha=0.0,
            beta=1.0,
            gamma=1.0,
            sigma=0.5,
        )
        geometry = tuple(geometry_list)
        ggr = geometry_guarded_resistance_selection(
            center, candidate_points, leverage, budget, epsilon=0.0
        )
        selections: dict[str, tuple[int, ...]] = {
            "algorithm4": algorithm4,
            "geometry": geometry,
            "maxmin_angle": maxmin_angle_select(center, candidate_points, labels, budget),
            "length_aware_angle": length_aware_angle_select(
                center, candidate_points, labels, budget
            ),
            "ggr_0": ggr.selected,
            "geometry_safe_random": geometry_safe_random_selection(
                center, candidate_points, budget, requested_swaps=len(ggr.swaps), seed=event_seed
            ).selected,
            "mpcc_shuffled": shuffled_mpcc_select(
                empirical_masks, budget, np.random.default_rng(event_seed + 30000057)
            ),
            "geometry_backbone_random": random_backbone_select(
                len(rows),
                budget,
                algorithm4[: min(12, budget)],
                np.random.default_rng(event_seed + 40000063),
            ),
            "geometry_backbone_mpcc_shuffled": shuffled_backbone_mpcc_select(
                empirical_masks,
                budget,
                algorithm4[: min(12, budget)],
                np.random.default_rng(event_seed + 50000069),
            ),
            "pure_mpcc": mpcc_select(empirical_masks, budget),
            "geometry_backbone_mpcc": mpcc_select(
                empirical_masks, budget, algorithm4[: min(12, budget)]
            ),
        }
        if tuple(selections) != SELECTORS:
            raise AssertionError("selector matrix is incomplete")
        for selector, selected in selections.items():
            record: dict[str, Any] = {
                "dataset": dataset_id,
                "build_seed": seed,
                "insertion_id": insertion_id,
                "external_source_label": external_center,
                "candidate_count": len(rows),
                "budget": budget,
                "selector": selector,
                "selected_external_labels": ";".join(
                    str(int(external_candidates[index])) for index in selected
                ),
                "ggr_swap_count": len(ggr.swaps),
            }
            record.update(
                selection_metrics(
                    center,
                    candidate_points,
                    selected,
                    algorithm4,
                    geometry,
                    state_masks,
                    eta_mask,
                    bin_labels,
                    empirical_directions,
                    radii,
                    local_scale,
                )
            )
            output.append(record)
        print(
            f"{run_id}: replayed {len(output) // len(SELECTORS)}/{len(selected_insertions)}",
            flush=True,
        )
    if len(output) != len(selected_insertions) * len(SELECTORS):
        raise RuntimeError(f"{run_id}: sampled replay matrix is incomplete")
    return output


def write_outputs(rows: list[dict[str, Any]], output: Path, protocol: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    detail = output / "per_event_selector.csv.gz"
    with gzip.open(detail, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    numeric = [key for key, value in rows[0].items() if isinstance(value, (int, float))]
    grouped: defaultdict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["dataset"], row["build_seed"], row["selector"])].append(row)
    with (output / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = [
            "dataset",
            "build_seed",
            "selector",
            "events",
            *[f"mean_{key}" for key in numeric],
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for (dataset, seed, selector), records in sorted(grouped.items()):
            item: dict[str, Any] = {
                "dataset": dataset,
                "build_seed": seed,
                "selector": selector,
                "events": len(records),
            }
            for key in numeric:
                values = np.asarray([float(record[key]) for record in records])
                item[f"mean_{key}"] = float(np.nanmean(values))
            writer.writerow(item)
    digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    (output / "metadata.json").write_text(
        json.dumps(
            {
                "status": "structural_replay_complete",
                "events": len(rows) // len(SELECTORS),
                "selector_rows": len(rows),
                "protocol_sha256": digest,
                "accessed_sources": ["frozen_train_prefix_fbin", "candidate_recorder_logs"],
                "formal_test_members_accessed": False,
                "index_built_or_saved": False,
                "development_trace_diagnostics_complete": False,
                "r0_gate_decision": "PENDING_TRACE_DIAGNOSTICS",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_r0.yaml"))
    parser.add_argument(
        "--inputs", type=Path, default=Path("results/gb_mpcc/r0_inputs/manifest.json")
    )
    parser.add_argument("--raw", type=Path, default=Path("results/gb_mpcc/r0_candidates"))
    parser.add_argument("--output", type=Path, default=Path("results/gb_mpcc/r0_replay"))
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    inputs = json.loads(args.inputs.read_text(encoding="utf-8"))
    input_map = {item["dataset"]: item for item in inputs["inputs"]}
    rows: list[dict[str, Any]] = []
    for dataset in protocol["datasets"]:
        for seed in protocol["original_candidate_recording"]["build_seeds"]:
            rows.extend(
                replay_run(dataset, int(seed), protocol, input_map[dataset["id"]], args.raw)
            )
    write_outputs(rows, args.output, args.protocol)
    print(json.dumps({"status": "structural_replay_complete", "selector_rows": len(rows)}))


if __name__ == "__main__":
    main()
