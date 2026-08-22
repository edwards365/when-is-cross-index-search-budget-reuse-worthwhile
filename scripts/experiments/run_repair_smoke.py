#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.neighbors import NearestNeighbors

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))

from narhnsw.repair import rewire_directed_graph  # noqa: E402
from narhnsw.search import beam_search  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    fixture = REPO / config["fixture"]
    points = np.loadtxt(fixture / "points.csv", delimiter=",")
    edges = pd.read_csv(fixture / "edges.csv")
    adjacency = np.zeros((len(points), len(points)), dtype=bool)
    adjacency[edges.source.to_numpy(), edges.target.to_numpy()] = True
    metadata = dict(
        line.split("=", maxsplit=1)
        for line in (fixture / "metadata.txt").read_text(encoding="utf-8").splitlines()
    )
    entrypoint = int(metadata["entrypoint"])
    rng = np.random.default_rng(config["query_seed"])
    query_ids = rng.choice(len(points), size=config["queries"], replace=False)
    queries = points[query_ids] + rng.normal(
        0, config["query_noise"], size=(len(query_ids), points.shape[1])
    )
    ground_truth = (
        NearestNeighbors(n_neighbors=config["k"], algorithm="brute", n_jobs=1)
        .fit(points)
        .kneighbors(queries, return_distance=False)
    )
    rows: list[dict] = []
    build_rows: list[dict] = []
    for variant in config["variants"]:
        started = time.perf_counter()
        repaired, repair_metadata = rewire_directed_graph(
            points,
            adjacency,
            variant,
            seed=config["repair_seed"],
            max_candidates=config["max_candidates"],
        )
        build_rows.append(
            {
                **repair_metadata,
                "repair_seconds": time.perf_counter() - started,
                "directed_edges": int(repaired.sum()),
            }
        )
        for ef in config["ef_search"]:
            for query_id, query in enumerate(queries):
                labels, ndc, expanded = beam_search(
                    points, repaired, query, entrypoint, k=config["k"], ef=ef
                )
                recall = len(set(labels).intersection(ground_truth[query_id])) / config["k"]
                rows.append(
                    {
                        "variant": variant,
                        "ef_search": ef,
                        "query_id": query_id,
                        "recall_at_10": recall,
                        "ndc": ndc,
                        "expanded": expanded,
                    }
                )
    results = pd.DataFrame(rows)
    summary = (
        results.groupby(["variant", "ef_search"])
        .agg(
            recall_at_10=("recall_at_10", "mean"),
            mean_ndc=("ndc", "mean"),
            p95_ndc=("ndc", lambda values: values.quantile(0.95)),
            p99_ndc=("ndc", lambda values: values.quantile(0.99)),
        )
        .reset_index()
    )
    output = REPO / "results" / "processed"
    results.to_csv(output / "repair_smoke_queries.csv", index=False)
    summary.to_csv(output / "repair_smoke_summary.csv", index=False)
    pd.DataFrame(build_rows).to_csv(output / "repair_smoke_build.csv", index=False)
    print(pd.DataFrame(build_rows).to_string(index=False))
    print(summary.to_string(index=False))
    print(json.dumps({"fixture": str(fixture), "entrypoint": entrypoint}, indent=2))


if __name__ == "__main__":
    main()
