"""Historical exact truth computation; unchanged search and serialization body."""
import hashlib
import os
import json
import time

ROLE_NAMES=("source_design","target_selection","target_certification","target_evaluation")

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()

def acquire(train_source, n, dim, keep, raw_ids, fresh_roles, metric, output, stem, faiss, np, h5py):
    from types import SimpleNamespace
    args=SimpleNamespace(dataset=stem)
    source=train_source
    spec={"metric":metric}
    impl={"base_stream_rows":8192,"k":10}
    result={"roles":{}}
    exact = faiss.IndexFlatL2(dim) if spec["metric"] == "squared_l2" else faiss.IndexFlatIP(dim)
    t0 = time.perf_counter_ns()
    with h5py.File(source, "r") as handle:
        train = handle["train"]
        if list(train.shape) != [n, dim] or str(train.dtype) != "float32":
            raise ValueError("Train shape/dtype")
        for begin in range(0, n, impl["base_stream_rows"]):
            end = min(begin + impl["base_stream_rows"], n)
            block = np.ascontiguousarray(train[begin:end][keep[begin:end]], dtype=np.float32)
            if len(block):
                exact.add(block)
    result["exact_base_acquisition_ns"] = time.perf_counter_ns() - t0
    if exact.ntotal != len(raw_ids):
        raise ValueError("Incomplete exact base")
    with h5py.File(source, "r") as handle:
        train = handle["train"]
        for role in ROLE_NAMES:
            ids = fresh_roles[role]
            t0 = time.perf_counter_ns()
            queries = np.ascontiguousarray(train[ids.tolist()], dtype=np.float32)
            read_ns = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns()
            scores, positions = exact.search(queries, impl["k"])
            search_ns = time.perf_counter_ns() - t0
            if positions.shape != (len(ids), 10) or np.any(positions < 0) or np.any(positions >= len(raw_ids)):
                raise ValueError("Exact top-k positions")
            topk = raw_ids[positions]
            if np.any(topk == ids[:, None]) or np.any(np.sort(topk, axis=1)[:, 1:] == np.sort(topk, axis=1)[:, :-1]):
                raise ValueError("Exact top-k IDs")
            if not np.all(np.isfinite(scores)):
                raise ValueError("Nonfinite exact scores")
            if spec["metric"] == "squared_l2" and np.any(np.diff(scores, axis=1) < -1e-4):
                raise ValueError("L2 rank order")
            if spec["metric"] == "inner_product" and np.any(np.diff(scores, axis=1) > 1e-4):
                raise ValueError("IP rank order")
            path = output / (stem + "_" + role + ".npz")
            with path.open("xb") as stream:
                np.savez_compressed(stream, query_ids=ids, neighbor_raw_ids=topk,
                                    scores=scores)
                stream.flush()
                os.fsync(stream.fileno())
            result["roles"][role] = {"count": len(ids), "query_read_ns": read_ns,
                                     "exact_search_ns": search_ns, "output_path": str(path),
                                     "output_sha256": digest(path), "output_bytes": path.stat().st_size}
            print(json.dumps({"dataset": args.dataset, "role": role,
                              "count": len(ids), "exact_search_ns": search_ns}), flush=True)
    return result
