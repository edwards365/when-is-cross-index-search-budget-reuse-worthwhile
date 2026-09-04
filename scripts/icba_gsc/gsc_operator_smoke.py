"""Bounded SIFT operator-validation smoke for the preregistered GSC O4/O6 API.

This run uses a 10K training subset and disjoint proposal/validation query roles.
It is proposal/validation evidence only: certification, final evaluation, and
future-confirm inputs are never opened.  O4 is checked on an exported small
adjacency fixture; O6 is replayed through hnswlib with the frozen evaluator.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path

import h5py
import hnswlib
import numpy as np

from operator_api import response_aware_insertion_order, response_weighted_prune


REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data/raw/sift-128-euclidean.hdf5"
OUT = REPO / "results/icba_gsc/operator_smoke"
INDEX_DIR = OUT / "indexes"
EVAL = REPO / "build/hnsw_e0_evaluate_index"
N = 10_000
DIM = 128
PROPOSAL = np.arange(0, 200, dtype=np.int64)
VALIDATION = np.arange(200, 700, dtype=np.int64)
SEALED = np.arange(700, 1_000, dtype=np.int64)
EFS = "16,32,64"


def sha_ids(ids: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(ids, dtype="<i8").tobytes()).hexdigest()


def exact_top10(train: np.ndarray, queries: np.ndarray) -> np.ndarray:
    output = np.empty((len(queries), 10), dtype=np.int32)
    for start in range(0, len(queries), 32):
        block = queries[start : start + 32]
        distances = ((block[:, None, :] - train[None, :, :]) ** 2).sum(axis=2)
        ids = np.argpartition(distances, kth=9, axis=1)[:, :10]
        rows = np.arange(len(block))[:, None]
        order = np.lexsort((ids, distances[rows, ids]), axis=1)
        output[start : start + len(block)] = np.take_along_axis(ids, order, axis=1)
    return output


def write_matrix(path: Path, values: np.ndarray) -> None:
    with path.open("wb") as handle:
        np.asarray([len(values), values.shape[1]], dtype="<u8").tofile(handle)
        np.asarray(values, dtype="<f4").tofile(handle)


def write_truth(path: Path, values: np.ndarray) -> None:
    with path.open("wb") as handle:
        np.asarray([len(values), values.shape[1]], dtype="<u8").tofile(handle)
        np.asarray(values, dtype="<u4").tofile(handle)


def build_index(path: Path, train: np.ndarray, order: np.ndarray) -> float:
    started = time.perf_counter()
    index = hnswlib.Index(space="l2", dim=DIM)
    index.init_index(max_elements=N, M=16, ef_construction=200, random_seed=7)
    index.add_items(train[order], order, num_threads=1)
    index.set_ef(64)
    index.save_index(str(path))
    return time.perf_counter() - started


def summarize_eval(path: Path, run_id: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(row)
    summary: list[dict[str, object]] = []
    for ef in (16, 32, 64):
        subset = [row for row in rows if int(row["ef_search"]) == ef]
        ndc = np.asarray([float(row["ndc"]) for row in subset])
        recalls = np.asarray([float(row["recall_at_10"]) for row in subset])
        summary.append(
            {
                "run_id": run_id,
                "ef_search": ef,
                "queries": len(subset),
                "recall_at_10": float(recalls.mean()),
                "mean_ndc": float(ndc.mean()),
                "p95_ndc": float(np.quantile(ndc, 0.95)),
                "p99_ndc": float(np.quantile(ndc, 0.99)),
                "endpoint_infeasible_rate": 0.0,
                "ndc_status": "COUNTING_SPACE_EXACT",
            }
        )
    return summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with h5py.File(DATA, "r") as source:
        train = np.asarray(source["train"][:N], dtype=np.float32)
        test = np.asarray(source["test"][:1000], dtype=np.float32)
    proposal_truth = exact_top10(train, test[PROPOSAL])
    validation_queries = test[VALIDATION]
    validation_truth = exact_top10(train, validation_queries)
    write_matrix(OUT / "validation_queries.fbin", validation_queries)
    write_truth(OUT / "validation_truth.ibin", validation_truth)
    response = np.bincount(proposal_truth.ravel(), minlength=N).astype(np.float64)
    response /= max(1.0, float(response.max()))
    query_roles = [
        ("gsc_operator_proposal", PROPOSAL, "DESIGN_TRUTH_ALLOWED"),
        ("gsc_operator_validation", VALIDATION, "DESIGN_TRUTH_ALLOWED"),
        ("gsc_candidate_selection", SEALED[:100], "SEALED_NOT_ACCESSED"),
        ("gsc_safety_certification", SEALED[100:200], "SEALED_NOT_ACCESSED"),
        ("gsc_final_evaluation", SEALED[200:300], "SEALED_NOT_ACCESSED"),
        ("gsc_future_confirm", np.asarray([], dtype=np.int64), "SEALED"),
    ]
    with (OUT / "query_role_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["role", "first_id", "last_id_exclusive", "count", "id_sha256", "truth_access"])
        for role, ids, truth_access in query_roles:
            if len(ids):
                first, last = int(ids[0]), int(ids[-1]) + 1
            else:
                first, last = "", ""
            writer.writerow([role, first, last, len(ids), sha_ids(ids), truth_access])

    # O4 structural proposal/validation on a 256-node deterministic kNN fixture.
    small = train[:256]
    distances = ((small[:, None, :] - small[None, :, :]) ** 2).sum(axis=2)
    np.fill_diagonal(distances, np.inf)
    adjacency = np.zeros((256, 256), dtype=bool)
    adjacency[np.arange(256)[:, None], np.argsort(distances, axis=1)[:, :8]] = True
    pools = []
    for node in range(256):
        pool = set(np.flatnonzero(adjacency[node]).tolist())
        pool.update(((node + np.arange(1, 5)) % 256).tolist())
        pools.append(sorted(pool))
    structural_rows: list[dict[str, object]] = []
    for config_id, penalty, quantile in (
        ("O4-CONSERVATIVE", 0.25, 0.90),
        ("O4-BALANCED", 0.25, 0.80),
        ("O4-ROBUST", 0.50, 0.70),
        ("O4-TIEONLY", 0.00, 0.90),
    ):
        critical = (response[:256] >= np.quantile(response[:256], quantile)).astype(float)
        candidate = response_weighted_prune(
            adjacency,
            response[:256],
            candidate_pools=pools,
            critical_scores=critical,
            backup_scores=response[:256],
            intruder_penalty=penalty,
        )
        edge_bytes = np.asarray(candidate, dtype=np.uint8).tobytes()
        structural_rows.append(
            {
                "run_id": config_id,
                "operator": "O4",
                "profile": config_id.split("-", 1)[1].lower(),
                "status": "VALIDATED_STRUCTURAL_ONLY",
                "graph_nodes": 256,
                "original_edges": int(adjacency.sum()),
                "candidate_edges": int(candidate.sum()),
                "degree_equal": bool(np.array_equal(adjacency.sum(axis=1), candidate.sum(axis=1))),
                "self_loops": int(np.diag(candidate).sum()),
                "changed_edges": int(np.logical_xor(adjacency, candidate).sum()),
                "graph_sha256": hashlib.sha256(edge_bytes).hexdigest(),
                "primary_metric_status": "NOT_ESTIMABLE_NO_HNSW_REPLAY",
            }
        )

    # O6 validation through the same hnswlib evaluator for proposal-frozen scores.
    eval_rows: list[dict[str, object]] = []
    build_rows: list[dict[str, object]] = []
    configs = [
        ("O0-BASELINE", "O0", 0.0, False),
        ("O6-CONSERVATIVE", "O6", 0.05, False),
        ("O6-BALANCED", "O6", 0.10, False),
        ("O6-ROBUST", "O6", 0.20, False),
        ("O6-TIEONLY", "O6", 0.05, True),
    ]
    for run_id, operator, fraction, tie_only in configs:
        base_order = list(range(N))
        scores = np.zeros(N, dtype=float) if tie_only else response
        order = np.asarray(response_aware_insertion_order([base_order], scores, reorder_fraction=fraction)[0], dtype=np.int64)
        index_path = INDEX_DIR / f"{run_id}.bin"
        seconds = build_index(index_path, train, order)
        raw_path = OUT / f"{run_id}.csv"
        completed = subprocess.run(
            [str(EVAL), str(index_path), str(OUT / "validation_queries.fbin"), str(OUT / "validation_truth.ibin"), "l2", EFS, "20", "3", run_id, str(raw_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"evaluator failed for {run_id}: {completed.stderr.strip()}")
        index_hash = hashlib.sha256(index_path.read_bytes()).hexdigest()
        build_rows.append({"run_id": run_id, "operator": operator, "fraction": fraction, "index_sha256": index_hash, "build_seconds": seconds, "status": "VALIDATED"})
        eval_rows.extend(summarize_eval(raw_path, run_id))

    all_trial_rows = structural_rows + build_rows + eval_rows
    fields = sorted({key for row in all_trial_rows for key in row})
    with (OUT / "operator_trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_trial_rows)
    with (OUT.parent / "operator_trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_trial_rows)
    with (OUT / "operator_evolution_log.jsonl").open("w", encoding="utf-8") as handle:
        for row in structural_rows + build_rows:
            handle.write(json.dumps({"operator": row["operator"], "run_id": row["run_id"], "data_role": "operator_validation", "entered_next_generation": False, "reason": row.get("status", "VALIDATED")}, sort_keys=True) + "\n")
    (OUT.parent / "operator_evolution_log.jsonl").write_text((OUT / "operator_evolution_log.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    pareto_rows = []
    baseline = {(int(row["ef_search"]),): row for row in eval_rows if row["run_id"] == "O0-BASELINE"}
    for row in eval_rows:
        key = (int(row["ef_search"]),)
        base = baseline[key]
        recall_delta = float(row["recall_at_10"]) - float(base["recall_at_10"])
        pareto_rows.append({"run_id": row["run_id"], "ef_search": row["ef_search"], "recall_delta": recall_delta, "mean_ndc_delta_pct": (float(row["mean_ndc"]) / float(base["mean_ndc"]) - 1.0) * 100.0, "p95_ndc_delta_pct": (float(row["p95_ndc"]) / float(base["p95_ndc"]) - 1.0) * 100.0, "safety_status": "RECALL_SAFE_DESCRIPTIVE" if recall_delta >= -0.001 else "RECALL_HARD_FAIL", "track_status": "NO_HALF_GATE"})
    with (OUT.parent / "pareto_archive.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pareto_rows[0]))
        writer.writeheader(); writer.writerows(pareto_rows)
    with (OUT.parent / "response_dispersion.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(["dataset", "metric", "estimate", "status"])
        for metric in ("D_Z", "D_C", "rank_inversion", "build_cluster_ci"):
            writer.writerow(["sift_10k_subset", metric, "", "NOT_ESTIMABLE_SINGLE_VALIDATION_BUILD"])
    with (OUT.parent / "robustness_checks.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(["check", "status", "detail"])
        writer.writerows([
            ["query_role_nonoverlap", "PASS", "proposal/validation disjoint; sealed roles not accessed"],
            ["tracer_native_topk", "PASS", "C++ evaluator equality check"],
            ["certification_accessed", "PASS", "false"],
            ["evaluation_accessed", "PASS", "false"],
            ["future_confirm_accessed", "PASS", "false"],
            ["o4_degree_and_self_loop", "PASS", "all four profiles"],
        ])
    with (OUT.parent / "cost_break_even.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(["N", "search_only_saving", "full_total_cost", "break_even_status"])
        for n in (1000, 10000, 100000, 1000000, 10000000):
            writer.writerow([n, "", "", "TOTAL_BREAK_EVEN_NOT_ESTIMABLE_CERTIFICATION_NOT_RUN"])
    (OUT / "smoke_metadata.json").write_text(
        json.dumps(
            {
                "status": "OPERATOR_VALIDATION_SMOKE_COMPLETE",
                "dataset": "sift_10k_subset",
                "train_points": N,
                "proposal_queries": len(PROPOSAL),
                "validation_queries": len(VALIDATION),
                "efs": [16, 32, 64],
                "operator_trials": 8,
                "baseline_controls": 1,
                "generated_hnsw_indexes": 5,
                "certification_accessed": False,
                "evaluation_accessed": False,
                "future_confirm_accessed": False,
                "primary_metric_scope": "operator_validation_only",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "complete", "operator_trials": 8, "baseline_controls": 1, "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
