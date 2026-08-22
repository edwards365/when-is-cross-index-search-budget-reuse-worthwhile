#!/usr/bin/env python
"""Derive proposed treatment-strength metrics from a Gate 0 raw audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


def edge_sets(frame: pd.DataFrame, column: str) -> set[tuple[int, int]]:
    edges = set()
    for row in frame.itertuples(index=False):
        for target in json.loads(getattr(row, column)):
            edges.add((int(row.center), int(target)))
    return edges


def graph_metrics(edges: set[tuple[int, int]]) -> dict[str, float | int]:
    nodes = sorted({node for edge in edges for node in edge})
    position = {node: offset for offset, node in enumerate(nodes)}
    rows = [position[source] for source, _ in edges]
    columns = [position[target] for _, target in edges]
    adjacency = csr_matrix(
        (np.ones(len(edges), dtype=np.int8), (rows, columns)), shape=(len(nodes), len(nodes))
    )
    _, weak_labels = connected_components(adjacency, directed=True, connection="weak")
    _, strong_labels = connected_components(adjacency, directed=True, connection="strong")
    indegree = np.asarray(adjacency.sum(axis=0)).ravel()
    reciprocal = sum((target, source) in edges for source, target in edges) / len(edges)
    undirected = adjacency.maximum(adjacency.T).astype(bool)
    clustering = []
    for node in range(len(nodes)):
        neighbors = undirected[node].indices
        if len(neighbors) < 2:
            clustering.append(0.0)
            continue
        links = undirected[np.ix_(neighbors, neighbors)].nnz / 2
        clustering.append(links / (len(neighbors) * (len(neighbors) - 1) / 2))
    return {
        "nodes_in_partial_graph": len(nodes),
        "weak_components_partial": int(len(np.unique(weak_labels))),
        "strong_components_partial": int(len(np.unique(strong_labels))),
        "reciprocal_rate_partial": reciprocal,
        "mean_indegree_partial": float(indegree.mean()),
        "p99_indegree_partial": float(np.quantile(indegree, 0.99)),
        "max_indegree_partial": int(indegree.max(initial=0)),
        "indegree_std_partial": float(indegree.std()),
        "mean_local_clustering_partial": float(np.mean(clustering)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("derived output exists and will not be overwritten")
    centers = pd.read_csv(args.raw / "per_center.csv")
    swaps = pd.read_csv(args.raw / "per_swap.csv")
    centers = centers[centers.geometry_tolerance == 0.0]
    swaps = swaps[swaps.geometry_tolerance == 0.0]
    rows = []
    for dataset, group in centers.groupby("dataset"):
        baseline = edge_sets(group, "geometry_selected_targets")
        final = edge_sets(group, "final_selected_targets")
        baseline_support = {tuple(sorted(edge)) for edge in baseline}
        final_support = {tuple(sorted(edge)) for edge in final}
        changes = baseline.symmetric_difference(final)
        geometry_delta = group.geometry_delta.to_numpy()
        leverage_delta = group.leverage_delta.to_numpy()
        dataset_swaps = swaps[swaps.dataset == dataset]
        row = {
            "dataset": dataset,
            "audited_sources": len(group),
            "changed_sources": int((group.swaps > 0).sum()),
            "changed_source_fraction": float((group.swaps > 0).mean()),
            "proposed_swaps": int(group.swaps.sum()),
            "net_changed_directed_edges": len(changes),
            "directed_edge_jaccard": len(baseline & final) / len(baseline | final),
            "undirected_support_jaccard": len(baseline_support & final_support)
            / len(baseline_support | final_support),
            "geometry_delta_total": float(geometry_delta.sum()),
            "geometry_delta_p00": float(np.quantile(geometry_delta, 0.0)),
            "geometry_delta_p50": float(np.quantile(geometry_delta, 0.5)),
            "geometry_delta_p95": float(np.quantile(geometry_delta, 0.95)),
            "geometry_delta_p100": float(np.quantile(geometry_delta, 1.0)),
            "leverage_delta_total": float(leverage_delta.sum()),
            "leverage_delta_p50": float(np.quantile(leverage_delta, 0.5)),
            "leverage_delta_p95": float(np.quantile(leverage_delta, 0.95)),
            "leverage_delta_p100": float(np.quantile(leverage_delta, 1.0)),
            "layer0_swap_fraction": float((dataset_swaps.layer == 0).mean()),
            "actual_retained_swaps": None,
            "actual_retention_rate": None,
        }
        for prefix, edges in (("baseline", baseline), ("proposed", final)):
            row.update({f"{prefix}_{key}": value for key, value in graph_metrics(edges).items()})
        rows.append(row)
    args.output.mkdir(parents=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(args.output / "treatment_strength.csv", index=False)
    (args.output / "status.json").write_text(
        json.dumps(
            {
                "scope": "128-source proposed partial graphs; not final HNSW",
                "final_retention_available": False,
                "blocker": "GGR is not integrated before reciprocal insertion/reverse pruning",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
