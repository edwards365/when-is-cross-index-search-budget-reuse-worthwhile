from pathlib import Path
import hashlib
import numpy as np
# faiss is bound only after pinned native verification.
GRID=[16,32,64,128,256,512]
ROLE_OFFSETS={}

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
                    # Faiss 1.8.0 HNSW records base-layer distance work in n3;
                    # ndis is unused by this search path and remains zero.
                    "ndc": int(faiss.cvar.hnsw_stats.n3),
                    "top10_sha256": hashlib.sha256(found.astype(np.int64).tobytes()).hexdigest(),
                })
