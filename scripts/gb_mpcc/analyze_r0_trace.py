#!/usr/bin/env python3
"""Analyze frozen proxy-to-route mechanism transfer for Replay Gate R0."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

BASELINES = (
    "algorithm4",
    "geometry",
    "maxmin_angle",
    "length_aware_angle",
    "ggr_0",
)
MATCHED_CONTROLS = (
    "geometry_backbone_random",
    "geometry_backbone_mpcc_shuffled",
)
COMPARATORS = (*BASELINES, *MATCHED_CONTROLS)
GB = "geometry_backbone_mpcc"
LABELS = (
    "strict_progress",
    "multiplicative_progress_eta_0_05",
    "beam_admissible",
    "expanded_later",
    "missed_true_neighbor_opportunity",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_float_matrix(path: Path) -> np.ndarray:
    with path.open("rb") as stream:
        rows, columns = struct.unpack("<QQ", stream.read(16))
        values = np.fromfile(stream, dtype=np.float32)
    if values.size != rows * columns:
        raise ValueError(f"invalid float matrix: {path}")
    return values.reshape(rows, columns)


def parse_labels(value: Any) -> tuple[int, ...]:
    if value is None or (isinstance(value, float) and np.isnan(value)) or value == "":
        return ()
    return tuple(int(item) for item in str(value).split(";"))


def metric_distances(query: np.ndarray, points: np.ndarray, metric: str) -> np.ndarray:
    if metric == "ip":
        return 1.0 - points @ query
    return np.einsum("ij,ij->i", points - query, points - query)


def euclidean_distances(query: np.ndarray, points: np.ndarray, metric: str) -> np.ndarray:
    raw = metric_distances(query, points, metric)
    return np.sqrt(np.maximum(raw * (2.0 if metric == "ip" else 1.0), 0.0))


def safe_spearman(first: pd.Series, second: pd.Series) -> float:
    if first.nunique() < 2 or second.nunique() < 2:
        return float("nan")
    return float(spearmanr(first, second).statistic)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--addendum",
        type=Path,
        default=Path("preregistration/gb_mpcc_r0_trace_addendum.yaml"),
    )
    parser.add_argument(
        "--structural-root",
        type=Path,
        default=Path("results/gb_mpcc/r0_replay_trace_ready"),
    )
    parser.add_argument("--trace-root", type=Path, default=Path("results/gb_mpcc/r0_trace"))
    parser.add_argument(
        "--input-manifest",
        type=Path,
        default=Path("results/gb_mpcc/r0_inputs/manifest.json"),
    )
    parser.add_argument("--output", type=Path, default=Path("results/gb_mpcc/r0_trace_analysis"))
    parser.add_argument(
        "--report", type=Path, default=Path("reports/replay_gate_r0_preliminary.md")
    )
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.mkdir(parents=True)

    addendum = yaml.safe_load(args.addendum.read_text(encoding="utf-8"))
    if (
        addendum["status"] != "frozen_before_reading_query_trace_events"
        or addendum["firewall"]["formal_test_access"] != "forbidden"
        or addendum["index_policy"]["construction"] != "forbidden"
        or addendum["index_policy"]["mutation"] != "forbidden"
    ):
        raise PermissionError("trace addendum firewall or index policy is not frozen")
    trace_manifest = json.loads((args.trace_root / "manifest.json").read_text(encoding="utf-8"))
    if (
        trace_manifest["status"] != "complete"
        or trace_manifest["complete_runs"] != 9
        or trace_manifest["formal_test_members_accessed"] is not False
        or trace_manifest["index_built_or_mutated"] is not False
        or trace_manifest["addendum_sha256"] != sha256(args.addendum)
    ):
        raise ValueError("trace manifest failed its frozen provenance checks")
    structural_path = args.structural_root / "per_event_selector.csv.gz"
    if trace_manifest["structural_replay_sha256"] != sha256(structural_path):
        raise ValueError("trace and structural replay hashes disagree")
    structural_meta = json.loads(
        (args.structural_root / "metadata.json").read_text(encoding="utf-8")
    )
    if structural_meta["formal_test_members_accessed"] is not False:
        raise PermissionError("structural replay firewall failure")

    structural = pd.read_csv(structural_path)
    selectors = tuple(structural["selector"].unique())
    if (
        len(structural) != 2304 * len(selectors)
        or structural["selected_external_labels"].isna().any()
    ):
        raise ValueError("structural selector matrix is incomplete")
    structural_index = {
        (row.dataset, int(row.build_seed), int(row.external_source_label), row.selector): row
        for row in structural.itertuples(index=False)
    }
    input_manifest = json.loads(args.input_manifest.read_text(encoding="utf-8"))
    inputs = {item["dataset"]: item for item in input_manifest["inputs"]}
    vectors: dict[str, np.ndarray] = {}
    queries: dict[str, np.ndarray] = {}
    metrics: dict[str, str] = {}
    for dataset, item in inputs.items():
        vectors[dataset] = np.memmap(
            item["path"],
            dtype=np.float32,
            mode="r",
            shape=(int(item["points"]), int(item["dimensions"])),
        )
        queries[dataset] = read_float_matrix(
            args.trace_root / "inputs" / f"{dataset}_queries.f32bin"
        )
        metrics[dataset] = "ip" if item["normalized"] else "l2"

    state_records: list[dict[str, Any]] = []
    reached: dict[tuple[str, int], set[int]] = {}
    for run in trace_manifest["runs"]:
        dataset, seed = run["dataset"], int(run["build_seed"])
        trace_path = args.trace_root / "raw" / run["run_id"] / "matched_trace_states.csv.gz"
        if sha256(trace_path) != run["trace_sha256"]:
            raise ValueError(f"{run['run_id']}: trace checksum mismatch")
        trace = pd.read_csv(trace_path)
        if len(trace) != run["matched_trace_rows"]:
            raise ValueError(f"{run['run_id']}: trace row-count mismatch")
        reached[(dataset, seed)] = set(int(value) for value in trace["source_label"])
        for state in trace.itertuples(index=False):
            query = queries[dataset][int(state.query_id)]
            source_label = int(state.source_label)
            center = np.asarray(vectors[dataset][source_label])
            center_raw = float(metric_distances(query, center[None, :], metrics[dataset])[0])
            if not np.isclose(center_raw, float(state.source_distance), rtol=2e-4, atol=2e-5):
                raise ValueError("recomputed center distance disagrees with native trace")
            center_euclidean = float(
                euclidean_distances(query, center[None, :], metrics[dataset])[0]
            )
            later = set(parse_labels(state.later_expanded_labels))
            returned = set(parse_labels(state.returned_top10))
            truth = set(parse_labels(state.truth_top10))
            missed_truth = truth - returned
            for selector in selectors:
                key = (dataset, seed, source_label, selector)
                if key not in structural_index:
                    raise ValueError(f"trace source absent from structural replay: {key}")
                proxy = structural_index[key]
                selected = parse_labels(proxy.selected_external_labels)
                candidate_points = np.asarray(vectors[dataset][list(selected)])
                raw = metric_distances(query, candidate_points, metrics[dataset])
                euclidean = euclidean_distances(query, candidate_points, metrics[dataset])
                record = {
                    "dataset": dataset,
                    "build_seed": seed,
                    "query_id": int(state.query_id),
                    "ef": int(state.ef),
                    "event_index": int(state.event_index),
                    "source_label": source_label,
                    "selector": selector,
                    "strict_progress": int(np.any(euclidean < center_euclidean)),
                    "multiplicative_progress_eta_0_05": int(
                        np.any(euclidean <= 0.95 * center_euclidean)
                    ),
                    "beam_admissible": int(np.any(raw < float(state.lower_bound))),
                    "expanded_later": int(bool(set(selected) & later)),
                    "missed_true_neighbor_opportunity": int(bool(set(selected) & missed_truth)),
                    "proxy_hard_progress_coverage": float(proxy.hard_progress_coverage),
                }
                state_records.append(record)
    states = pd.DataFrame.from_records(state_records)
    if len(states) != (
        sum(run["matched_trace_rows"] for run in trace_manifest["runs"]) * len(selectors)
    ):
        raise RuntimeError("trace selector-state matrix is incomplete")
    states.to_csv(args.output / "per_state_selector.csv.gz", index=False, compression="gzip")

    event_keys = ["dataset", "build_seed", "source_label", "selector"]
    events = states.groupby(event_keys, as_index=False).agg(
        states=("query_id", "size"),
        proxy_hard_progress_coverage=("proxy_hard_progress_coverage", "first"),
        **{label: (label, "mean") for label in LABELS},
    )
    events.to_csv(args.output / "per_reached_event_selector.csv", index=False)
    summary = events.groupby(["dataset", "build_seed", "selector"], as_index=False).agg(
        reached_events=("source_label", "size"),
        state_count=("states", "sum"),
        proxy_hard_progress_coverage=("proxy_hard_progress_coverage", "mean"),
        **{label: (label, "mean") for label in LABELS},
    )
    summary["reached_event_fraction"] = summary.apply(
        lambda row: len(reached[(row.dataset, int(row.build_seed))]) / 256.0, axis=1
    )
    summary.to_csv(args.output / "summary.csv", index=False)

    paired_rows: list[dict[str, Any]] = []
    for (dataset, seed), group in events.groupby(["dataset", "build_seed"]):
        indexed = group.set_index(["source_label", "selector"])
        common_sources = sorted(set(group["source_label"]))
        for baseline in COMPARATORS:
            row: dict[str, Any] = {
                "dataset": dataset,
                "build_seed": int(seed),
                "baseline": baseline,
                "events": len(common_sources),
            }
            for label in LABELS:
                differences = [
                    float(indexed.loc[(source, GB), label])
                    - float(indexed.loc[(source, baseline), label])
                    for source in common_sources
                ]
                row[f"delta_{label}"] = float(np.mean(differences))
            paired_rows.append(row)
    paired = pd.DataFrame.from_records(paired_rows)
    paired.to_csv(args.output / "paired_differences.csv", index=False)

    calibration_rows: list[dict[str, Any]] = []
    for (dataset, selector), group in events.groupby(["dataset", "selector"]):
        calibration_rows.append(
            {
                "dataset": dataset,
                "selector": selector,
                "events": len(group),
                "spearman_proxy_vs_real_strict": safe_spearman(
                    group["proxy_hard_progress_coverage"], group["strict_progress"]
                ),
                "mean_absolute_calibration_error": float(
                    np.mean(
                        np.abs(group["proxy_hard_progress_coverage"] - group["strict_progress"])
                    )
                ),
                "signed_proxy_minus_real": float(
                    np.mean(group["proxy_hard_progress_coverage"] - group["strict_progress"])
                ),
            }
        )
    calibration = pd.DataFrame.from_records(calibration_rows)
    calibration.to_csv(args.output / "proxy_calibration.csv", index=False)

    dataset_directions: dict[str, dict[str, int]] = {}
    for dataset, group in paired.groupby("dataset"):
        dataset_directions[dataset] = {}
        for baseline in COMPARATORS:
            comparison = group[group["baseline"] == baseline]
            dataset_directions[dataset][baseline] = int(
                (comparison["delta_strict_progress"] > 0).sum()
            )
    metadata = {
        "status": "trace_analysis_complete",
        "state_selector_rows": len(states),
        "matched_trace_states": len(states) // len(selectors),
        "selectors": list(selectors),
        "reached_events": int(
            events[["dataset", "build_seed", "source_label"]].drop_duplicates().shape[0]
        ),
        "formal_test_members_accessed": False,
        "index_built_or_mutated": False,
        "addendum_sha256": sha256(args.addendum),
        "structural_replay_sha256": sha256(structural_path),
        "dataset_seed_positive_directions_vs_baselines": dataset_directions,
        "r0_gate_decision": "PENDING_FINAL_R0_ADJUDICATION",
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report_lines = [
        "# Replay Gate R0 preliminary mechanism analysis",
        "",
        "Status: **PENDING_FINAL_R0_ADJUDICATION**. This report contains the frozen "
        "structural replay and read-only design-dev trace diagnostics; it does not "
        "authorize E0.",
        "",
        f"- Structural events: {structural_meta['events']} across 9 dataset/seed runs.",
        f"- Matched route states: {metadata['matched_trace_states']}.",
        f"- Reached sampled events: {metadata['reached_events']} of 2304.",
        "- Existing Original 100K indexes were loaded read-only; no graph was built or mutated.",
        "- Formal test members accessed: false.",
        "",
        "## GB-MPCC paired real-route differences",
        "",
        "Positive values favor Geometry-Backbone-MPCC. Values are macro-averaged over "
        "sampled events reached by at least one frozen query/ef trace.",
        "",
        "```text",
        paired.round(6).to_string(index=False),
        "```",
        "",
        "## Proxy calibration",
        "",
        "```text",
        calibration[calibration["selector"].isin([GB, *COMPARATORS])]
        .round(6)
        .to_string(index=False),
        "```",
        "",
        "The final PASS/STOP label must be assigned only after checking the preregistered "
        "two-dataset, majority-seed, strong-baseline, and edge-length criteria together.",
    ]
    args.report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
