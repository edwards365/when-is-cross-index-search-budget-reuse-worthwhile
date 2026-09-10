#!/usr/bin/env python3
"""Measure Phase-I profiling costs on the frozen cost-only query role."""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import os
import resource
import statistics
import struct
import sys
import time
from pathlib import Path

import hnswlib
import numpy as np
from scipy.stats import beta

REPO = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
SCRATCH = Path("/home/wlk/data500/graph_anns_iclr_phase1_scratch")
FAISS_SITE = Path("/home/wlk/data500/graph_anns_faiss_external_validity/python")
sys.path.append(str(FAISS_SITE))
import faiss  # noqa: E402

NS = (59, 121, 129, 256, 750)
THREADS = (1, 8)
REPS = 5
GRIDS = {
    "hnswlib": (10, 20, 40, 80, 120, 200),
    "faiss": (16, 32, 64, 128, 256, 512),
}
BASES = {
    "sift_100k": Path("/home/wlk/data500/graph_anns_e4/inputs/sift_100k/base.f32bin"),
    "arxiv_nomic_100k": Path("/home/wlk/data500/graph_anns_e4/inputs/arxiv_nomic_100k/base.f32bin"),
}
HNSW_INDEX = {
    "sift_100k": Path("/home/wlk/data500/graph_anns_e4/raw/sift_100k__seed83__random/index.bin"),
    "arxiv_nomic_100k": Path("/home/wlk/data500/graph_anns_e4/raw/arxiv_nomic_100k__seed83__random/index.bin"),
}
FAISS_INDEX = {
    "sift_100k": Path("/home/wlk/data500/graph_anns_faiss_external_validity/run/indexes/sift_100k/sift_100k__perm00__seed3101.faiss"),
    "arxiv_nomic_100k": Path("/home/wlk/data500/graph_anns_faiss_external_validity/run/indexes/arxiv_nomic_100k/arxiv_nomic_100k__perm00__seed3101.faiss"),
}


def f32bin(path: Path) -> np.ndarray:
    with path.open("rb") as handle:
        n, d = struct.unpack("<QQ", handle.read(16))
    return np.memmap(path, dtype="<f4", mode="r", offset=16, shape=(n, d))


def elapsed(call):
    before_cpu = time.process_time_ns()
    before = time.perf_counter_ns()
    value = call()
    return value, time.perf_counter_ns() - before, time.process_time_ns() - before_cpu


def row(dataset, implementation, threads, n, component, rep, wall_ns, cpu_ns, detail):
    return {
        "dataset": dataset,
        "implementation": implementation,
        "threads": threads,
        "n": n,
        "component": component,
        "rep": rep,
        "wall_seconds": wall_ns / 1e9,
        "cpu_seconds": cpu_ns / 1e9,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "cache_state": "resident_after_explicit_warmup",
        "detail": detail,
    }


def cert_control(n: int, m: int = 6):
    failures = np.zeros(m, dtype=np.int64)
    alpha = 0.05 / m
    ucbs = []
    for count in failures:
        ucbs.append(beta.ppf(1 - alpha, count + 1, n - count) if count < n else 1.0)
    selected = next((i for i, value in enumerate(ucbs) if value <= 0.05), None)
    payload = json.dumps({"n": n, "M": m, "ucb": ucbs, "selected": selected}, sort_keys=True)
    hashlib.sha256(payload.encode()).hexdigest()
    return payload


