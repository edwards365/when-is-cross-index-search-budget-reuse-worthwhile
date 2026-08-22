"""HNSW baseline runner with query-level recall, latency, and run metadata."""

from __future__ import annotations

import json
import platform
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import hnswlib
import numpy as np
import pandas as pd


def git_commit(repo: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def recall_at_k(expected: np.ndarray, observed: np.ndarray) -> np.ndarray:
    if expected.shape != observed.shape:
        raise ValueError("ground truth and observed labels must have equal shape")
    k = expected.shape[1]
    return np.fromiter(
        (len(set(a).intersection(b)) / k for a, b in zip(expected, observed, strict=True)),
        dtype=np.float64,
        count=len(expected),
    )


def run_hnsw_sweep(
    base: np.ndarray,
    queries: np.ndarray,
    ground_truth: np.ndarray,
    *,
    ef_values: list[int],
    m: int,
    ef_construction: int,
    seed: int,
    warmup: int = 50,
) -> tuple[pd.DataFrame, dict]:
    index = hnswlib.Index(space="l2", dim=base.shape[1])
    started = time.perf_counter()
    index.init_index(max_elements=len(base), ef_construction=ef_construction, M=m, random_seed=seed)
    index.add_items(base, np.arange(len(base)), num_threads=1)
    build_seconds = time.perf_counter() - started
    rows: list[dict] = []
    query_ids = np.arange(len(queries))
    for ef in ef_values:
        index.set_ef(ef)
        index.knn_query(
            queries[: min(warmup, len(queries))], k=ground_truth.shape[1], num_threads=1
        )
        for query_id in query_ids:
            before = time.perf_counter_ns()
            labels, _ = index.knn_query(
                queries[query_id : query_id + 1], k=ground_truth.shape[1], num_threads=1
            )
            latency_ns = time.perf_counter_ns() - before
            recall = recall_at_k(ground_truth[query_id : query_id + 1], labels)[0]
            rows.append(
                {
                    "query_id": int(query_id),
                    "ef_search": ef,
                    "recall_at_10": recall,
                    "latency_ns": latency_ns,
                    "algorithm": "original_hnsw",
                    "seed": seed,
                }
            )
    metadata = {
        "run_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "build_seconds": build_seconds,
        "base_vectors": len(base),
        "query_vectors": len(queries),
        "dimension": base.shape[1],
        "m": m,
        "ef_construction": ef_construction,
        "seed": seed,
        "python": platform.python_version(),
        "hnswlib_version": getattr(hnswlib, "__version__", "0.8.0"),
        "status": "success",
    }
    return pd.DataFrame(rows), metadata


def save_run(results: pd.DataFrame, metadata: dict, output_dir: Path, repo: Path) -> Path:
    run_dir = output_dir / metadata["run_id"]
    run_dir.mkdir(parents=True, exist_ok=False)
    metadata = {**metadata, "git_commit": git_commit(repo)}
    results.to_csv(run_dir / "queries.csv", index=False)
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return run_dir
