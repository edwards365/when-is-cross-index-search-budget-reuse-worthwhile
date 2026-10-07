import numpy as np
def truth_e1a_source(roles_row, config, expected_base, heldout, excluded, source, chunk_rows, faiss, h5py):
    dim = int(roles_row["train_shape"][1])
    if config["metric"] == "squared_l2":
        index = faiss.IndexFlatL2(dim)
    elif config["metric"] == "inner_product_on_original_normalized_float32":
        index = faiss.IndexFlatIP(dim)
    else:
        raise ValueError("Unknown metric")
    raw_ids = np.empty(expected_base, dtype=np.int64)
    cursor = 0
    with h5py.File(source, "r") as handle:
        train = handle["train"]  # Do not access test, neighbors, or distances.
        if list(train.shape) != roles_row["train_shape"] or str(train.dtype) != "float32":
            raise ValueError("Train metadata mismatch")
        design_ids = np.asarray(roles_row["roles"]["source_design"], dtype=np.int64)
        if len(design_ids) != config["source_design_query_count"]:
            raise ValueError("Design count mismatch")
        queries = np.ascontiguousarray(train[design_ids.tolist()], dtype=np.float32)
        for begin in range(0, train.shape[0], chunk_rows):
            end = min(begin + chunk_rows, train.shape[0])
            ids = np.arange(begin, end, dtype=np.int64)
            keep = np.fromiter((int(i) not in heldout and int(i) not in excluded for i in ids), dtype=bool, count=len(ids))
            block = np.ascontiguousarray(train[begin:end][keep], dtype=np.float32)
            n = len(block)
            if n:
                index.add(block)
                raw_ids[cursor:cursor+n] = ids[keep]
                cursor += n
        if cursor != expected_base or index.ntotal != expected_base:
            raise ValueError("Incomplete exact base")
    faiss.omp_set_num_threads(16)
    scores, positions = index.search(queries, 10)
    if np.any(positions < 0) or np.any(positions >= expected_base):
        raise ValueError("Invalid Faiss positions")
    neighbors = raw_ids[positions]
    if np.any(neighbors == design_ids[:, None]):
        raise ValueError("Self-neighbor leakage")
    if np.any(np.sort(neighbors, axis=1)[:, 1:] == np.sort(neighbors, axis=1)[:, :-1]):
        raise ValueError("Duplicate neighbors")
    if not np.all(np.isfinite(scores)):
        raise ValueError("Nonfinite exact score")
    if config["metric"] == "squared_l2" and np.any(np.diff(scores, axis=1) < -1e-5):
        raise ValueError("L2 score order mismatch")
    if config["metric"].startswith("inner_product") and np.any(np.diff(scores, axis=1) > 1e-5):
        raise ValueError("IP score order mismatch")
    return dict(query_ids=design_ids,neighbor_raw_ids=neighbors,scores=scores)

def truth_e1a_selection(row, DATASETS, args, query_ids, heldout, excluded, source, faiss, h5py):
    dim = int(row["train_shape"][1])
    config = DATASETS[args.dataset]
    index = faiss.IndexFlatL2(dim) if config["metric"] == "l2" else faiss.IndexFlatIP(dim)
    base_ids = np.empty(config["base_count"], dtype=np.int64)
    cursor = 0
    order = np.argsort(query_ids)
    with h5py.File(source, "r") as handle:
        train = handle["train"]  # Formal-test datasets are never opened.
        if list(train.shape) != row["train_shape"] or str(train.dtype) != "float32":
            raise ValueError("Frozen train shape/dtype mismatch")
        sorted_queries = np.asarray(train[query_ids[order]], dtype=np.float32)
        queries = np.ascontiguousarray(sorted_queries[np.argsort(order)])
        for begin in range(0, train.shape[0], 8192):
            end = min(begin + 8192, train.shape[0])
            raw = np.arange(begin, end, dtype=np.int64)
            keep = np.fromiter((int(i) not in heldout and int(i) not in excluded for i in raw), dtype=bool, count=len(raw))
            block = np.ascontiguousarray(train[begin:end][keep], dtype=np.float32)
            if len(block):
                index.add(block)
                base_ids[cursor:cursor + len(block)] = raw[keep]
                cursor += len(block)
    if cursor != config["base_count"] or index.ntotal != cursor:
        raise ValueError("Effective base insertion incomplete")
    faiss.omp_set_num_threads(16)
    scores, positions = index.search(queries, 10)
    if positions.shape != (500, 10) or np.any(positions < 0) or np.any(positions >= cursor):
        raise ValueError("Invalid exact positions")
    neighbors = base_ids[positions]
    if np.any(neighbors == query_ids[:, None]) or np.any(np.sort(neighbors, axis=1)[:, 1:] == np.sort(neighbors, axis=1)[:, :-1]):
        raise ValueError("Self or duplicate exact neighbor")
    if not np.all(np.isfinite(scores)):
        raise ValueError("Nonfinite scores")
    if config["metric"] == "l2" and np.any(np.diff(scores, axis=1) < -1e-5):
        raise ValueError("L2 scores unsorted")
    if config["metric"] == "ip" and np.any(np.diff(scores, axis=1) > 1e-5):
        raise ValueError("IP scores unsorted")
    return dict(query_ids=query_ids,neighbor_raw_ids=neighbors,scores=scores)

