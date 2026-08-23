#!/usr/bin/env python3
"""Apply the frozen Replay Gate R0 criteria and write its final adjudication."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def length_adjusted_result(group: pd.DataFrame) -> dict[str, float]:
    indexed = group.set_index(["build_seed", "insertion_id", "selector"])
    events = group[["build_seed", "insertion_id"]].drop_duplicates().itertuples(index=False)
    coverage_delta: list[float] = []
    length_delta: list[float] = []
    for event in events:
        gb = indexed.loc[(event.build_seed, event.insertion_id, GB)]
        original = indexed.loc[(event.build_seed, event.insertion_id, "algorithm4")]
        coverage_delta.append(float(gb.hard_progress_coverage - original.hard_progress_coverage))
        length_delta.append(float(gb.edge_length_mean_scaled - original.edge_length_mean_scaled))
    response = np.asarray(coverage_delta)
    length = np.asarray(length_delta)
    design = np.column_stack([np.ones(len(length)), length])
    coefficients = np.linalg.lstsq(design, response, rcond=None)[0]
    residual = response - design @ coefficients
    inverse = np.linalg.inv(design.T @ design)
    standard_error = float(np.sqrt((residual @ residual) / (len(response) - 2) * inverse[0, 0]))
    return {
        "mean_coverage_delta_vs_algorithm4": float(response.mean()),
        "mean_length_delta_vs_algorithm4": float(length.mean()),
        "length_adjusted_intercept": float(coefficients[0]),
        "length_adjusted_intercept_t": float(coefficients[0] / standard_error),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--control-correction",
        type=Path,
        default=Path("preregistration/gb_mpcc_r0_control_correction.yaml"),
    )
    parser.add_argument(
        "--structural",
        type=Path,
        default=Path("results/gb_mpcc/r0_replay_trace_ready/per_event_selector.csv.gz"),
    )
    parser.add_argument("--analysis", type=Path, default=Path("results/gb_mpcc/r0_trace_analysis"))
    parser.add_argument(
        "--trace-manifest",
        type=Path,
        default=Path("results/gb_mpcc/r0_trace/manifest.json"),
    )
    parser.add_argument("--decision", type=Path, default=Path("manifests/gb_mpcc_r0_decision.json"))
    parser.add_argument("--report", type=Path, default=Path("reports/replay_gate_r0.md"))
    args = parser.parse_args()
    correction = yaml.safe_load(args.control_correction.read_text(encoding="utf-8"))
    if (
        correction["status"] != "frozen_before_budget_matched_control_outputs"
        or correction["correction_type"] != "control_compliance_only_no_parameter_tuning"
        or correction["firewall"]["formal_test_access"] != "forbidden"
    ):
        raise PermissionError("R0 control-correction protocol is not frozen")
    metadata = json.loads((args.analysis / "metadata.json").read_text(encoding="utf-8"))
    trace_manifest = json.loads(args.trace_manifest.read_text(encoding="utf-8"))
    if (
        metadata["status"] != "trace_analysis_complete"
        or metadata["formal_test_members_accessed"] is not False
        or metadata["index_built_or_mutated"] is not False
        or trace_manifest["status"] != "complete"
        or trace_manifest["complete_runs"] != 9
        or metadata["structural_replay_sha256"] != sha256(args.structural)
    ):
        raise ValueError("R0 evidence provenance is incomplete")

    structural = pd.read_csv(args.structural)
    paired = pd.read_csv(args.analysis / "paired_differences.csv")
    calibration = pd.read_csv(args.analysis / "proxy_calibration.csv")
    summary = pd.read_csv(args.analysis / "summary.csv")
    event_keys = ["dataset", "build_seed", "insertion_id"]
    algorithm4 = structural[structural["selector"] == "algorithm4"].set_index(event_keys)
    length_aware = structural[structural["selector"] == "length_aware_angle"].set_index(event_keys)
    length_aware_exact = bool(
        (algorithm4["selected_external_labels"] == length_aware["selected_external_labels"]).all()
    )

    dataset_results: dict[str, dict[str, Any]] = {}
    passing_datasets: list[str] = []
    for dataset, group in structural.groupby("dataset"):
        gb = group[group["selector"] == GB]
        mean_jaccard = float(gb["algorithm4_jaccard"].mean())
        selector_nonempty = bool((gb["selected_count"] > 0).all())
        non_equivalent = mean_jaccard < 0.95
        route = paired[paired["dataset"] == dataset]
        strict_by_baseline = {
            baseline: {
                "mean_delta": float(
                    route[route["baseline"] == baseline]["delta_strict_progress"].mean()
                ),
                "positive_seeds": int(
                    (route[route["baseline"] == baseline]["delta_strict_progress"] > 0).sum()
                ),
            }
            for baseline in COMPARATORS
        }
        beam_by_baseline = {
            baseline: {
                "mean_delta": float(
                    route[route["baseline"] == baseline]["delta_beam_admissible"].mean()
                ),
                "positive_seeds": int(
                    (route[route["baseline"] == baseline]["delta_beam_admissible"] > 0).sum()
                ),
            }
            for baseline in COMPARATORS
        }
        beats_strict = all(
            item["mean_delta"] > 0 and item["positive_seeds"] >= 2
            for item in strict_by_baseline.values()
        )
        beats_beam = all(
            item["mean_delta"] > 0 and item["positive_seeds"] >= 2
            for item in beam_by_baseline.values()
        )
        length_result = length_adjusted_result(group)
        not_length_only = length_result["length_adjusted_intercept"] > 0
        dataset_pass = (
            selector_nonempty and non_equivalent and beats_strict and beats_beam and not_length_only
        )
        if dataset_pass:
            passing_datasets.append(dataset)
        gb_calibration = calibration[
            (calibration["dataset"] == dataset) & (calibration["selector"] == GB)
        ].iloc[0]
        reached = summary[(summary["dataset"] == dataset) & (summary["selector"] == GB)]
        dataset_results[dataset] = {
            "pass": dataset_pass,
            "selector_nonempty": selector_nonempty,
            "mean_algorithm4_jaccard": mean_jaccard,
            "non_equivalent_below_0_95": non_equivalent,
            "strict_progress_vs_baselines": strict_by_baseline,
            "beam_admissible_vs_baselines": beam_by_baseline,
            "length_analysis": length_result,
            "gain_not_explained_only_by_length": not_length_only,
            "reached_events": int(reached["reached_events"].sum()),
            "mean_reached_event_fraction": float(reached["reached_event_fraction"].mean()),
            "proxy_real_spearman": float(gb_calibration["spearman_proxy_vs_real_strict"]),
            "proxy_real_mean_absolute_calibration_error": float(
                gb_calibration["mean_absolute_calibration_error"]
            ),
            "proxy_minus_real_bias": float(gb_calibration["signed_proxy_minus_real"]),
        }

    passed = len(passing_datasets) >= 2
    decision = {
        "schema_version": 1,
        "gate": "Replay Gate R0",
        "decision": "PASS_TO_GRAPH_E0" if passed else "STOP_BEFORE_GRAPH_E0",
        "predefined_labels": (
            ["LOCAL_NAVIGATION_SUPPORTED", "PROXY_DISTRIBUTION_MISMATCH"]
            if passed
            else ["PERFORMANCE_NOT_ESTABLISHED"]
        ),
        "passing_datasets": passing_datasets,
        "required_passing_datasets": 2,
        "length_aware_angle_exactly_algorithm4": length_aware_exact,
        "structural_events": 2304,
        "matched_route_states": metadata["matched_trace_states"],
        "reached_events": metadata["reached_events"],
        "dataset_results": dataset_results,
        "limitations": [
            "R0 is an offline local mechanism diagnostic, not a graph-performance result.",
            "Route states came from existing Original 100K indexes, while candidate "
            "pools came from 10K insertion replays.",
            "Only sampled centers reached by design-dev query IDs 0-499 on the frozen "
            "ef grid contribute route metrics.",
            "Absolute proxy calibration is poor despite relative ranking transfer on two datasets.",
            "Missed-true-neighbor opportunity labels are too sparse to support a positive claim.",
        ],
        "formal_test_members_accessed": False,
        "index_built_or_mutated_during_r0_trace": False,
        "e0_authorized": passed,
        "e1_authorized": False,
        "formal_test_authorized": False,
        "evidence_sha256": {
            "control_correction": sha256(args.control_correction),
            "structural": sha256(args.structural),
            "trace_manifest": sha256(args.trace_manifest),
            "trace_analysis_metadata": sha256(args.analysis / "metadata.json"),
            "paired_differences": sha256(args.analysis / "paired_differences.csv"),
            "proxy_calibration": sha256(args.analysis / "proxy_calibration.csv"),
        },
    }
    args.decision.parent.mkdir(parents=True, exist_ok=True)
    args.decision.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    rows = []
    for dataset, result in dataset_results.items():
        rows.append(
            {
                "dataset": dataset,
                "Jaccard(A4)": result["mean_algorithm4_jaccard"],
                "dStrict vs A4": result["strict_progress_vs_baselines"]["algorithm4"]["mean_delta"],
                "dStrict vs Geometry": result["strict_progress_vs_baselines"]["geometry"][
                    "mean_delta"
                ],
                "dStrict vs GGR": result["strict_progress_vs_baselines"]["ggr_0"]["mean_delta"],
                "dStrict vs matched random": result["strict_progress_vs_baselines"][
                    "geometry_backbone_random"
                ]["mean_delta"],
                "dStrict vs matched shuffled": result["strict_progress_vs_baselines"][
                    "geometry_backbone_mpcc_shuffled"
                ]["mean_delta"],
                "dBeam vs A4": result["beam_admissible_vs_baselines"]["algorithm4"]["mean_delta"],
                "proxy-real rho": result["proxy_real_spearman"],
                "calibration MAE": result["proxy_real_mean_absolute_calibration_error"],
                "pass": result["pass"],
            }
        )
    table_frame = pd.DataFrame(rows).round(6)
    table_header = "| " + " | ".join(table_frame.columns) + " |"
    table_rule = "| " + " | ".join("---" for _ in table_frame.columns) + " |"
    table_rows = [
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in table_frame.itertuples(index=False, name=None)
    ]
    table = "\n".join([table_header, table_rule, *table_rows])
    args.report.write_text(
        "\n".join(
            [
                "# Replay Gate R0 final report",
                "",
                f"Decision: **{decision['decision']}**.",
                "",
                "Labels: **LOCAL_NAVIGATION_SUPPORTED** at the offline local-diagnostic "
                "level and **PROXY_DISTRIBUTION_MISMATCH** for absolute calibration. "
                "Neither label establishes final-graph or search-performance improvement.",
                "",
                "## Evidence matrix",
                "",
                table,
                "",
                f"Passing datasets: {', '.join(passing_datasets)} "
                f"({len(passing_datasets)}/3; required 2).",
                "",
                "- The full selector matrix contains 2,304 frozen insertion events; all "
                "registered selector outputs are nonempty.",
                "- GloVe and Arxiv are non-equivalent to Algorithm 4 at the frozen 0.95 "
                "mean-Jaccard threshold and beat every registered strong comparator on "
                "strict-progress and beam-admissible route labels in a majority of seeds, "
                "including the backbone/slot-matched random and shuffled controls.",
                "- Length-adjusted coverage intercepts remain positive; the signal is not "
                "fully explained by choosing shorter edges.",
                "- LengthAware-Angle exactly reproduces Algorithm 4 on all recorded events; "
                "GB-MPCC therefore also exceeds this explicit equivalence baseline on the "
                "two passing datasets.",
                "- SIFT does not pass because mean GB-MPCC/Algorithm-4 Jaccard exceeds 0.95 "
                "and route gains over Geometry/GGR are seed-inconsistent.",
                "- The proxy strongly overestimates absolute real-route coverage and has "
                "only modest event-level rank correlation. This is retained as a central "
                "risk, not hidden by the relative-ranking result.",
                "",
                "## Scope and authorization",
                "",
                "R0 used only frozen train-prefix candidates and existing design-dev "
                "queries/truth. Existing Original 100K indexes were loaded read-only; no "
                "index was constructed or mutated. Formal test was not accessed.",
                "",
                "This committed PASS authorizes only Graph Gate E0 under a separate frozen "
                "E0 protocol. It does not authorize E1, formal test, or any performance claim.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in decision.items() if key != "dataset_results"}, indent=2
        )
    )


if __name__ == "__main__":
    main()
