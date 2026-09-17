#!/usr/bin/env python3
import argparse
import csv
import gzip
import json
import time
from pathlib import Path

import faiss
import numpy as np


GRIDS = {"sift_100k": [16, 32, 64, 128, 256, 512], "arxiv_nomic_100k": [16, 32, 64, 128, 256, 512]}


def per_query_ndc():
    """Return Faiss HNSW distance computations for the frozen runtime.

    Faiss 1.8.0 combines the search accumulator as
    ``HNSWStats(n1, n2, ndis, nhops)`` while the legacy struct layout is
    ``n1, n2, n3, ndis, nreorder``.  Consequently the distance-computation
    counter is exposed as ``n3`` in this exact runtime.  Newer releases use
    the named ``ndis`` field directly.  Prefer the field that is positive and
    fail closed if neither counter is populated.
    """
    stats = faiss.cvar.hnsw_stats
    legacy = int(stats.n3)
    current = int(stats.ndis)
    if legacy > 0 and current == 0:
        return legacy
    if current > 0:
        return current
    raise RuntimeError("Faiss HNSW distance counter is unavailable")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    doc = json.loads(args.manifest.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    faiss.omp_set_num_threads(1)
    for entry in doc["faiss_indexes"]:
        dataset, build = entry["dataset"], entry["build_id"]
        out_path = args.output / f"{build}.csv.gz"
        if out_path.exists():
            continue
        queries = np.load(args.inputs / f"{dataset}.queries.npy").astype(np.float32, copy=False)
        truth = np.load(args.inputs / f"{dataset}.truth.npy")
        index = faiss.read_index(entry["path"])
        core = faiss.downcast_index(index.index) if hasattr(index, "index") else faiss.downcast_index(index)
        rows = []
        for ef in GRIDS[dataset]:
            core.hnsw.efSearch = ef
            for qid, query in enumerate(queries):
                faiss.cvar.hnsw_stats.reset()
                start = time.perf_counter_ns()
                _, labels = index.search(query.reshape(1, -1), 10)
                wall = time.perf_counter_ns() - start
                ndc = per_query_ndc()
                found = labels[0].astype(int)
                hits = len(set(map(int, found)) & set(map(int, truth[qid])))
                rows.append(
                    {
                        "build": build,
                        "query_id": qid,
                        "ef": ef,
                        "recall": hits / 10.0,
                        "ndc": ndc,
                        "wall_ns": wall,
                        "topk": ";".join(map(str, found)),
                    }
                )
        with gzip.open(out_path, "wt", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
        print(json.dumps({"status": "complete", "build": build, "rows": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
