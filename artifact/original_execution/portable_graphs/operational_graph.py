"""Exact original whole-unit operational boundary; opt-in new measurement."""
import hashlib,json,os,time
from types import SimpleNamespace

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()

def construct(source,train_shape,all_query,excluded,expected_base_rows,metric,seed,history,index_path,receipt_path,failure_path,hnswlib,np,h5py,resource):
    args=SimpleNamespace(seed=seed,history=history)
    row={"train_shape":train_shape}
    spec={"metric":metric,"expected_base_rows":expected_base_rows}
    frozen_row={"effective_base_count":expected_base_rows}
    stem=index_path.stem
    record={"status":"RUNNING","historical_source_sha256":"e8f89456dd906365c79e9a09688c3f604ce93cd631891aa8ebfd01a779599ae9","declared_boundary":"original began through finally whole_unit_ns: membership mask, raw IDs, base read, order, init, insert, serialize/fsync, index hash and status; excludes prior role/source validation and final receipt write"}
    began = time.perf_counter_ns()
    try:
        n, dim = row["train_shape"]
        keep = np.ones(n, dtype=bool)
        keep[np.asarray(sorted(all_query), dtype=np.int64)] = False
        keep[excluded] = False
        raw_ids = np.flatnonzero(keep).astype(np.int64)
        if len(raw_ids) != spec["expected_base_rows"] or len(raw_ids) != frozen_row["effective_base_count"]:
            raise ValueError("New base row count")
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
    except BaseException as error:
        record["status"] = "FAILED_STOP_NEW_WORK"
        record["failure_type"] = type(error).__name__
        record["failure_message"] = str(error)[:1000]
        raise
    finally:
        record["whole_unit_ns"] = time.perf_counter_ns() - began
        record["process_maxrss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        path = receipt_path if record["status"] == "BUILT_NO_QUERY_OUTCOME_ACCESSED" else failure_path
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, sort_keys=True, allow_nan=False)
            stream.write("\n")
        print(json.dumps({"stem": stem, "status": record["status"], "receipt_sha256": digest(path)}), flush=True)
    return record
