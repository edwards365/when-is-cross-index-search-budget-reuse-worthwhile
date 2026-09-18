#!/usr/bin/env python3
"""Independently replay one frozen S3 Faiss build and compare native outputs."""

import argparse
import csv
import gzip
import hashlib
import json
import random
import sys
from pathlib import Path

import faiss
import numpy as np


GRID = [16, 32, 64, 128, 256, 512]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stable_seed(build, query_id):
    payload = f"991|{build}|{query_id}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")


def ndc():
    stats = faiss.cvar.hnsw_stats
    legacy, current = int(stats.n3), int(stats.ndis)
    if legacy > 0 and current == 0:
        return legacy
    if current > 0:
        return current
    raise RuntimeError("Faiss HNSW distance counter unavailable")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--dataset", default="sift_100k")
    parser.add_argument("--build", default="sift_100k__100k__clean00__seed3101")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entry = next(
        row for row in manifest["faiss_indexes"]
        if row["dataset"] == args.dataset and row["build_id"] == args.build
    )
    index_path = Path(entry["path"])
    query_path = args.inputs / f"{args.dataset}.queries.npy"
    truth_path = args.inputs / f"{args.dataset}.truth.npy"
    raw_path = args.raw / f"{args.build}.csv.gz"

    with gzip.open(raw_path, "rt", encoding="utf-8", newline="") as handle:
        expected = {
            (int(row["query_id"]), int(row["ef"])): row
            for row in csv.DictReader(handle)
        }
    queries = np.load(query_path).astype(np.float32, copy=False)
    truth = np.load(truth_path)
    index = faiss.read_index(str(index_path))
    core = faiss.downcast_index(index.index) if hasattr(index, "index") else faiss.downcast_index(index)
    faiss.omp_set_num_threads(1)
    for ef in GRID:
        core.hnsw.efSearch = ef
        for query in queries[:20]:
            index.search(query.reshape(1, -1), 10)

    mismatches = {"action_order": 0, "topk": 0, "recall": 0, "ndc": 0}
    examples = []
    checked = 0
    for query_id, query in enumerate(queries):
        actions = list(GRID)
        random.Random(stable_seed(args.build, query_id)).shuffle(actions)
        for order, ef in enumerate(actions):
            row = expected[(query_id, ef)]
            core.hnsw.efSearch = ef
            faiss.cvar.hnsw_stats.reset()
            _, labels = index.search(query.reshape(1, -1), 10)
            found = labels[0].astype(int)
            hits = len(set(map(int, found)) & set(map(int, truth[query_id])))
            observed = {
                "action_order": order,
                "topk": ";".join(map(str, found)),
                "recall": hits / 10.0,
                "ndc": ndc(),
            }
            checks = {
                "action_order": int(row["action_order"]) == observed["action_order"],
                "topk": row["topk"] == observed["topk"],
                "recall": float(row["recall"]) == observed["recall"],
                "ndc": int(row["ndc"]) == observed["ndc"],
            }
            for key, ok in checks.items():
                mismatches[key] += int(not ok)
            if not all(checks.values()) and len(examples) < 10:
                examples.append({"query_id": query_id, "ef": ef, "failed_fields": [k for k, v in checks.items() if not v]})
            checked += 1

    result = {
        "status": "PASS" if sum(mismatches.values()) == 0 else "FAIL",
        "scope": "one preregistered SIFT target build; all 1,000 target-role queries and six actions",
        "build": args.build,
        "rows_checked": checked,
        "fields_checked_per_row": ["action_order", "topk", "recall", "ndc"],
        "wall_clock_compared": False,
        "mismatches": mismatches,
        "first_mismatch_examples": examples,
        "environment": {
            "python": ".".join(map(str, sys.version_info[:3])),
            "faiss": getattr(faiss, "__version__", "1.8.0"),
            "numpy": np.__version__,
            "omp_threads": 1,
        },
        "sha256": {
            "index": digest(index_path),
            "queries": digest(query_path),
            "truth": digest(truth_path),
            "frozen_response": digest(raw_path),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
