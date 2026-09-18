#!/usr/bin/env python3
"""Replay the frozen S3 query roles with interleaved Faiss HNSW actions."""

import argparse
import csv
import gzip
import hashlib
import json
import os
import random
import time
from pathlib import Path

import faiss
import numpy as np


GRID = [16, 32, 64, 128, 256, 512]


def ndc():
    stats = faiss.cvar.hnsw_stats
    legacy, current = int(stats.n3), int(stats.ndis)
    if legacy > 0 and current == 0:
        return legacy
    if current > 0:
        return current
    raise RuntimeError("Faiss HNSW distance counter unavailable")


def stable_seed(build, query_id):
    payload = f"991|{build}|{query_id}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    faiss.omp_set_num_threads(1)
    for entry in manifest["faiss_indexes"]:
        dataset, build = entry["dataset"], entry["build_id"]
        output = args.output / f"{build}.csv.gz"
        if output.exists():
            continue
        queries = np.load(args.inputs / f"{dataset}.queries.npy").astype(np.float32, copy=False)
        truth = np.load(args.inputs / f"{dataset}.truth.npy")
        index = faiss.read_index(entry["path"])
        core = faiss.downcast_index(index.index) if hasattr(index, "index") else faiss.downcast_index(index)
        for ef in GRID:
            core.hnsw.efSearch = ef
            for query in queries[:20]:
                index.search(query.reshape(1, -1), 10)
        rows = []
        for query_id, query in enumerate(queries):
            actions = list(GRID)
            random.Random(stable_seed(build, query_id)).shuffle(actions)
            for order, ef in enumerate(actions):
                core.hnsw.efSearch = ef
                faiss.cvar.hnsw_stats.reset()
                start = time.perf_counter_ns()
                _, labels = index.search(query.reshape(1, -1), 10)
                elapsed = time.perf_counter_ns() - start
                found = labels[0].astype(int)
                hits = len(set(map(int, found)) & set(map(int, truth[query_id])))
                rows.append({
                    "build": build,
                    "query_id": query_id,
                    "role": "target_certification" if query_id < 500 else "target_evaluation",
                    "ef": ef,
                    "action_order": order,
                    "recall": hits / 10.0,
                    "ndc": ndc(),
                    "wall_ns": elapsed,
                    "topk": ";".join(map(str, found)),
                })
        with gzip.open(output, "wt", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(json.dumps({"status": "complete", "build": build, "rows": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
