#!/usr/bin/env python
"""Small exact mechanism check on a k-NN candidate graph."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.neighbors import NearestNeighbors

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))

from narhnsw.resistance import edge_leverage_scores, effective_resistance_matrix  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    with np.load(REPO / config["dataset"]) as data:
        points = data["base"][: config["sample_nodes"]]
    neighbors = NearestNeighbors(n_neighbors=config["knn"] + 1).fit(points)
    distances, indices = neighbors.kneighbors(points)
    adjacency = np.zeros((len(points), len(points)), dtype=bool)
    for node, row in enumerate(indices[:, 1:]):
        adjacency[node, row] = True
    if config["symmetrization"] == "union":
        adjacency |= adjacency.T
    elif config["symmetrization"] == "intersection":
        adjacency &= adjacency.T
    else:
        raise ValueError("symmetrization must be union or intersection")
    pair_distance = np.linalg.norm(points[:, None] - points[None, :], axis=2)
    rho = float(np.median(distances[:, 1:]))
    weights = adjacency * np.exp(-np.square(pair_distance / rho))
    resistance = effective_resistance_matrix(weights)
    leverage = edge_leverage_scores(weights, resistance)
    rows = []
    for u, v in zip(*np.triu_indices(len(points), k=1), strict=True):
        if weights[u, v] > 0:
            rows.append(
                {
                    "u": u,
                    "v": v,
                    "distance": pair_distance[u, v],
                    "weight": weights[u, v],
                    "resistance": resistance[u, v],
                    "leverage": leverage[u, v],
                }
            )
    frame = pd.DataFrame(rows)
    output = REPO / "results" / "processed" / "mechanism_edge_scores.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    summary = {
        "edges": len(frame),
        "rho": rho,
        "max_leverage": float(frame.leverage.max()),
        "min_leverage": float(frame.leverage.min()),
        "leverage_above_one_tolerance": int((frame.leverage > 1 + 1e-8).sum()),
        "output": str(output.relative_to(REPO)),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
