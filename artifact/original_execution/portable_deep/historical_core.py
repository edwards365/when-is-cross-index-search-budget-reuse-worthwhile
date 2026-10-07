"""Historical Deep numerical bodies; explicit calls only."""
import hashlib,time
import numpy as np
import hnswlib
from pathlib import Path
def normalize(values):
    values = np.asarray(values, dtype=np.float32)
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return np.ascontiguousarray(values / np.maximum(norms, np.finfo(np.float32).tiny))

def write_vecs(path, values, dtype):
    values = np.asarray(values, dtype=dtype)
    dim = np.full((values.shape[0], 1), values.shape[1], dtype="<i4")
    payload = np.concatenate([dim.view("<f4"), values], axis=1) if dtype == "<f4" else np.concatenate([dim, values], axis=1)
    payload.tofile(path)

def exact_truth(base, queries, k=10):
    best_scores = np.full((len(queries), k), -np.inf, dtype=np.float32)
    best_ids = np.full((len(queries), k), -1, dtype=np.int32)
    for start in range(0, len(base), 100000):
        block = normalize(base[start:start + 100000])
        for qs in range(0, len(queries), 100):
            q = queries[qs:qs + 100]
            scores = q @ block.T
            local = np.argpartition(scores, -k, axis=1)[:, -k:]
            local_scores = np.take_along_axis(scores, local, axis=1)
            ids = local.astype(np.int32) + start
            merged_scores = np.concatenate([best_scores[qs:qs + len(q)], local_scores], axis=1)
            merged_ids = np.concatenate([best_ids[qs:qs + len(q)], ids], axis=1)
            keep = np.argpartition(merged_scores, -k, axis=1)[:, -k:]
            best_scores[qs:qs + len(q)] = np.take_along_axis(merged_scores, keep, axis=1)
            best_ids[qs:qs + len(q)] = np.take_along_axis(merged_ids, keep, axis=1)
    order = np.argsort(-best_scores, axis=1)
    return np.take_along_axis(best_ids, order, axis=1)
def build_index(base: np.ndarray, seed: int, order_name: str, path: Path) -> float:
    if path.exists():
        return 0.0
    if order_name == "random":
        order = np.random.default_rng(seed).permutation(len(base))
    else:
        order = np.argsort(np.linalg.norm(base, axis=1), kind="stable")
    index = hnswlib.Index(space="cosine", dim=base.shape[1])
    index.init_index(max_elements=len(base), M=16, ef_construction=100, random_seed=seed)
    index.set_num_threads(1)
    t0 = time.time()
    for start in range(0, len(base), 100_000):
        ids = order[start:start + 100_000]
        index.add_items(base[ids], ids.astype(np.int64))
    elapsed = time.time() - t0
    index.save_index(str(path))
    return elapsed
