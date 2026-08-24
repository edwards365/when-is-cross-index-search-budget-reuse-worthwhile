#!/usr/bin/env python3
"""Generate frozen greedy set-cover D0-F directed-edge add-back rankings."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import heapq
import json
import math
from pathlib import Path
from typing import Any

import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def edges(path: Path) -> set[tuple[int, int]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        return {(int(row["source"]), int(row["target"])) for row in csv.DictReader(stream)}


def coverage(path: Path) -> tuple[dict[tuple[int, int], set[tuple[int, int]]], set[tuple[int, int]]]:
    edge_queries: dict[tuple[int, int], set[tuple[int, int]]] = {}
    queries: set[tuple[int, int]] = set()
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            edge = (int(row["source_internal"]), int(row["target_internal"]))
            query = (int(row["ef_search"]), int(row["query_id"]))
            edge_queries.setdefault(edge, set()).add(query)
            queries.add(query)
    return edge_queries, queries


def greedy_ranking(
    deleted: set[tuple[int, int]],
    edge_queries: dict[tuple[int, int], set[tuple[int, int]]],
    universe: set[tuple[int, int]],
) -> list[tuple[tuple[int, int], int, int]]:
    if not set(edge_queries) <= deleted:
        raise ValueError("trace coverage contains an edge not in Original-minus-Primary")
    query_edges: dict[tuple[int, int], set[tuple[int, int]]] = {query: set() for query in universe}
    for edge, queries in edge_queries.items():
        for query in queries:
            query_edges[query].add(edge)
    uncovered = set(universe)
    heap = [(-len(edge_queries.get(edge, set())), edge) for edge in deleted]
    heapq.heapify(heap)
    selected: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], int, int]] = []
    while uncovered:
        while heap:
            negative, edge = heapq.heappop(heap)
            if edge in selected:
                continue
            current = len(edge_queries.get(edge, set()) & uncovered)
            if -negative != current:
                heapq.heappush(heap, (-current, edge))
                continue
            break
        else:
            raise RuntimeError("greedy set cover cannot cover every harmed query-ef")
        if current <= 0:
            raise RuntimeError("uncovered harmed query has no Original-only trace edge")
        selected.add(edge)
        newly = edge_queries.get(edge, set()) & uncovered
        result.append((edge, current, len(newly)))
        uncovered -= newly
        affected = set()
        for query in newly:
            affected.update(query_edges[query])
        for affected_edge in affected - selected:
            heapq.heappush(
                heap, (-len(edge_queries.get(affected_edge, set()) & uncovered), affected_edge)
            )
    remaining = sorted(
        deleted - selected,
        key=lambda edge: (-len(edge_queries.get(edge, set())), edge[0], edge[1]),
    )
    result.extend((edge, len(edge_queries.get(edge, set())), 0) for edge in remaining)
    if len(result) != len(deleted) or len({edge for edge, _, _ in result}) != len(deleted):
        raise AssertionError("add-back ranking is not a permutation of deleted edges")
    return result


def fraction_name(value: float) -> str:
    return str(value).replace(".", "p")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--protocol", type=Path, default=Path("preregistration/post_e0_d0_dfg.yaml")
    )
    parser.add_argument("--e0", type=Path, default=Path("results/gb_mpcc/e0"))
    parser.add_argument("--coverage", type=Path, default=Path("results/post_e0/d0d_coverage"))
    parser.add_argument("--output", type=Path, default=Path("results/post_e0/d0f_plans"))
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if protocol["firewall"]["formal_test_access"] != "forbidden":
        raise PermissionError("D0-F firewall open")
    matrix = json.loads((args.coverage / "matrix_summary.json").read_text(encoding="utf-8"))
    if (
        matrix["status"] != "D0D_TRACE_MATRIX_COMPLETE"
        or not matrix["all_reconstructions_exact_e0"]
        or not matrix["all_temporary_indexes_deleted"]
    ):
        raise ValueError("D0-F coverage matrix incomplete")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.mkdir(parents=True)
    fractions = [float(value) for value in protocol["d0f_oracle_addback"][
        "budgets_as_fraction_of_replaced_original_edges"
    ]]
    summaries: list[dict[str, Any]] = []
    for dataset in protocol["matrix"]["datasets"]:
        for seed in protocol["matrix"]["build_seeds"]:
            run_id = f"{dataset}-b{seed}"
            original = edges(
                args.e0 / "runs" / run_id / "original_algorithm4" / "layer0_edges.csv.gz"
            )
            primary = edges(
                args.e0
                / "runs"
                / run_id
                / "geometry_backbone_mpcc_R4"
                / "layer0_edges.csv.gz"
            )
            deleted = original - primary
            edge_queries, query_universe = coverage(
                args.coverage / "runs" / run_id / "original_only_trace_edges.csv.gz"
            )
            ranking = greedy_ranking(deleted, edge_queries, query_universe)
            directory = args.output / run_id
            directory.mkdir()
            ranking_path = directory / "addback_ranking.csv"
            with ranking_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(
                    ["rank", "source", "target", "criticality_at_selection", "total_criticality"]
                )
                for rank, (edge, current, _) in enumerate(ranking, start=1):
                    writer.writerow([rank, edge[0], edge[1], current, len(edge_queries.get(edge, set()))])
            budgets = []
            for fraction in fractions:
                count = 0 if fraction == 0 else math.ceil(fraction * len(deleted))
                plan_path = directory / f"addback_{fraction_name(fraction)}.csv"
                with plan_path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.writer(stream)
                    writer.writerow(["source", "target"])
                    for edge, _, _ in ranking[:count]:
                        writer.writerow(edge)
                covered = set()
                for edge, _, _ in ranking[:count]:
                    covered.update(edge_queries.get(edge, set()))
                budgets.append(
                    {
                        "fraction": fraction,
                        "edges": count,
                        "covered_harmed_query_ef_pairs": len(covered),
                        "coverage_fraction": len(covered) / len(query_universe),
                        "plan": plan_path.as_posix(),
                        "plan_sha256": sha256(plan_path),
                    }
                )
            summary = {
                "run_id": run_id,
                "dataset": dataset,
                "build_seed": seed,
                "deleted_original_directed_edges": len(deleted),
                "harmed_query_ef_pairs": len(query_universe),
                "trace_covered_deleted_edges": len(edge_queries),
                "minimum_edges_for_full_trace_set_cover": next(
                    index
                    for index, (_, _, newly) in enumerate(ranking, start=1)
                    if newly == 0
                )
                - 1
                if any(newly == 0 for _, _, newly in ranking)
                else len(ranking),
                "ranking_sha256": sha256(ranking_path),
                "budgets": budgets,
                "oracle_query_supervision_diagnostic_only": True,
                "validation_dev_accessed": False,
                "formal_test_members_accessed": False,
            }
            (directory / "metadata.json").write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            summaries.append(summary)
            print(json.dumps({key: value for key, value in summary.items() if key != "budgets"}))
    matrix_summary = {
        "status": "D0F_ADDBACK_PLANS_COMPLETE",
        "runs": len(summaries),
        "budget_fractions": fractions,
        "oracle_query_supervision_diagnostic_only": True,
        "new_graphs_built": False,
        "validation_dev_accessed": False,
        "formal_test_members_accessed": False,
        "runs_detail": summaries,
    }
    (args.output / "matrix_summary.json").write_text(
        json.dumps(matrix_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
