#!/usr/bin/env python3
"""Build and replay the preregistered S9-3 prospective Faiss-HNSW units."""

import argparse
import csv
import gzip
import hashlib
import json
import os
import platform
import time
from pathlib import Path

import faiss
import numpy as np


DATASETS = {
    "sift_100k": "/home/wlk/data500/graph_anns_e4/inputs/sift_100k/base.f32bin",
    "arxiv_nomic_100k": "/home/wlk/data500/graph_anns_e4/inputs/arxiv_nomic_100k/base.f32bin",
}
GRID = [16, 32, 64, 128, 256, 512]
SEEDS = [6011, 6211, 6421, 6637, 6841, 7057, 7273, 7481]
ROLE_OFFSETS = {
    "source_design": (0, 500),
    "target_certification": (500, 1000),
    "target_evaluation": (1000, 1500),
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_f32bin(path):
    with Path(path).open("rb") as handle:
        n, d = np.fromfile(handle, np.int64, 2)
        values = np.fromfile(handle, np.float32)
    if values.size != int(n * d):
        raise RuntimeError(f"truncated f32bin: {path}")
    return values.reshape(int(n), int(d))


def core(index):
    return faiss.downcast_index(index.index)


def build_index(base, permutation):
    graph = faiss.IndexHNSWFlat(base.shape[1], 16, faiss.METRIC_L2)
    graph.hnsw.efConstruction = 100
    index = faiss.IndexIDMap2(graph)
    index.add_with_ids(base[permutation], permutation.astype(np.int64))
    return index


def build_id(dataset, ordinal, seed):
    return f"{dataset}__s9p3_{ordinal:02d}__seed{seed}"


def verify_environment(prereg):
    expected = prereg["runtime_environment"]
    if faiss.__version__ != expected["faiss_version"]:
        raise RuntimeError(f"Faiss drift: {faiss.__version__}")
    module = Path(faiss.__file__).parent / "_swigfaiss_avx2.so"
    if not module.exists():
        matches = list(Path(faiss.__file__).parent.glob("_swigfaiss_avx2*.so"))
        if len(matches) != 1:
            raise RuntimeError("cannot resolve _swigfaiss_avx2 module")
        module = matches[0]
    if sha256(module) != expected["swigfaiss_avx2_sha256"]:
        raise RuntimeError("Faiss binary hash drift")
    if GRID != prereg["policy"]["primary_grid"] or SEEDS != prereg["builds"]["insertion_permutation_seeds"]:
        raise RuntimeError("registered grid or build seeds drift")
    faiss.omp_set_num_threads(1)
    return module


def build_units(root, output, prereg, limit):
    registry = []
    indexes = output / "indexes"
    indexes.mkdir(parents=True, exist_ok=True)
    for dataset in prereg["datasets"]:
        base_path = Path(DATASETS[dataset])
        base = load_f32bin(base_path)
        if base.shape[0] != 100000:
            raise RuntimeError("unexpected base cardinality")
        for ordinal, seed in enumerate(SEEDS[:limit]):
            identifier = build_id(dataset, ordinal, seed)
            path = indexes / dataset / f"{identifier}.faiss"
            path.parent.mkdir(parents=True, exist_ok=True)
            permutation = np.random.default_rng(seed).permutation(len(base)).astype(np.int64)
            started = time.monotonic()
            index = build_index(base, permutation)
            build_seconds = time.monotonic() - started
            faiss.write_index(index, str(path))
            replay = faiss.read_index(str(path))
            if replay.ntotal != len(base):
                raise RuntimeError("serialized index cardinality drift")
            registry.append({
                "dataset": dataset,
                "build_id": identifier,
                "permutation_seed": seed,
                "permutation_sha256": hashlib.sha256(permutation.tobytes()).hexdigest(),
                "base_path": str(base_path),
                "base_sha256": sha256(base_path),
                "index_path": str(path),
                "index_sha256": sha256(path),
                "index_bytes": path.stat().st_size,
                "build_seconds": build_seconds,
                "M": 16,
                "efConstruction": 100,
                "threads": 1,
            })
            print(json.dumps({"phase": "build", "complete": identifier, "seconds": build_seconds}), flush=True)
    registry_path = output / f"build_registry_limit{limit}.json"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return registry


def evaluate_unit(index, queries, truth, dataset, identifier, writer):
    graph = core(index)
    for role, (start, stop) in ROLE_OFFSETS.items():
        for action in GRID:
            graph.hnsw.efSearch = action
            for query_position in range(start, stop):
                faiss.cvar.hnsw_stats.reset()
                _, found = index.search(queries[query_position : query_position + 1], 10)
                recall = len(set(map(int, found[0])).intersection(map(int, truth[query_position]))) / 10.0
                writer.writerow({
                    "dataset": dataset,
                    "build_id": identifier,
                    "query_role": role,
                    "query_position": query_position - start,
                    "ef_search": action,
                    "recall_at_10": f"{recall:.1f}",
                    "failure": int(recall < 0.95),
                    "ndc": int(faiss.cvar.hnsw_stats.ndis),
                    "top10_sha256": hashlib.sha256(found.astype(np.int64).tobytes()).hexdigest(),
                })


def replay_units(root, output, prereg, limit):
    registry = json.loads((output / f"build_registry_limit{limit}.json").read_text(encoding="utf-8"))
    fields = ["dataset", "build_id", "query_role", "query_position", "ef_search", "recall_at_10", "failure", "ndc", "top10_sha256"]
    equivalence = []
    for record in registry:
        dataset = record["dataset"]
        identifier = record["build_id"]
        queries = np.load(root / "results/sigmod_s9/s9_3_inputs" / f"{dataset}.queries.npy")
        truth = np.load(root / "results/sigmod_s9/s9_3_inputs" / f"{dataset}.truth.npy")
        index = faiss.read_index(record["index_path"])
        raw = output / "responses" / dataset / f"{identifier}.csv.gz"
        raw.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(raw, "wt", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            evaluate_unit(index, queries, truth, dataset, identifier, writer)
        first = faiss.read_index(record["index_path"])
        second = faiss.read_index(record["index_path"])
        equal = True
        ndc_equal = True
        for action in GRID:
            core(first).hnsw.efSearch = action
            core(second).hnsw.efSearch = action
            faiss.cvar.hnsw_stats.reset()
            _, a = first.search(queries[:20], 10)
            a_ndc = int(faiss.cvar.hnsw_stats.ndis)
            faiss.cvar.hnsw_stats.reset()
            _, b = second.search(queries[:20], 10)
            b_ndc = int(faiss.cvar.hnsw_stats.ndis)
            equal &= np.array_equal(a, b)
            ndc_equal &= a_ndc == b_ndc
        equivalence.append({"dataset": dataset, "build_id": identifier, "top10_equal": bool(equal), "ndc_equal": bool(ndc_equal)})
        print(json.dumps({"phase": "replay", "complete": identifier, "rows": 1500 * len(GRID)}), flush=True)
    (output / f"replay_equivalence_limit{limit}.json").write_text(json.dumps(equivalence, indent=2) + "\n", encoding="utf-8")
    if not all(row["top10_equal"] and row["ndc_equal"] for row in equivalence):
        raise RuntimeError("native serialization replay mismatch")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["build", "replay"], required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, choices=range(1, 9), required=True)
    args = parser.parse_args()
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    module = verify_environment(prereg)
    args.output.mkdir(parents=True, exist_ok=True)
    environment = {
        "python": os.sys.executable,
        "python_version": platform.python_version(),
        "faiss_version": faiss.__version__,
        "faiss_module": str(module),
        "faiss_module_sha256": sha256(module),
        "compile_options": faiss.get_compile_options(),
        "threads": 1,
        "gpu_used": False,
    }
    (args.output / "environment.json").write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8")
    if args.phase == "build":
        build_units(args.root, args.output, prereg, args.limit)
    else:
        replay_units(args.root, args.output, prereg, args.limit)


if __name__ == "__main__":
    main()
