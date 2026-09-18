#!/usr/bin/env python3
"""Replay the frozen S9-4 response cube on the paired S9-3 indexes."""

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import faiss
import numpy as np


GRID = [16, 32, 64, 128, 256, 512]
ROLE_OFFSETS = {
    "baseline_selection": (0, 500),
    "baseline_certification": (500, 1000),
    "baseline_evaluation": (1000, 1500),
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def core(index):
    return faiss.downcast_index(index.index)


def verify(prereg, root):
    if prereg["status"] != "FROZEN_BEFORE_QUERY_VECTOR_TRUTH_RESPONSE_POLICY_OR_RUNTIME_ACCESS":
        raise RuntimeError("preregistration status drift")
    for record in prereg["frozen_inputs"].values():
        if sha256(root / record["path"]) != record["sha256"]:
            raise RuntimeError(f"frozen input drift: {record['path']}")
    if GRID != prereg["native_grid"]:
        raise RuntimeError("native grid drift")
    module = Path(faiss.__file__).parent / "_swigfaiss_avx2.so"
    if not module.exists():
        matches = list(Path(faiss.__file__).parent.glob("_swigfaiss_avx2*.so"))
        if len(matches) != 1:
            raise RuntimeError("cannot resolve Faiss module")
        module = matches[0]
    if sha256(module) != prereg["runtime_environment"]["swigfaiss_avx2_sha256"]:
        raise RuntimeError("Faiss binary drift")
    faiss.omp_set_num_threads(1)


def evaluate(index, queries, truth, dataset, build_id, writer):
    graph = core(index)
    for role, (start, stop) in ROLE_OFFSETS.items():
        for action in GRID:
            graph.hnsw.efSearch = action
            for position in range(start, stop):
                faiss.cvar.hnsw_stats.reset()
                _, found = index.search(queries[position : position + 1], 10)
                recall = len(set(map(int, found[0])).intersection(map(int, truth[position]))) / 10.0
                writer.writerow({
                    "dataset": dataset,
                    "build_id": build_id,
                    "query_role": role,
                    "query_position": position - start,
                    "ef_search": action,
                    "recall_at_10": f"{recall:.1f}",
                    "failure": int(recall < 0.95),
                    "ndc": int(faiss.cvar.hnsw_stats.n3),
                    "top10_sha256": hashlib.sha256(found.astype(np.int64).tobytes()).hexdigest(),
                })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    verify(prereg, args.root)
    registry_path = args.root / prereg["frozen_inputs"]["s9_3_build_registry"]["path"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if len(registry) != 16:
        raise RuntimeError("expected 16 frozen indexes")
    args.output.mkdir(parents=True, exist_ok=True)
    fields = ["dataset", "build_id", "query_role", "query_position", "ef_search", "recall_at_10", "failure", "ndc", "top10_sha256"]
    replay = []
    for record in registry:
        dataset, build_id = record["dataset"], record["build_id"]
        index_path = Path(record["index_path"])
        if sha256(index_path) != record["index_sha256"]:
            raise RuntimeError(f"index hash drift: {build_id}")
        queries = np.load(args.root / "results/sigmod_s9/s9_4_inputs" / f"{dataset}.queries.npy")
        truth = np.load(args.root / "results/sigmod_s9/s9_4_inputs" / f"{dataset}.truth.npy")
        index = faiss.read_index(str(index_path))
        raw = args.output / "responses" / dataset / f"{build_id}.csv.gz"
        raw.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(raw, "wt", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            evaluate(index, queries, truth, dataset, build_id, writer)
        first, second = faiss.read_index(str(index_path)), faiss.read_index(str(index_path))
        top_equal, ndc_equal = True, True
        for action in GRID:
            core(first).hnsw.efSearch = action
            core(second).hnsw.efSearch = action
            faiss.cvar.hnsw_stats.reset(); _, left = first.search(queries[:20], 10); left_ndc = int(faiss.cvar.hnsw_stats.n3)
            faiss.cvar.hnsw_stats.reset(); _, right = second.search(queries[:20], 10); right_ndc = int(faiss.cvar.hnsw_stats.n3)
            top_equal &= np.array_equal(left, right)
            ndc_equal &= left_ndc == right_ndc
        replay.append({"dataset": dataset, "build_id": build_id, "top10_equal": bool(top_equal), "ndc_equal": bool(ndc_equal)})
        print(json.dumps({"complete": build_id, "rows": 9000}), flush=True)
    (args.output / "replay_equivalence.json").write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
    if not all(row["top10_equal"] and row["ndc_equal"] for row in replay):
        raise RuntimeError("native replay mismatch")


if __name__ == "__main__":
    main()
