"""AST-delimited original scientific blocks; caller supplies paths and modules."""
import numpy as np
from scipy.stats import beta
import time
import json
import csv

def source_order(vectors, union_ids, state_ids, history, seed):
    if history == "random":
        all_order = union_ids[np.random.RandomState(seed).permutation(len(union_ids))]
    elif history == "norm_ascending":
        norms = np.empty(len(union_ids), dtype=np.float64)
        for begin in range(0, len(union_ids), 8192):
            end = min(begin + 8192, len(union_ids))
            block = vectors[union_ids[begin:end]].astype(np.float64)
            norms[begin:end] = np.einsum("ij,ij->i", block, block)
        all_order = union_ids[np.lexsort((union_ids, norms))]
    else:
        raise ValueError("Unknown build history")
    return all_order[np.isin(all_order, state_ids, assume_unique=True)]

def build_e1a(vectors, heldout, excluded, base_rows, args, prereg, index_path, stem, hnswlib):
    keep = np.ones(len(vectors), dtype=bool)
    keep[heldout] = False
    keep[excluded] = False
    raw_ids = np.flatnonzero(keep).astype(np.int64)
    if len(raw_ids) != base_rows:
        raise ValueError("Effective base size mismatch")
    if args.history == "random":
        order = np.random.RandomState(args.seed).permutation(len(raw_ids))
    else:
        norms = np.empty(len(raw_ids), dtype=np.float64)
        for begin in range(0, len(raw_ids), 8192):
            end = min(begin + 8192, len(raw_ids))
            chunk = vectors[raw_ids[begin:end]].astype(np.float64)
            norms[begin:end] = np.einsum("ij,ij->i", chunk, chunk)
        order = np.lexsort((raw_ids, norms))
    metric = prereg["implementation"]["metric_by_dataset"][args.dataset]
    space = "l2" if metric == "l2" else "ip"
    graph = hnswlib.Index(space=space, dim=vectors.shape[1])
    graph.init_index(max_elements=len(raw_ids), M=16, ef_construction=100, random_seed=args.seed)
    graph.set_num_threads(1)
    began = time.monotonic()
    batch = prereg["implementation"]["insertion_batch_rows"]
    for begin in range(0, len(order), batch):
        selected = raw_ids[order[begin:begin + batch]]
        graph.add_items(vectors[selected], selected, num_threads=1)
        if begin == 0 or (begin // batch + 1) % 20 == 0:
            print(json.dumps({"stem": stem, "inserted": min(begin + batch, len(order)), "total": len(order)}), flush=True)
    elapsed = time.monotonic() - began
    if graph.get_current_count() != len(raw_ids):
        raise ValueError("Incomplete graph")
    graph.save_index(str(index_path))
    return graph

def build_e1b(vectors, union_ids, state_ids, count, args, dataset_row, prefix, out, pair_key, hnswlib):
    order = source_order(vectors, union_ids, state_ids, args.history, args.seed)
    if order.size != count or np.unique(order).size != count:
        raise ValueError("Build insertion order incomplete")
    metric = "l2" if prefix == "sift" else "ip"
    graph = hnswlib.Index(space=metric, dim=int(dataset_row["train_shape"][1]))
    graph.init_index(max_elements=count, M=16, ef_construction=100, random_seed=args.seed)
    graph.set_num_threads(1)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    for begin in range(0, count, 8192):
        selected = order[begin:begin + 8192]
        graph.add_items(vectors[selected], selected, num_threads=1)
        if begin == 0 or (begin // 8192 + 1) % 20 == 0:
            print(json.dumps({"pair_key": pair_key, "state": args.state,
                              "inserted": min(begin + 8192, count), "total": count}), flush=True)
    if graph.get_current_count() != count:
        raise ValueError("Graph build incomplete")
    index_path = out / "index.bin"
    graph.save_index(str(index_path))
    return graph

def candidate_roles(roles_doc, exclusions_doc, SPECS, ROLE_COUNTS):
    arrays = {}
    receipt = {"datasets": []}
    for name, prefix, seed, expected_eligible, expected_reserve, expected_graph in SPECS:
        row = next(x for x in roles_doc["datasets"] if x["name"] == name)
        exclusion = next(x for x in exclusions_doc["datasets"] if x["name"] == name)
        n = int(row["train_shape"][0])
        old_query = np.asarray([value for values in row["roles"].values() for value in values], dtype=np.int64)
        old_excluded = np.asarray(exclusion["excluded_index_row_ids"], dtype=np.int64)
        if old_query.size != 2500 or np.unique(old_query).size != 2500:
            raise ValueError("Old role count or uniqueness mismatch")
        if np.intersect1d(old_query, old_excluded).size:
            raise ValueError("Old exclusion overlaps old query")
        available = np.ones(n, dtype=bool)
        available[old_query] = False
        available[old_excluded] = False
        pool = np.flatnonzero(available)
        rng = np.random.Generator(np.random.PCG64(seed))
        chosen = rng.permutation(pool)
        new_query = chosen[:2500]
        eligible = chosen[2500:]
        reserve = int(np.floor(0.05 * eligible.size))
        if eligible.size != expected_eligible or reserve != expected_reserve:
            raise ValueError("Prospective cardinality mismatch")
        old_only = np.sort(eligible[:reserve])
        new_only = np.sort(eligible[reserve:2 * reserve])
        if np.intersect1d(old_only, new_only).size:
            raise ValueError("Turnover reserves overlap")
        offset = 0
        for role, count in ROLE_COUNTS:
            arrays[f"{prefix}_{role}_ids"] = np.sort(new_query[offset:offset + count]).astype(np.int64)
            offset += count
        arrays[f"{prefix}_old_only_ids"] = old_only.astype(np.int64)
        arrays[f"{prefix}_new_only_ids"] = new_only.astype(np.int64)
        row_receipt = {
            "dataset": name,
            "source_sha256": row["source_sha256"],
            "pcg64_seed": seed,
            "old_query_count": int(old_query.size),
            "old_duplicate_exclusion_count": int(old_excluded.size),
            "fresh_query_count": 2500,
            "eligible_after_all_query_roles_and_old_exclusions": int(eligible.size),
            "old_only_count": reserve,
            "new_only_count": reserve,
            "initial_and_refreshed_graph_count_before_new_content_repair": int(eligible.size - reserve),
            "turnover_fraction_of_eligible": reserve / eligible.size,
        }
        if row_receipt["initial_and_refreshed_graph_count_before_new_content_repair"] != expected_graph:
            raise ValueError("Prospective graph count mismatch")
        receipt["datasets"].append(row_receipt)
    return arrays

def repair_one(roles, exclusions, candidate, content, name, prefix, expected_count, ROLE_NAMES):
    arrays = {}
    rows = []
    role = next(x for x in roles["datasets"] if x["name"] == name)
    excluded = next(x for x in exclusions["datasets"] if x["name"] == name)
    audited = next(x for x in content["datasets"] if x["dataset"] == name)
    if audited["query_query_duplicate_pairs"] or not audited["fresh_query_independence_pass"]:
        raise ValueError("Fresh query content overlap")
    old_queries = [int(i) for values in role["roles"].values() for i in values]
    fresh_queries = [int(i) for role_name in ROLE_NAMES
                     for i in candidate[f"{prefix}_{role_name}_ids"]]
    n = int(role["train_shape"][0])
    disallowed = np.zeros(n, dtype=bool)
    disallowed[old_queries] = True
    disallowed[fresh_queries] = True
    disallowed[excluded["excluded_index_row_ids"]] = True
    disallowed[audited["new_counterpart_exclusion_ids"]] = True
    old_only = candidate[f"{prefix}_old_only_ids"].copy()
    new_only = candidate[f"{prefix}_new_only_ids"].copy()
    live_old = old_only[~disallowed[old_only]]
    live_new = new_only[~disallowed[new_only]]
    if live_old.size > live_new.size:
        neutral_trim = live_old[:live_old.size - live_new.size]
    else:
        neutral_trim = live_new[:live_new.size - live_old.size]
    disallowed[neutral_trim] = True
    initial_allowed = ~disallowed.copy()
    refreshed_allowed = ~disallowed.copy()
    initial_allowed[new_only] = False
    refreshed_allowed[old_only] = False
    initial = np.flatnonzero(initial_allowed).astype(np.int64)
    refreshed = np.flatnonzero(refreshed_allowed).astype(np.int64)
    if initial.size != expected_count or refreshed.size != expected_count:
        raise ValueError("Final graph count mismatch")
    initial_only = np.setdiff1d(initial, refreshed, assume_unique=True)
    refreshed_only = np.setdiff1d(refreshed, initial, assume_unique=True)
    if initial_only.size != refreshed_only.size or initial_only.size == 0:
        raise ValueError("Final turnover is not balanced")
    if np.intersect1d(np.r_[old_queries, fresh_queries], np.r_[initial, refreshed]).size:
        raise ValueError("Query/member overlap")
    arrays[f"{prefix}_initial_member_ids"] = initial
    arrays[f"{prefix}_refreshed_member_ids"] = refreshed
    arrays[f"{prefix}_neutral_trim_ids"] = np.sort(neutral_trim).astype(np.int64)
    rows.append({
        "dataset": name,
        "source_sha256": role["source_sha256"],
        "final_initial_count": int(initial.size),
        "final_refreshed_count": int(refreshed.size),
        "effective_old_only_count": int(initial_only.size),
        "effective_new_only_count": int(refreshed_only.size),
        "new_content_counterpart_exclusions": audited["new_counterpart_exclusion_count"],
        "neutral_smallest_id_trim_count": int(neutral_trim.size),
        "neutral_smallest_id_trim_ids": np.sort(neutral_trim).astype(int).tolist(),
        "nominal_turnover_rate": "5% of candidate eligible train rows, followed by frozen content QA and symmetric cardinality repair",
        "actual_turnover_fraction_of_graph": float(initial_only.size / initial.size),
    })
    return arrays, rows

def cp_upper(failures, n, delta):
    return 1.0 if failures == n else float(beta.ppf(1.0 - delta, failures + 1, n - failures))

def source_response(ids, source, role_row, unit, graph_path, graph_receipt, grid, neighbors, h5py, hnswlib):
    order = np.argsort(ids)
    with h5py.File(source, 'r') as handle:
        train = handle['train']  # Do not open HDF5 test/neighbors/distances.
        if list(train.shape) != role_row['train_shape'] or str(train.dtype) != 'float32':
            raise ValueError('Train metadata mismatch')
        vectors = np.asarray(train[ids[order]], dtype=np.float32)
    queries = np.ascontiguousarray(vectors[np.argsort(order)])
    metric = 'l2' if unit['prefix'] == 'sift' else 'ip'
    graph = hnswlib.Index(space=metric, dim=queries.shape[1])
    graph.load_index(str(graph_path), max_elements=graph_receipt['member_count'])
    if graph.get_current_count() != graph_receipt['member_count']:
        raise ValueError('Reload count mismatch')
    graph.set_num_threads(1)
    topk = np.empty((11, 500, 10), dtype=np.int64)
    hits = np.empty((11, 500), dtype=np.uint8)
    exact_sets = [set(row.tolist()) for row in neighbors]
    for j, ef in enumerate(grid):
        graph.set_ef(int(ef))
        labels, _ = graph.knn_query(queries, k=10, num_threads=1)
        if labels.shape != (500, 10) or np.any(labels < 0) or np.any(labels == ids[:, None]):
            raise ValueError('Invalid approximate labels')
        if np.any(np.sort(labels, axis=1)[:, 1:] == np.sort(labels, axis=1)[:, :-1]):
            raise ValueError('Duplicate approximate labels')
        topk[j] = labels
        hits[j] = np.fromiter((len(set(row.tolist()) & exact_sets[i]) for i, row in enumerate(labels)), dtype=np.uint8, count=500)
    z_rec = hits < 10
    z_censor = z_rec[-1].copy()
    z_abs = np.logical_or(z_rec, z_censor[None, :])
    failures = z_abs.sum(axis=1).astype(int)
    ucbs = [cp_upper(int(x), 500, 0.05 / 11) for x in failures]
    accepted = [i for i, value in enumerate(ucbs) if value <= 0.05]
    selected = None if not accepted else int(grid[accepted[0]])
    return (dict(query_ids=ids, action_grid=grid, topk=topk, hits=hits, z_rec=z_rec, z_censor=z_censor, z_abs=z_abs), dict(selected_source_action=selected, cp_ucb=ucbs, absolute_failure_counts=failures.tolist()))

def cert_response(ids, source, role_row, unit, graph_path, graph_receipt, selected, neighbors, h5py, hnswlib):
    order = np.argsort(ids)
    with h5py.File(source, 'r') as handle:
        train = handle['train']  # Never open test/neighbors/distances.
        if list(train.shape) != role_row['train_shape'] or str(train.dtype) != 'float32':
            raise ValueError('Train metadata mismatch')
        vectors = np.asarray(train[ids[order]], dtype=np.float32)
    queries = np.ascontiguousarray(vectors[np.argsort(order)])
    graph = hnswlib.Index(space='l2' if unit['prefix'] == 'sift' else 'ip', dim=queries.shape[1])
    graph.load_index(str(graph_path), max_elements=graph_receipt['member_count'])
    if graph.get_current_count() != graph_receipt['member_count']:
        raise ValueError('Refreshed graph reload count mismatch')
    graph.set_num_threads(1)
    actions = (selected, 2400)
    topk = np.empty((2, 500, 10), dtype=np.int64)
    hits = np.empty((2, 500), dtype=np.uint8)
    exact_sets = [set(row.tolist()) for row in neighbors]
    for j, ef in enumerate(actions):
        graph.set_ef(ef)
        labels, _ = graph.knn_query(queries, k=10, num_threads=1)
        if labels.shape != (500, 10) or np.any(labels < 0) or np.any(labels == ids[:, None]):
            raise ValueError('Invalid approximate labels')
        if np.any(np.sort(labels, axis=1)[:, 1:] == np.sort(labels, axis=1)[:, :-1]):
            raise ValueError('Duplicate approximate labels')
        topk[j] = labels
        hits[j] = np.fromiter((len(set(row.tolist()) & exact_sets[i]) for i, row in enumerate(labels)), dtype=np.uint8, count=500)
    z_rec = hits < 10
    z_abs_candidate = np.logical_or(z_rec[0], z_rec[1])
    z_abs_endpoint = z_rec[1]
    failures = (int(z_abs_candidate.sum()), int(z_abs_endpoint.sum()))
    ucbs = (cp_upper(failures[0], 500, 0.025), cp_upper(failures[1], 500, 0.025))
    decision = 'execute_candidate' if ucbs[0] <= 0.05 and ucbs[1] <= 0.05 else ('endpoint_fallback' if ucbs[1] <= 0.05 else 'abstain')
    return (dict(query_ids=ids, action_ef=np.asarray(actions,dtype=np.int32), topk=topk, hits=hits, z_rec=z_rec, z_abs_candidate=z_abs_candidate, z_abs_endpoint=z_abs_endpoint), dict(decision=decision, selected_source_action=selected, cp_ucb=list(ucbs)))

def eval_response(ids, train_path, role, unit, graph_paths, graph_counts, ef, decision, truths, h5py, hnswlib):
    order = np.argsort(ids)
    with h5py.File(train_path, 'r') as handle:
        train = handle['train']  # Never access test/neighbors/distances.
        if list(train.shape) != role['train_shape'] or str(train.dtype) != 'float32':
            raise ValueError('Train metadata mismatch')
        sorted_vectors = np.asarray(train[ids[order]], dtype=np.float32)
    queries = np.ascontiguousarray(sorted_vectors[np.argsort(order)])
    topk = np.empty((2, 2, 1000, 10), dtype=np.int64)
    hits = np.empty((2, 2, 1000), dtype=np.uint8)
    for state_index, state in enumerate(('initial', 'refreshed')):
        graph = hnswlib.Index(space='l2' if unit['prefix'] == 'sift' else 'ip', dim=queries.shape[1])
        graph.load_index(str(graph_paths[state_index]), max_elements=graph_counts[state_index])
        if graph.get_current_count() != graph_counts[state_index]:
            raise ValueError('Graph reload count mismatch')
        graph.set_num_threads(1)
        exact_sets = [set(row.tolist()) for row in truths[state_index]]
        for arm_index, action in enumerate((ef, 2400)):
            graph.set_ef(action)
            labels, _ = graph.knn_query(queries, k=10, num_threads=1)
            if labels.shape != (1000, 10) or np.any(labels < 0) or np.any(labels == ids[:, None]):
                raise ValueError('Invalid approximate labels')
            if np.any(np.diff(np.sort(labels, axis=1), axis=1) == 0):
                raise ValueError('Duplicate approximate labels')
            topk[state_index, arm_index] = labels
            hits[state_index, arm_index] = np.fromiter((len(set(row.tolist()) & exact_sets[i]) for i, row in enumerate(labels)), dtype=np.uint8, count=1000)
    z_rec = hits < 10  # Recall@10 < 0.95 iff top10 overlap <= 9.
    z_abs = np.logical_or(z_rec[:, 0], z_rec[:, 1])
    z_endpoint = z_rec[:, 1]
    executed_arm = 0 if decision == 'execute_candidate' else (1 if decision == 'endpoint_fallback' else -1)
    return (dict(query_ids=ids, action_ef=np.asarray([ef,2400],dtype=np.int32), topk=topk, hits=hits, z_rec=z_rec, z_abs=z_abs, z_endpoint=z_endpoint, executed_arm=np.asarray(executed_arm,dtype=np.int8)), dict(decision=decision, selected_source_action=ef, executed_arm_index=executed_arm))

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

def truth_e1b_source(role_row, metric, count, query_ids, member_ids, source, faiss, h5py):
    dim = int(role_row["train_shape"][1])
    flat = faiss.IndexFlatL2(dim) if metric == "l2" else faiss.IndexFlatIP(dim)
    begin = time.monotonic()
    with h5py.File(source, "r") as handle:
        train = handle["train"]
        if list(train.shape) != role_row["train_shape"] or str(train.dtype) != "float32":
            raise ValueError("Train metadata mismatch")
        queries = np.ascontiguousarray(train[query_ids], dtype=np.float32)
        mask = np.zeros(train.shape[0], dtype=bool)
        mask[member_ids] = True
        for start in range(0, train.shape[0], 8192):
            end = min(start + 8192, train.shape[0])
            if np.any(mask[start:end]):
                block = np.ascontiguousarray(train[start:end][mask[start:end]], dtype=np.float32)
                flat.add(block)
    if flat.ntotal != count:
        raise ValueError("Flat index count mismatch")
    faiss.omp_set_num_threads(16)
    scores, positions = flat.search(queries, 10)
    if positions.shape != (500, 10) or np.any(positions < 0) or np.any(positions >= count):
        raise ValueError("Invalid exact positions")
    neighbors = member_ids[positions]
    if np.any(neighbors == query_ids[:, None]) or np.any(np.sort(neighbors, axis=1)[:, 1:] == np.sort(neighbors, axis=1)[:, :-1]):
        raise ValueError("Self or duplicate exact neighbor")
    if not np.all(np.isfinite(scores)):
        raise ValueError("Nonfinite exact score")
    if metric == "l2" and np.any(np.diff(scores, axis=1) < -1e-5):
        raise ValueError("L2 score ordering mismatch")
    if metric == "ip" and np.any(np.diff(scores, axis=1) > 1e-5):
        raise ValueError("IP score ordering mismatch")
    return dict(query_ids=query_ids,neighbor_raw_ids=neighbors,scores=scores)

def truth_e1b_certify(role_row, unit, query_ids, member_ids, source, faiss, h5py):
    dim = int(role_row['train_shape'][1])
    flat = faiss.IndexFlatL2(dim) if unit['metric'] == 'l2' else faiss.IndexFlatIP(dim)
    with h5py.File(source, 'r') as handle:
        train = handle['train']  # HDF5 test/neighbors/distances never opened.
        if list(train.shape) != role_row['train_shape'] or str(train.dtype) != 'float32':
            raise ValueError('Train shape/dtype mismatch')
        queries = np.ascontiguousarray(train[query_ids], dtype=np.float32)
        mask = np.zeros(train.shape[0], dtype=bool)
        mask[member_ids] = True
        for start in range(0, train.shape[0], 8192):
            end = min(start + 8192, train.shape[0])
            if np.any(mask[start:end]):
                block = np.ascontiguousarray(train[start:end][mask[start:end]], dtype=np.float32)
                flat.add(block)
    if flat.ntotal != unit['member_count']:
        raise ValueError('Flat index member count mismatch')
    faiss.omp_set_num_threads(16)
    scores, positions = flat.search(queries, 10)
    if positions.shape != (500, 10) or np.any(positions < 0) or np.any(positions >= flat.ntotal):
        raise ValueError('Exact top-10 positions invalid')
    neighbors = member_ids[positions]
    if np.any(neighbors == query_ids[:, None]) or np.any(np.diff(np.sort(neighbors, axis=1), axis=1) == 0):
        raise ValueError('Exact top-10 self/duplicate ID')
    if not np.all(np.isfinite(scores)):
        raise ValueError('Nonfinite exact score')
    if unit['metric'] == 'l2' and np.any(np.diff(scores, axis=1) < -1e-5):
        raise ValueError('L2 score order invalid')
    if unit['metric'] == 'ip' and np.any(np.diff(scores, axis=1) > 1e-5):
        raise ValueError('IP score order invalid')
    return dict(query_ids=query_ids,neighbor_raw_ids=neighbors,scores=scores)

def truth_e1b_evaluate(role_row, unit, query_ids, member_ids, source, faiss, h5py):
    dim = int(role_row['train_shape'][1])
    flat = faiss.IndexFlatL2(dim) if unit['metric'] == 'l2' else faiss.IndexFlatIP(dim)
    with h5py.File(source, 'r') as handle:
        train = handle['train']  # Raw HDF5 test/neighbors/distances never opened.
        if list(train.shape) != role_row['train_shape'] or str(train.dtype) != 'float32':
            raise ValueError('Train metadata mismatch')
        queries = np.ascontiguousarray(train[query_ids], dtype=np.float32)
        mask = np.zeros(train.shape[0], dtype=bool)
        mask[member_ids] = True
        for start in range(0, train.shape[0], 8192):
            end = min(start + 8192, train.shape[0])
            if np.any(mask[start:end]):
                flat.add(np.ascontiguousarray(train[start:end][mask[start:end]], dtype=np.float32))
    if flat.ntotal != unit['member_count']:
        raise ValueError('Exact index member count mismatch')
    faiss.omp_set_num_threads(16)
    scores, positions = flat.search(queries, 10)
    if positions.shape != (1000, 10) or np.any(positions < 0) or np.any(positions >= flat.ntotal):
        raise ValueError('Exact top-10 positions invalid')
    neighbors = member_ids[positions]
    if np.any(neighbors == query_ids[:, None]) or np.any(np.diff(np.sort(neighbors, axis=1), axis=1) == 0):
        raise ValueError('Exact top-10 self/duplicate raw ID')
    if not np.all(np.isfinite(scores)):
        raise ValueError('Nonfinite exact score')
    if unit['metric'] == 'l2' and np.any(np.diff(scores, axis=1) < -1e-5):
        raise ValueError('L2 exact score order invalid')
    if unit['metric'] == 'ip' and np.any(np.diff(scores, axis=1) > 1e-5):
        raise ValueError('IP exact score order invalid')
    return dict(query_ids=query_ids,neighbor_raw_ids=neighbors,scores=scores)

def e1a_source_response(design_ids, source, args, index_path, graph_row, protocol, neighbors, stem, h5py, hnswlib):
    order = np.argsort(design_ids)
    with h5py.File(source, "r") as handle:
        train = handle["train"]  # HDF5 test/neighbors/distances never opened.
        sorted_vectors = np.asarray(train[design_ids[order]], dtype=np.float32)
    queries = np.ascontiguousarray(sorted_vectors[np.argsort(order)])
    space = "l2" if args.dataset == "sift-1m-heldout" else "ip"
    graph = hnswlib.Index(space=space, dim=queries.shape[1])
    graph.load_index(str(index_path), max_elements=graph_row["serialized_count"])
    graph.set_num_threads(1)
    grid = np.asarray(protocol["action_grid"], dtype=np.int32)
    topk = np.empty((len(grid), 500, 10), dtype=np.int64)
    hits = np.empty((len(grid), 500), dtype=np.uint8)
    for j, action in enumerate(grid):
        graph.set_ef(int(action))
        labels, _ = graph.knn_query(queries, k=10, num_threads=1)
        if labels.shape != (500, 10) or np.any(labels < 0):
            raise ValueError("Native top-k shape/labels invalid")
        topk[j] = labels
        hits[j] = np.fromiter((len(set(a.tolist()) & set(b.tolist())) for a, b in zip(labels, neighbors)), dtype=np.uint8, count=500)
        print(json.dumps({"stem": stem, "ef": int(action), "raw_failures": int(np.count_nonzero(hits[j] < 10))}), flush=True)
    z_rec = hits < 10
    z_censor = z_rec[-1].copy()
    z_abs = np.logical_or(z_rec, z_censor[None, :])
    if np.any(z_abs[:, z_censor] == 0):
        raise ValueError("Endpoint-censoring closure failed")
    failure_counts = z_abs.sum(axis=1).astype(int)
    ucbs = [cp_upper(int(x), 500, 0.05 / len(grid)) for x in failure_counts]
    accepted = [j for j, u in enumerate(ucbs) if u <= 0.05]
    selected = accepted[0] if accepted else None
    return (dict(query_ids=design_ids,action_grid=grid,topk=topk,hits=hits,z_rec=z_rec,z_censor=z_censor,z_abs=z_abs), dict(selected_source_action=None if selected is None else int(grid[selected]),cp_ucb=ucbs))

def e1a_selection_response(ids, n, source, dataset, index_path, row, grid, neighbors, counter, query_bin, csv_path, h5py, hnswlib, subprocess, role):
    panel_row = row
    qbin = query_bin
    order = np.argsort(ids[:n])
    with h5py.File(source, "r") as handle:
        sorted_vectors = np.asarray(handle["train"][ids[:n][order]], dtype=np.float32)
    queries = np.ascontiguousarray(sorted_vectors[np.argsort(order)])
    space = "l2" if dataset == "sift-1m-heldout" else "ip"
    graph = hnswlib.Index(space=space, dim=queries.shape[1])
    graph.load_index(str(index_path), max_elements=row["serialized_count"])
    graph.set_num_threads(1)
    native_topk = np.empty((len(grid), n, 10), dtype=np.int64)
    native_hits = np.empty((len(grid), n), dtype=np.uint8)
    for j, ef in enumerate(grid):
        graph.set_ef(ef)
        labels, _ = graph.knn_query(queries, k=10, num_threads=1)
        if labels.shape != (n, 10) or np.any(labels < 0):
            raise ValueError("Native top-k invalid")
        native_topk[j] = labels
        native_hits[j] = np.fromiter((len(set(a.tolist()) & set(b.tolist())) for a, b in zip(labels, neighbors[:n])), dtype=np.uint8, count=n)
    z_rec = native_hits < 10
    z_censor = z_rec[-1].copy()
    z_abs = np.logical_or(z_rec, z_censor[None, :])
    command = [str(counter), str(index_path), str(query_bin), space, ",".join(map(str, grid)), str(n), str(row["serialized_count"]), str(csv_path)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    ndc = np.empty((len(grid), n), dtype=np.uint64)
    seen = set()
    mismatches = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["query_id", "ef", "ndc", "topk"]:
            raise ValueError("Counter CSV schema mismatch")
        for line in reader:
            ef, qid, count = int(line["ef"]), int(line["query_id"]), int(line["ndc"])
            if ef not in grid or qid not in ids[:n] or count <= 0:
                mismatches.append("action_query_or_count")
                continue
            j = grid.index(ef)
            i = int(np.flatnonzero(ids[:n] == qid)[0])
            if (j, i) in seen:
                mismatches.append("duplicate_cell")
                continue
            seen.add((j, i))
            ndc[j, i] = count
            found = np.asarray([int(v) for v in line["topk"].split(";")], dtype=np.int64)
            hits = len(set(found.tolist()) & set(neighbors[i].tolist()))
            observed_z_abs = hits < 10 or bool(z_censor[i])
            if len(found) != 10 or not np.array_equal(found, native_topk[j, i]) or hits != int(native_hits[j, i]) or observed_z_abs != bool(z_abs[j, i]):
                mismatches.append("native_equivalence")
    if len(seen) != n * len(grid):
        mismatches.append("missing_cells")
    return (dict(query_ids=ids[:n],action_grid=np.asarray(grid),topk=native_topk,hits=native_hits,z_rec=z_rec,z_censor=z_censor,z_abs=z_abs,ndc=ndc),mismatches)

def e1a_certify_response(ids, n, source, dataset, index_path, row, grid, neighbors, counter, query_bin, csv_path, h5py, hnswlib, subprocess, role):
    panel_row = row
    qbin = query_bin
    order = np.argsort(ids[:n])
    with h5py.File(source, "r") as handle:
        sorted_vectors = np.asarray(handle["train"][ids[:n][order]], dtype=np.float32)
    queries = np.ascontiguousarray(sorted_vectors[np.argsort(order)])
    space = "l2" if dataset == "sift-1m-heldout" else "ip"
    index = hnswlib.Index(space=space, dim=role["train_shape"][1])
    index.load_index(str(index_path), max_elements=panel_row["serialized_count"])
    index.set_num_threads(1)
    topk = np.empty((len(grid), n, 10), dtype=np.int64)
    hits = np.empty((len(grid), n), dtype=np.uint8)
    for j, ef in enumerate(grid):
        index.set_ef(ef)
        labels, _ = index.knn_query(queries, k=10, num_threads=1)
        if labels.shape != (n, 10) or np.any(labels < 0):
            raise ValueError("Native certification top-k invalid")
        topk[j] = labels
        hits[j] = np.fromiter((len(set(a.tolist()) & set(b.tolist())) for a, b in zip(labels, neighbors[:n])), dtype=np.uint8, count=n)
    z_rec = hits < 10
    z_censor = z_rec[-1].copy()
    z_abs = np.logical_or(z_rec, z_censor[None, :])
    subprocess.run([str(counter), str(index_path), str(qbin), space, ",".join(map(str, grid)), str(n), str(panel_row["serialized_count"]), str(csv_path)],
                   check=True, capture_output=True, text=True)
    ndc = np.empty((len(grid), n), dtype=np.uint64)
    seen = set()
    mismatches = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["query_id", "ef", "ndc", "topk"]:
            raise ValueError("Counter CSV schema mismatch")
        for row in reader:
            ef, qid, count = int(row["ef"]), int(row["query_id"]), int(row["ndc"])
            if ef not in grid or qid not in ids[:n] or count <= 0:
                mismatches.append("invalid_action_query_count")
                continue
            j = grid.index(ef)
            i = int(np.flatnonzero(ids[:n] == qid)[0])
            if (j, i) in seen:
                mismatches.append("duplicate_cell")
                continue
            seen.add((j, i))
            ndc[j, i] = count
            found = np.asarray([int(v) for v in row["topk"].split(";")], dtype=np.int64)
            observed_hits = len(set(found.tolist()) & set(neighbors[i].tolist()))
            if len(found) != 10 or not np.array_equal(found, topk[j, i]) or observed_hits != int(hits[j, i]) or (observed_hits < 10 or bool(z_censor[i])) != bool(z_abs[j, i]):
                mismatches.append("native_equivalence")
    if len(seen) != len(grid) * n:
        mismatches.append("missing_cells")
    return (dict(query_ids=ids[:n],action_grid=np.asarray(grid),topk=topk,hits=hits,z_rec=z_rec,z_censor=z_censor,z_abs=z_abs,ndc=ndc),mismatches)

def e1a_evaluate_response(ids, n, source, dataset, index_path, row, grid, neighbors, counter, query_bin, csv_path, h5py, hnswlib, subprocess, role):
    panel_row = row
    qbin = query_bin
    order = np.argsort(ids[:n])
    with h5py.File(source, "r") as handle:
        sorted_vectors = np.asarray(handle["train"][ids[:n][order]], dtype=np.float32)
    queries = np.ascontiguousarray(sorted_vectors[np.argsort(order)])
    space = "l2" if dataset == "sift-1m-heldout" else "ip"
    index = hnswlib.Index(space=space, dim=role["train_shape"][1])
    index.load_index(str(index_path), max_elements=panel_row["serialized_count"])
    index.set_num_threads(1)
    topk = np.empty((len(grid), n, 10), dtype=np.int64)
    hits = np.empty((len(grid), n), dtype=np.uint8)
    for j, ef in enumerate(grid):
        index.set_ef(ef)
        labels, _ = index.knn_query(queries, k=10, num_threads=1)
        if labels.shape != (n, 10) or np.any(labels < 0):
            raise ValueError("Native evaluation top-k invalid")
        topk[j] = labels
        hits[j] = np.fromiter((len(set(a.tolist()) & set(b.tolist())) for a, b in zip(labels, neighbors[:n])), dtype=np.uint8, count=n)
    z_rec = hits < 10
    z_censor = z_rec[-1].copy()
    z_abs = np.logical_or(z_rec, z_censor[None, :])
    subprocess.run([str(counter), str(index_path), str(qbin), space, ",".join(map(str, grid)), str(n), str(panel_row["serialized_count"]), str(csv_path)],
                   check=True, capture_output=True, text=True)
    ndc = np.empty((len(grid), n), dtype=np.uint64)
    seen = set()
    mismatches = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["query_id", "ef", "ndc", "topk"]:
            raise ValueError("Counter CSV schema mismatch")
        for row in reader:
            ef, qid, count = int(row["ef"]), int(row["query_id"]), int(row["ndc"])
            if ef not in grid or qid not in ids[:n] or count <= 0:
                mismatches.append("invalid_action_query_count")
                continue
            j = grid.index(ef)
            i = int(np.flatnonzero(ids[:n] == qid)[0])
            if (j, i) in seen:
                mismatches.append("duplicate_cell")
                continue
            seen.add((j, i))
            ndc[j, i] = count
            found = np.asarray([int(v) for v in row["topk"].split(";")], dtype=np.int64)
            observed_hits = len(set(found.tolist()) & set(neighbors[i].tolist()))
            if len(found) != 10 or not np.array_equal(found, topk[j, i]) or observed_hits != int(hits[j, i]) or (observed_hits < 10 or bool(z_censor[i])) != bool(z_abs[j, i]):
                mismatches.append("native_equivalence")
    if len(seen) != len(grid) * n:
        mismatches.append("missing_cells")
    return (dict(query_ids=ids[:n],action_grid=np.asarray(grid),topk=topk,hits=hits,z_rec=z_rec,z_censor=z_censor,z_abs=z_abs,ndc=ndc),mismatches)

GRID = [10,20,40,80,120,200,400,800,1200,1600,2400]
SEEDS=[13,83,197,2029]
HISTORIES=["random","norm_ascending"]
DELTA=.025
ALPHA=.05

def build_id(seed, history):
    return f"seed{seed}_{history}"

def e1a_selection_policy(dataset, responses, source_rows):
    actions=[]
    globals_=[]
    for target_seed in SEEDS:
                for target_history in HISTORIES:
                    tid = build_id(target_seed, target_history)
                    z_abs, ndc = responses[tid]
                    global_ucb = [cp_upper(int(z_abs[j].sum()), 500, .05 / 11) for j in range(11)]
                    qualified_global = [j for j, ucb in enumerate(global_ucb) if ucb <= .05]
                    gj = qualified_global[0] if qualified_global else 10
                    globals_.append({
                        "dataset": dataset, "target_build_id": tid,
                        "selected_ef": GRID[gj], "qualified_on_selection": bool(qualified_global),
                        "selection_failures": int(z_abs[gj].sum()), "selection_cp_ucb": global_ucb[gj],
                        "grid_cp_delta_per_action": .05 / 11,
                        "mean_selection_ndc": float(ndc[gj].mean()),
                        "endpoint_mean_selection_ndc": float(ndc[-1].mean()),
                        "certification_status": "NOT_ACCESSED",
                    })
                    for source_seed in SEEDS:
                        for source_history in HISTORIES:
                            sid = build_id(source_seed, source_history)
                            if sid == tid:
                                continue
                            source = next(r for r in source_rows if (r["dataset"], r["seed"], r["history"]) == (dataset, source_seed, source_history))
                            source_ef = source["selected_source_action"]
                            if source_ef not in GRID:
                                raise ValueError(f"Source action absent: {dataset}/{sid}")
                            source_j = GRID.index(source_ef)
                            rungs = []
                            used_ef = set()
                            for shift in range(4):
                                j = min(source_j + shift, 10)
                                if GRID[j] in used_ef:
                                    continue
                                used_ef.add(GRID[j])
                                failures = int(z_abs[j].sum())
                                ucb = cp_upper(failures, 500, .05 / 4)
                                rungs.append({"shift": shift, "ef": GRID[j], "selection_failures": failures,
                                              "selection_cp_ucb": ucb, "mean_selection_ndc": float(ndc[j].mean()),
                                              "eligible_selection_screen": ucb <= .05})
                            eligible = [r for r in rungs if r["eligible_selection_screen"]]
                            chosen = min(eligible, key=lambda r: (r["mean_selection_ndc"], r["shift"], r["ef"])) if eligible else None
                            actions.append({
                                "dataset": dataset, "source_build_id": sid, "target_build_id": tid,
                                "source_action_ef": source_ef,
                                "one_rung_ef": GRID[min(source_j + 1, 10)],
                                "rungs": rungs,
                                "selected_shift": None if chosen is None else chosen["shift"],
                                "selected_ef": 2400 if chosen is None else chosen["ef"],
                                "selection_screen_passed": chosen is not None,
                                "selection_cp_delta_per_shift": .05 / 4,
                                "fallback_candidate_if_no_eligible_rung": chosen is None,
                                "certification_status": "NOT_ACCESSED",
                            })
    return dict(directed_pair_actions=actions,target_global_actions=globals_)

def expected_grid(dataset, target, actions):
    grid = {2400}
    global_rows = [r for r in actions["target_global_actions"] if r["dataset"] == dataset and r["target_build_id"] == target]
    if len(global_rows) != 1:
        raise ValueError("Target-global cardinality mismatch")
    grid.add(global_rows[0]["selected_ef"])
    pair_rows = [r for r in actions["directed_pair_actions"] if r["dataset"] == dataset and r["target_build_id"] == target]
    if len(pair_rows) != 7:
        raise ValueError("Directed pair cardinality mismatch")
    for row in pair_rows:
        grid.update((row["source_action_ef"], row["one_rung_ef"], row["selected_ef"]))
    return sorted(grid), pair_rows, global_rows[0]

def outcome(dataset, target, source, arm, selected_ef, grid, z_abs, ndc, endpoint_failures, endpoint_ucb, cp_upper):
    j = grid.index(selected_ef)
    failures = int(z_abs[j].sum())
    ucb = cp_upper(failures)
    if endpoint_ucb > ALPHA:
        decision = "ABSTAIN"
        executed_ef = None
        reason = "ENDPOINT_NOT_QUALIFIED"
    elif ucb <= ALPHA:
        decision = "ACCEPT"
        executed_ef = selected_ef
        reason = "CANDIDATE_AND_ENDPOINT_QUALIFIED"
    else:
        decision = "FALLBACK"
        executed_ef = 2400
        reason = "CANDIDATE_NOT_QUALIFIED"
    return {
        "dataset": dataset, "target_build_id": target, "source_build_id": source, "arm": arm,
        "selected_candidate_ef": selected_ef,
        "candidate_failures_of_500": failures, "candidate_cp_ucb": ucb,
        "endpoint_failures_of_500": endpoint_failures, "endpoint_cp_ucb": endpoint_ucb,
        "candidate_delta": DELTA, "endpoint_delta": DELTA, "alpha": ALPHA,
        "decision": decision, "executed_ef": executed_ef, "reason": reason,
        "candidate_mean_certification_ndc_descriptive_only": float(ndc[j].mean()),
        "endpoint_mean_certification_ndc_descriptive_only": float(ndc[-1].mean()),
        "certification_query_count": 500,
    }

def action_grid(dataset, target_id, decisions):
    grid = {2400}
    rows = [r for r in decisions["decisions"] if r["dataset"] == dataset and r["target_build_id"] == target_id]
    if len(rows) != 23 or {r["arm"] for r in rows} != {"fixed_endpoint", "target_global", "source_reuse", "one_rung", "selected_ladder"}:
        raise ValueError("Missing predeclared comparison decisions")
    if sum(r["arm"] == "fixed_endpoint" for r in rows) != 1 or sum(r["arm"] == "target_global" for r in rows) != 1:
        raise ValueError("Missing fixed or target-global decision")
    for arm in ("source_reuse", "one_rung", "selected_ladder"):
        if sum(r["arm"] == arm for r in rows) != 7:
            raise ValueError("Missing directed pair decisions")
    for row in rows:
        if row["decision"] not in {"ACCEPT", "FALLBACK", "ABSTAIN"}:
            raise ValueError("Invalid frozen decision")
        if row["decision"] != "ABSTAIN":
            grid.add(int(row["executed_ef"]))
    result = sorted(grid)
    if result[-1] != 2400 or any(v not in [10, 20, 40, 80, 120, 200, 400, 800, 1200, 1600, 2400] for v in result):
        raise ValueError("Candidate action outside frozen grid")
    return result

