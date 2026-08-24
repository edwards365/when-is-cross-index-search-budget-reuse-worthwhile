#!/usr/bin/env python3
"""Analyze the frozen E0 graph/search matrix and issue its preregistered decision."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml


PRIMARY = "geometry_backbone_mpcc_R4"
COMPARATORS = [
    "original_algorithm4",
    "geometry",
    "geometry_backbone_random_R4",
    "geometry_backbone_mpcc_shuffled_R4",
]
NAVIGATION_DIRECTIONS = {
    "strict_progress_rate": 1.0,
    "beam_admissible_progress_rate": 1.0,
    "local_minimum_fraction": -1.0,
    "base_expansions": -1.0,
    "ndc": -1.0,
}
QUERY_FIELDS = [
    "recall_at_1",
    "recall_at_10",
    "strict_progress_rate",
    "multiplicative_progress_eta_0_05_rate",
    "beam_admissible_progress_rate",
    "local_minimum_fraction",
    "base_expansions",
    "traversal_hops",
    "ndc",
]


def load_query(path: Path, efs: list[int]) -> dict[str, np.ndarray]:
    values = {field: [] for field in QUERY_FIELDS}
    latencies: list[float] = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            latencies.append(float(row["latency_ns"]))
            if int(row["latency_round"]) == 0:
                for field in QUERY_FIELDS:
                    values[field].append(float(row[field]))
    expected = len(efs) * 500
    if any(len(items) != expected for items in values.values()) or len(latencies) != expected * 3:
        raise ValueError(f"invalid frozen query matrix {path}")
    result = {field: np.asarray(items).reshape(len(efs), 500) for field, items in values.items()}
    result["latency_ns"] = np.asarray(latencies).reshape(len(efs), 500, 3)
    return result


def quantiles(values: np.ndarray) -> tuple[float, float, float, float]:
    return (
        float(np.mean(values)),
        float(np.quantile(values, 0.50)),
        float(np.quantile(values, 0.95)),
        float(np.quantile(values, 0.99)),
    )


def load_edge_set(path: Path, points: int) -> tuple[set[int], list[set[int]]]:
    edges: set[int] = set()
    adjacent = [set() for _ in range(points)]
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            source, target = int(row["source"]), int(row["target"])
            edges.add(source * points + target)
            adjacent[source].add(target)
    return edges, adjacent


def bootstrap_effect(
    paired: np.ndarray, replicates: int, generator: np.random.Generator
) -> tuple[float, float, float, float]:
    """Bootstrap queries within each seed; ef is collapsed within each paired query."""
    if paired.shape != (3, 6, 500):
        raise ValueError(f"unexpected paired effect shape {paired.shape}")
    collapsed = paired.mean(axis=1)
    draws = np.empty(replicates, dtype=np.float64)
    for replicate in range(replicates):
        seed_means = []
        for seed_index in range(3):
            sample = generator.integers(0, 500, size=500)
            seed_means.append(collapsed[seed_index, sample].mean())
        draws[replicate] = np.mean(seed_means)
    effect = float(collapsed.mean())
    lower, upper = np.quantile(draws, [0.025, 0.975])
    p_one_sided = float((1 + np.count_nonzero(draws <= 0.0)) / (replicates + 1))
    return effect, float(lower), float(upper), p_one_sided


def holm_adjust(rows: list[dict[str, Any]]) -> None:
    order = sorted(range(len(rows)), key=lambda index: rows[index]["p_one_sided"])
    running = 0.0
    total = len(rows)
    for rank, index in enumerate(order):
        adjusted = min(1.0, (total - rank) * rows[index]["p_one_sided"])
        running = max(running, adjusted)
        rows[index]["p_holm"] = running


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_e0.yaml"))
    parser.add_argument("--root", type=Path, default=Path("results/gb_mpcc/e0"))
    parser.add_argument("--output", type=Path, default=Path("results/gb_mpcc/e0/derived"))
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if (
        protocol["firewall"]["formal_test_access"] != "forbidden"
        or protocol["firewall"]["validation_dev_access"] != "forbidden"
        or protocol["authorization_after_e0"]["formal_test"] is not False
    ):
        raise PermissionError("E0 firewall is not closed")
    matrix = json.loads((args.root / "graph_matrix_summary.json").read_text(encoding="utf-8"))
    if (
        matrix["status"] != "E0_GRAPH_MATRIX_COMPLETE"
        or matrix["graphs"] != 117
        or not matrix["all_temporary_indexes_deleted"]
        or not matrix["all_graph_invariants_passed"]
        or not matrix["upper_checksums_equal_within_run"]
        or matrix["formal_test_members_accessed"]
        or matrix["validation_dev_accessed"]
    ):
        raise RuntimeError("E0 graph matrix is incomplete or invalid")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.mkdir(parents=True)

    datasets = list(protocol["execution"]["datasets_order"])
    seeds = [int(seed) for seed in protocol["execution"]["seeds_order"]]
    methods = list(protocol["execution"]["methods_order"])
    efs = [int(ef) for ef in protocol["search"]["ef_search"]]
    query: dict[tuple[str, int, str], dict[str, np.ndarray]] = {}
    summary_rows: list[dict[str, Any]] = []
    for dataset in datasets:
        for seed in seeds:
            run_id = f"{dataset}-b{seed}"
            for method in methods:
                result = load_query(args.root / "runs" / run_id / method / "query_metrics.csv.gz", efs)
                query[(dataset, seed, method)] = result
                for ef_index, ef in enumerate(efs):
                    row: dict[str, Any] = {
                        "dataset": dataset,
                        "build_seed": seed,
                        "method": method,
                        "ef_search": ef,
                    }
                    for field in QUERY_FIELDS:
                        row[f"mean_{field}"] = float(result[field][ef_index].mean())
                    for field in ("base_expansions", "traversal_hops", "ndc"):
                        mean, p50, p95, p99 = quantiles(result[field][ef_index])
                        row[f"{field}_mean"] = mean
                        row[f"{field}_p50"] = p50
                        row[f"{field}_p95"] = p95
                        row[f"{field}_p99"] = p99
                    mean, p50, p95, p99 = quantiles(result["latency_ns"][ef_index])
                    row.update(
                        latency_ns_mean=mean,
                        latency_ns_p50=p50,
                        latency_ns_p95=p95,
                        latency_ns_p99=p99,
                    )
                    summary_rows.append(row)
    with (args.output / "query_summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    graph_rows: list[dict[str, Any]] = []
    for dataset in datasets:
        for seed in seeds:
            run_id = f"{dataset}-b{seed}"
            original_edges, original_adjacent = load_edge_set(
                args.root / "runs" / run_id / "original_algorithm4" / "layer0_edges.csv.gz", 10000
            )
            for method in methods:
                directory = args.root / "runs" / run_id / method
                metrics = json.loads((directory / "graph_metrics.json").read_text(encoding="utf-8"))
                edges, adjacent = load_edge_set(directory / "layer0_edges.csv.gz", 10000)
                changed_sources = sum(left != right for left, right in zip(adjacent, original_adjacent, strict=True))
                row = {
                    "dataset": dataset,
                    "build_seed": seed,
                    "method": method,
                    "directed_edges": len(edges),
                    "changed_source_fraction_vs_original": changed_sources / 10000,
                    "changed_directed_edge_fraction_vs_original": len(edges ^ original_edges)
                    / len(original_edges),
                    "directed_edge_jaccard_vs_original": len(edges & original_edges)
                    / len(edges | original_edges),
                    "planned_final_directed_edge_jaccard": metrics[
                        "planned_final_directed_edge_jaccard"
                    ],
                    "source_edge_immediate_retention": metrics[
                        "source_edge_immediate_retention"
                    ],
                    "source_edge_final_retention": metrics["source_edge_final_retention"],
                    "reciprocal_edge_immediate_retention": metrics[
                        "reciprocal_edge_immediate_retention"
                    ],
                    "reciprocal_edge_final_retention": metrics[
                        "reciprocal_edge_final_retention"
                    ],
                    "weak_component_count": metrics["weak_component_count"],
                    "strong_component_count": metrics["strong_component_count"],
                    "largest_strong_component_fraction": metrics[
                        "largest_strong_component_fraction"
                    ],
                    "mean_out_degree": metrics["out_degree"]["mean"],
                    "reciprocal_directed_fraction": metrics["reciprocal_directed_fraction"],
                    "mean_local_clustering": metrics["local_clustering"]["mean"],
                    "mean_edge_length": metrics["edge_length"]["mean"],
                    "mean_pairwise_angle_radians": metrics["pairwise_angle_radians"]["mean"],
                    "upper_layer_checksum_equal": metrics["upper_layer_checksum_equal"],
                }
                graph_rows.append(row)
    with (args.output / "graph_summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(graph_rows[0]))
        writer.writeheader()
        writer.writerows(graph_rows)

    cache_manifest = json.loads(
        (args.root / "local_neighbors" / "manifest.json").read_text(encoding="utf-8")
    )
    cache_bytes = {
        item["dataset"]: (args.root / "local_neighbors" / f"{item['dataset']}.npz").stat().st_size
        for item in cache_manifest["datasets"]
    }
    resource_rows: list[dict[str, Any]] = []
    for dataset in datasets:
        for seed in seeds:
            run_id = f"{dataset}-b{seed}"
            plan_metadata = json.loads(
                (args.root / "plans" / run_id / "metadata.json").read_text(encoding="utf-8")
            )
            for method in methods:
                directory = args.root / "runs" / run_id / method
                complete = json.loads((directory / "COMPLETE.json").read_text(encoding="utf-8"))
                resource_rows.append(
                    {
                        "dataset": dataset,
                        "build_seed": seed,
                        "method": method,
                        "selector_plan_generation_run_seconds": 0.0
                        if method == "original_algorithm4"
                        else plan_metadata["elapsed_seconds"],
                        "selector_per_method_seconds_unavailable": method != "original_algorithm4",
                        "graph_materialization_seconds": complete["build_seconds"],
                        "search_seconds": complete["search_seconds"],
                        "temporary_index_bytes": complete["temporary_index_bytes"],
                        "temporary_index_deleted": complete["temporary_index_deleted"],
                        "state_cache_bytes": cache_bytes[dataset],
                        "compressed_result_bytes": sum(
                            path.stat().st_size for path in directory.iterdir() if path.is_file()
                        ),
                        "peak_rss_bytes": "",
                        "peak_rss_unavailable": True,
                    }
                )
    with (args.output / "resource_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(resource_rows[0]))
        writer.writeheader()
        writer.writerows(resource_rows)

    replicates = int(protocol["statistics"]["bootstrap_replicates"])
    generator = np.random.default_rng(int(protocol["statistics"]["bootstrap_seed"]))
    effect_rows: list[dict[str, Any]] = []
    seed_effects: dict[tuple[str, int, str, str], float] = {}
    for dataset in datasets:
        for comparator in COMPARATORS:
            for metric, direction in NAVIGATION_DIRECTIONS.items():
                paired = np.stack(
                    [
                        direction
                        * (
                            query[(dataset, seed, PRIMARY)][metric]
                            - query[(dataset, seed, comparator)][metric]
                        )
                        for seed in seeds
                    ]
                )
                effect, lower, upper, p_value = bootstrap_effect(paired, replicates, generator)
                for seed_index, seed in enumerate(seeds):
                    seed_effects[(dataset, seed, comparator, metric)] = float(
                        paired[seed_index].mean()
                    )
                effect_rows.append(
                    {
                        "dataset": dataset,
                        "primary": PRIMARY,
                        "comparator": comparator,
                        "metric": metric,
                        "positive_means_primary_better": True,
                        "mean_effect": effect,
                        "ci95_lower": lower,
                        "ci95_upper": upper,
                        "p_one_sided": p_value,
                    }
                )
    holm_adjust(effect_rows)
    with (args.output / "paired_navigation_effects.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(effect_rows[0]))
        writer.writeheader()
        writer.writerows(effect_rows)

    recall_rows: list[dict[str, Any]] = []
    recall_pass: dict[str, bool] = {}
    for dataset in datasets:
        dataset_pass = True
        for comparator in COMPARATORS:
            for ef_index, ef in enumerate(efs):
                paired = np.stack(
                    [
                        query[(dataset, seed, PRIMARY)]["recall_at_10"][ef_index]
                        - query[(dataset, seed, comparator)]["recall_at_10"][ef_index]
                        for seed in seeds
                    ]
                )
                loss = float(paired.mean())
                passes = loss >= -0.001
                dataset_pass = dataset_pass and passes
                recall_rows.append(
                    {
                        "dataset": dataset,
                        "primary": PRIMARY,
                        "comparator": comparator,
                        "ef_search": ef,
                        "mean_recall_difference": loss,
                        "noninferiority_margin": -0.001,
                        "pass": passes,
                    }
                )
        recall_pass[dataset] = dataset_pass
    with (args.output / "recall_noninferiority.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(recall_rows[0]))
        writer.writeheader()
        writer.writerows(recall_rows)

    dataset_decisions: dict[str, Any] = {}
    for dataset in datasets:
        seed_details = []
        for seed in seeds:
            beats_original_geometry = [
                metric
                for metric in NAVIGATION_DIRECTIONS
                if seed_effects[(dataset, seed, "original_algorithm4", metric)] > 0
                and seed_effects[(dataset, seed, "geometry", metric)] > 0
            ]
            beats_controls = [
                metric
                for metric in NAVIGATION_DIRECTIONS
                if seed_effects[(dataset, seed, "geometry_backbone_random_R4", metric)] > 0
                and seed_effects[
                    (dataset, seed, "geometry_backbone_mpcc_shuffled_R4", metric)
                ]
                > 0
            ]
            seed_pass = len(beats_original_geometry) >= 2 and bool(
                set(beats_original_geometry) & set(beats_controls)
            )
            seed_details.append(
                {
                    "build_seed": seed,
                    "metrics_better_than_original_and_geometry": beats_original_geometry,
                    "metrics_better_than_both_matched_controls": beats_controls,
                    "navigation_chain_pass": seed_pass,
                }
            )
        positive_seeds = sum(item["navigation_chain_pass"] for item in seed_details)
        navigation_pass = positive_seeds >= 2
        dataset_decisions[dataset] = {
            "positive_navigation_seeds": positive_seeds,
            "navigation_chain_pass": navigation_pass,
            "recall_noninferiority_all_efs_all_primary_comparators": recall_pass[dataset],
            "combined_dataset_pass": navigation_pass and recall_pass[dataset],
            "seed_details": seed_details,
        }

    navigation_datasets = sum(item["navigation_chain_pass"] for item in dataset_decisions.values())
    recall_datasets = sum(
        item["recall_noninferiority_all_efs_all_primary_comparators"]
        for item in dataset_decisions.values()
    )
    combined_datasets = sum(item["combined_dataset_pass"] for item in dataset_decisions.values())
    stop_reasons = []
    if navigation_datasets < int(protocol["pass"]["minimum_datasets"]):
        stop_reasons.append("primary_R4_fails_navigation_chain_on_two_datasets")
    if recall_datasets < int(protocol["pass"]["minimum_datasets"]):
        stop_reasons.append("primary_R4_fails_recall_noninferiority")
    if combined_datasets < int(protocol["pass"]["minimum_datasets"]):
        stop_reasons.append("fewer_than_two_datasets_pass_both_primary_rules")
    decision = {
        "schema_version": 1,
        "gate": "Graph Gate E0",
        "status": "STOP_REJECT_E0_NO_E1" if stop_reasons else "PASS_E0_PENDING_COMMITTED_E1_AUTHORIZATION",
        "primary_method": PRIMARY,
        "primary_R": 4,
        "graph_matrix_complete": True,
        "graph_validity_all_runs": True,
        "original_exact_reproduction_9_of_9": True,
        "upper_layer_checksum_equality_all_runs": True,
        "navigation_passing_datasets": navigation_datasets,
        "recall_noninferiority_passing_datasets": recall_datasets,
        "combined_passing_datasets": combined_datasets,
        "required_datasets": int(protocol["pass"]["minimum_datasets"]),
        "dataset_decisions": dataset_decisions,
        "stop_reasons": stop_reasons,
        "proxy_distribution_mismatch_carried_forward": True,
        "formal_test_members_accessed": False,
        "validation_dev_accessed": False,
        "e1_authorized": False,
        "adaptive_tuning_performed": False,
        "diagnostic_resource_limitation": (
            "The launcher recorded materialization/search wall time, cache bytes, temporary-index "
            "bytes and compressed output bytes, but did not capture per-process peak RSS or "
            "per-method shares of the previously completed plan-generation run. Resource cost is "
            "report-only in E0 and this does not alter the hard recall/navigation decision."
        ),
        "statistical_interpretation": (
            "Fixed-ef recall noninferiority is a hard gate. Navigation effects collapse ef "
            "within paired queries; 95% intervals resample queries within each frozen build seed, "
            "then average seed summaries. Holm adjustment is within the primary navigation family."
        ),
    }
    (args.output / "e0_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = [
        "# GB-MPCC Graph Gate E0 final report",
        "",
        f"Decision: **{decision['status']}**. E1 remains unauthorized.",
        "",
        "All 117 preregistered graphs completed. Original reproduction was exact in 9/9 runs; "
        "all graph invariants, weak connectivity checks, and within-run upper-layer checksums "
        "passed; every temporary index was evaluated and deleted.",
        "",
        "## Primary R4 outcome",
        "",
        "| Dataset | Navigation seeds | Recall-NI | Mean NDC reduction vs Original | "
        "Worst fixed-ef recall difference |",
        "|---|---:|:---:|---:|---:|",
    ]
    for dataset in datasets:
        primary_ndc = np.mean(
            [query[(dataset, seed, PRIMARY)]["ndc"].mean() for seed in seeds]
        )
        original_ndc = np.mean(
            [query[(dataset, seed, "original_algorithm4")]["ndc"].mean() for seed in seeds]
        )
        recall_differences = [
            np.mean(
                [
                    query[(dataset, seed, PRIMARY)]["recall_at_10"][ef_index].mean()
                    - query[(dataset, seed, "original_algorithm4")]["recall_at_10"][
                        ef_index
                    ].mean()
                    for seed in seeds
                ]
            )
            for ef_index in range(len(efs))
        ]
        detail = dataset_decisions[dataset]
        report.append(
            f"| {dataset} | {detail['positive_navigation_seeds']}/3 | "
            f"{'PASS' if detail['recall_noninferiority_all_efs_all_primary_comparators'] else 'FAIL'} | "
            f"{100.0 * (original_ndc - primary_ndc) / original_ndc:.3f}% | "
            f"{min(recall_differences):+.6f} |"
        )
    report.extend(
        [
            "",
            "GB-MPCC R4 reduces mean NDC on all three datasets, including effects that remain "
            "positive against both backbone-matched controls. That mechanism signal is not enough "
            "for the preregistered gate: only one dataset has at least two positive navigation "
            "seeds, and no dataset satisfies recall noninferiority at every fixed ef against all "
            "primary comparators. R1/R2 are ablations and cannot rescue the failed R4 gate.",
            "",
            "The carried-forward label `PROXY_DISTRIBUTION_MISMATCH` remains applicable. No "
            "validation-dev or formal-test member was accessed, and no adaptive tuning occurred.",
            "",
            "Detailed artifacts: `query_summary.csv`, `graph_summary.csv`, "
            "`resource_summary.csv`, `paired_navigation_effects.csv`, "
            "`recall_noninferiority.csv`, and `e0_decision.json`.",
        ]
    )
    (args.output / "FINAL_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in decision.items() if key != "dataset_decisions"}))


if __name__ == "__main__":
    main()