def profile_dataset(dataset: str) -> list[dict]:
    rows = []
    base = f32bin(BASES[dataset])
    queries = f32bin(SCRATCH / "profiling_roles" / f"{dataset}.f32bin")
    dim = base.shape[1]
    for threads in THREADS:
        faiss.omp_set_num_threads(threads)
        truth_scopes = (
            ("hnswlib_vamana_exact_truth", np.asarray(base), "100000-point frozen base"),
            ("faiss_exact_truth", np.asarray(base[:30000]), "30000-point frozen Faiss external-validity base"),
        )
        for truth_name, truth_base, truth_detail in truth_scopes:
            flat = faiss.IndexFlatL2(dim)
            flat.add(truth_base)
            flat.search(np.asarray(queries[:59]), 10)  # warm-up
            for n in NS:
                q = np.asarray(queries[:n])
                for rep in range(REPS):
                    _, wall, cpu = elapsed(lambda q=q, flat=flat: flat.search(q, 10))
                    rows.append(row(dataset, truth_name, threads, n, "C_truth", rep, wall, cpu, f"faiss.IndexFlatL2; {truth_detail}"))
            del flat
            gc.collect()
        for n in NS:
            cert_control(n)
            for rep in range(REPS):
                _, wall, cpu = elapsed(lambda n=n: cert_control(n))
                rows.append(row(dataset, "shared_control", threads, n, "C_cert", rep, wall, cpu, "Bonferroni-Clopper-Pearson M=6 plus selection and policy digest"))

        # hnswlib resident search and six-action family replay
        hi = hnswlib.Index(space="l2", dim=dim)
        hi.load_index(str(HNSW_INDEX[dataset]), max_elements=base.shape[0])
        hi.set_num_threads(threads)
        hi.set_ef(GRIDS["hnswlib"][-1]); hi.knn_query(np.asarray(queries[:59]), k=10)
        for n in NS:
            q = np.asarray(queries[:n])
            for action in GRIDS["hnswlib"]:
                hi.set_ef(action)
                for rep in range(REPS):
                    _, wall, cpu = elapsed(lambda q=q: hi.knn_query(q, k=10))
                    rows.append(row(dataset, "hnswlib", threads, n, "C_search", rep, wall, cpu, f"ef={action}"))
            def hfamily(q=q):
                for action in GRIDS["hnswlib"]:
                    hi.set_ef(action); hi.knn_query(q, k=10)
            hfamily()
            for rep in range(REPS):
                _, wall, cpu = elapsed(hfamily)
                rows.append(row(dataset, "hnswlib", threads, n, "C_family", rep, wall, cpu, "six registered ef actions; truth shared"))
        del hi; gc.collect()

        # Faiss resident search and six-action family replay
        fi = faiss.read_index(str(FAISS_INDEX[dataset]))
        core = faiss.downcast_index(fi.index)
        core.hnsw.efSearch = GRIDS["faiss"][-1]; fi.search(np.asarray(queries[:59]), 10)
        for n in NS:
            q = np.asarray(queries[:n])
            for action in GRIDS["faiss"]:
                core.hnsw.efSearch = action
                for rep in range(REPS):
                    _, wall, cpu = elapsed(lambda q=q: fi.search(q, 10))
                    rows.append(row(dataset, "faiss", threads, n, "C_search", rep, wall, cpu, f"ef={action}"))
            def ffamily(q=q):
                for action in GRIDS["faiss"]:
                    core.hnsw.efSearch = action; fi.search(q, 10)
            ffamily()
            for rep in range(REPS):
                _, wall, cpu = elapsed(ffamily)
                rows.append(row(dataset, "faiss", threads, n, "C_family", rep, wall, cpu, "six registered efSearch actions; truth shared"))
        del fi; gc.collect()

    # Cold index load and serialization integrity are separately timed five times.
    for implementation, path in (("hnswlib", HNSW_INDEX[dataset]), ("faiss", FAISS_INDEX[dataset])):
        for rep in range(REPS):
            if implementation == "hnswlib":
                def load():
                    idx = hnswlib.Index(space="l2", dim=dim); idx.load_index(str(path), max_elements=base.shape[0]); return idx
            else:
                def load(): return faiss.read_index(str(path))
            value, wall, cpu = elapsed(load)
            rows.append(row(dataset, implementation, 1, 0, "C_serialize_cold_load", rep, wall, cpu, f"bytes={path.stat().st_size}"))
            del value; gc.collect()
    return rows


def summarize(rows: list[dict]) -> list[dict]:
    groups = {}
    for r in rows:
        key = tuple(r[k] for k in ("dataset", "implementation", "threads", "n", "component", "detail"))
        groups.setdefault(key, []).append(float(r["wall_seconds"]))
    out=[]
    for key, values in sorted(groups.items()):
        out.append(dict(zip(("dataset", "implementation", "threads", "n", "component", "detail"), key)) | {
            "repetitions": len(values),
            "wall_mean_seconds": statistics.mean(values),
            "wall_median_seconds": statistics.median(values),
            "wall_p95_seconds": float(np.quantile(values, .95)),
        })
    return out


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer=csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--dataset", choices=sorted(BASES), required=True); args=parser.parse_args()
    rows=profile_dataset(args.dataset)
    raw=SCRATCH/"profiling_raw"/f"{args.dataset}.csv"
    summary=REPO/"results/graph_anns_iclr_phase1"/f"profiling_cost_{args.dataset}.csv"
    write_csv(raw,rows); write_csv(summary,summarize(rows))
    print(summary)


if __name__ == "__main__": main()
