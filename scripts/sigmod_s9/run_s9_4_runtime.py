#!/usr/bin/env python3
"""Measure all unique S9-4 deployable actions under paired fixed-machine timing."""

import argparse
import csv
import gzip
import hashlib
import json
import time
from pathlib import Path

import faiss
import numpy as np
import pandas as pd


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def core(index):
    return faiss.downcast_index(index.index)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    registry_record = prereg["frozen_inputs"]["s9_3_build_registry"]
    registry_path = args.root / registry_record["path"]
    if sha256(registry_path) != registry_record["sha256"]:
        raise RuntimeError("build registry drift")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    decisions = pd.read_csv(args.decisions)
    decisions = decisions[decisions.deployable.astype(str).str.lower().eq("true")]
    faiss.omp_set_num_threads(1)
    args.output.mkdir(parents=True, exist_ok=True)
    fields = ["dataset", "target_build", "query_position", "repetition", "ef_search", "wall_ns", "cpu_ns", "ndc", "top10_sha256"]
    for record in registry:
        dataset, build_id = record["dataset"], record["build_id"]
        index_path = Path(record["index_path"])
        if sha256(index_path) != record["index_sha256"]:
            raise RuntimeError(f"index hash drift: {build_id}")
        target = decisions[(decisions.dataset.eq(dataset)) & (decisions.target_build.eq(build_id))]
        actions = sorted(set(map(int, target.executed_action.dropna())).union({512}))
        queries = np.load(args.root / "results/sigmod_s9/s9_4_inputs" / f"{dataset}.queries.npy")[1000:1500]
        index = faiss.read_index(str(index_path)); graph = core(index)
        for action in actions:
            graph.hnsw.efSearch = action
            index.search(queries[: prereg["runtime_environment"]["warmup_queries_per_action"]], 10)
        raw = args.output / dataset / f"{build_id}.csv.gz"
        raw.parent.mkdir(parents=True, exist_ok=True)
        seed = 991 + int(record["permutation_seed"])
        rng = np.random.default_rng(seed)
        with gzip.open(raw, "wt", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
            for repetition in range(prereg["runtime_environment"]["repetitions_per_query_action"]):
                for query_position in rng.permutation(len(queries)):
                    for action in rng.permutation(actions):
                        graph.hnsw.efSearch = int(action)
                        faiss.cvar.hnsw_stats.reset()
                        cpu_start = time.process_time_ns(); wall_start = time.monotonic_ns()
                        _, found = index.search(queries[query_position : query_position + 1], 10)
                        wall_ns = time.monotonic_ns() - wall_start; cpu_ns = time.process_time_ns() - cpu_start
                        writer.writerow({
                            "dataset": dataset, "target_build": build_id, "query_position": int(query_position),
                            "repetition": repetition, "ef_search": int(action), "wall_ns": wall_ns, "cpu_ns": cpu_ns,
                            "ndc": int(faiss.cvar.hnsw_stats.n3),
                            "top10_sha256": hashlib.sha256(found.astype(np.int64).tobytes()).hexdigest(),
                        })
        print(json.dumps({"complete": build_id, "actions": actions, "rows": len(queries) * len(actions) * 7}), flush=True)


if __name__ == "__main__":
    main()
