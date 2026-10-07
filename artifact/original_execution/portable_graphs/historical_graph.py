"""Unchanged historical base read, insertion order, build and serialization body."""
import hashlib,json,os,time
from types import SimpleNamespace

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()

def construct(source,n,dim,keep,raw_ids,metric,seed,history,index_path,hnswlib,np,h5py):
    args=SimpleNamespace(seed=seed,history=history)
    spec={"metric":metric}
    record={}
    stem=index_path.stem
    vectors = np.empty((len(raw_ids), dim), dtype=np.float32)
    cursor = 0
    t0 = time.perf_counter_ns()
    with h5py.File(source, "r") as handle:
        train = handle["train"]
        if list(train.shape) != [n, dim] or str(train.dtype) != "float32":
            raise ValueError("Train shape/dtype")
        for start in range(0, n, 8192):
            end = min(start + 8192, n)
            chunk = np.asarray(train[start:end], dtype=np.float32)
            picked = chunk[keep[start:end]]
            vectors[cursor:cursor + len(picked)] = picked
            cursor += len(picked)
    if cursor != len(raw_ids):
        raise ValueError("Incomplete base read")
    record["train_read_ns"] = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    if args.history == "random":
        order = np.random.RandomState(args.seed).permutation(len(raw_ids))
    else:
        norms = np.empty(len(raw_ids), dtype=np.float64)
        for start in range(0, len(raw_ids), 8192):
            end = min(start + 8192, len(raw_ids))
            as64 = vectors[start:end].astype(np.float64)
            norms[start:end] = np.einsum("ij,ij->i", as64, as64)
        order = np.lexsort((raw_ids, norms))
    record["membership_and_order_ns"] = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    graph = hnswlib.Index(space=spec["metric"], dim=dim)
    graph.init_index(max_elements=len(raw_ids), M=16, ef_construction=100, random_seed=args.seed)
    graph.set_num_threads(1)
    record["graph_init_ns"] = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    for start in range(0, len(order), 8192):
        selected = order[start:start + 8192]
        graph.add_items(np.ascontiguousarray(vectors[selected]), raw_ids[selected], num_threads=1)
        if start == 0 or (start // 8192 + 1) % 20 == 0:
            print(json.dumps({"stem": stem, "inserted": min(start + 8192, len(order)),
                              "total": len(order)}), flush=True)
    record["graph_insert_ns"] = time.perf_counter_ns() - t0
    if graph.get_current_count() != len(raw_ids):
        raise ValueError("Incomplete graph")
    t0 = time.perf_counter_ns()
    graph.save_index(str(index_path))
    with index_path.open("rb") as stream:
        os.fsync(stream.fileno())
    record["serialize_fsync_ns"] = time.perf_counter_ns() - t0
    record["index_bytes"] = index_path.stat().st_size
    record["index_sha256"] = digest(index_path)
    record["effective_base_count"] = int(graph.get_current_count())
    record["index_path"] = str(index_path)
    record["status"] = "BUILT_NO_QUERY_OUTCOME_ACCESSED"
    return record