def truth_e1a_certify(role, metric, base_count, ids, heldout, omitted, source, faiss, h5py):
    dim = int(role["train_shape"][1])
    index = faiss.IndexFlatL2(dim) if metric == "l2" else faiss.IndexFlatIP(dim)
    raw_ids = np.empty(base_count, dtype=np.int64)
    cursor = 0
    order = np.argsort(ids)
    with h5py.File(source, "r") as handle:
        train = handle["train"]  # Never access HDF5 test, neighbors, or distances.
        if list(train.shape) != role["train_shape"] or str(train.dtype) != "float32":
            raise ValueError("Train shape/dtype mismatch")
        sorted_queries = np.asarray(train[ids[order]], dtype=np.float32)
        queries = np.ascontiguousarray(sorted_queries[np.argsort(order)])
        for start_row in range(0, train.shape[0], 8192):
            end_row = min(start_row + 8192, train.shape[0])
            block_ids = np.arange(start_row, end_row, dtype=np.int64)
            keep = np.fromiter((int(i) not in heldout and int(i) not in omitted for i in block_ids), dtype=bool, count=len(block_ids))
            block = np.ascontiguousarray(train[start_row:end_row][keep], dtype=np.float32)
            if len(block):
                index.add(block)
                raw_ids[cursor:cursor + len(block)] = block_ids[keep]
                cursor += len(block)
    if cursor != base_count or index.ntotal != base_count:
        raise ValueError("Incomplete exact base")
    faiss.omp_set_num_threads(16)
    scores, positions = index.search(queries, 10)
    if positions.shape != (500, 10) or np.any(positions < 0) or np.any(positions >= base_count):
        raise ValueError("Exact search positions invalid")
    neighbors = raw_ids[positions]
    if np.any(neighbors == ids[:, None]) or np.any(np.sort(neighbors, axis=1)[:, 1:] == np.sort(neighbors, axis=1)[:, :-1]):
        raise ValueError("Self/duplicate neighbor")
    if not np.all(np.isfinite(scores)) or (metric == "l2" and np.any(np.diff(scores, axis=1) < -1e-5)) or (metric == "ip" and np.any(np.diff(scores, axis=1) > 1e-5)):
        raise ValueError("Exact score invalid or unsorted")
    return dict(query_ids=ids,neighbor_raw_ids=neighbors,scores=scores)

def truth_e1a_evaluate(role, metric, base_count, ids, heldout, omitted, source, faiss, h5py):
    dimension = int(role["train_shape"][1])
    index = faiss.IndexFlatL2(dimension) if metric == "l2" else faiss.IndexFlatIP(dimension)
    raw_ids = np.empty(base_count, dtype=np.int64)
    cursor = 0
    order = np.argsort(ids)
    with h5py.File(source, "r") as handle:
        train = handle["train"]  # Formal-test datasets are never opened.
        if list(train.shape) != role["train_shape"] or str(train.dtype) != "float32":
            raise ValueError("Train shape/dtype mismatch")
        sorted_queries = np.asarray(train[ids[order]], dtype=np.float32)
        queries = np.ascontiguousarray(sorted_queries[np.argsort(order)])
        for start_row in range(0, train.shape[0], 8192):
            end_row = min(start_row + 8192, train.shape[0])
            block_ids = np.arange(start_row, end_row, dtype=np.int64)
            keep = np.fromiter((int(i) not in heldout and int(i) not in omitted for i in block_ids), dtype=bool, count=len(block_ids))
            block = np.ascontiguousarray(train[start_row:end_row][keep], dtype=np.float32)
            if len(block):
                index.add(block)
                raw_ids[cursor:cursor + len(block)] = block_ids[keep]
                cursor += len(block)
    if cursor != base_count or index.ntotal != base_count:
        raise ValueError("Incomplete exact base")
    faiss.omp_set_num_threads(16)
    scores, positions = index.search(queries, 10)
    if positions.shape != (1000, 10) or np.any(positions < 0) or np.any(positions >= base_count):
        raise ValueError("Exact search positions invalid")
    neighbors = raw_ids[positions]
    if (np.any(neighbors == ids[:, None])
            or np.any(np.sort(neighbors, axis=1)[:, 1:] == np.sort(neighbors, axis=1)[:, :-1])
            or not np.all(np.isfinite(scores))
            or (metric == "l2" and np.any(np.diff(scores, axis=1) < -1e-5))
            or (metric == "ip" and np.any(np.diff(scores, axis=1) > 1e-5))):
        raise ValueError("Invalid exact neighbor IDs or scores")
    return dict(query_ids=ids,neighbor_raw_ids=neighbors,scores=scores)

