"""Original scientific blocks with explicit portable bindings; no sealed-path emulation."""
import hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.stats import beta

SEEDS=[13,83,197,2029,1103,1229,1361,1499,1621,1747,1877,1999]
HISTORIES=["random","norm_ascending"]
GRID=[16,32,64,128,256,512,1024,2048,4096]
CANDIDATE_DELTA=.025
ENDPOINT_DELTA=.025
RISK_LIMIT=.05
ENDPOINT=4096

def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            value.update(chunk)
    return value.hexdigest()

def source_cp_upper(failures, n, delta):
    if failures == n:
        return 1.0
    if failures == 0:
        return 1.0 - delta ** (1.0 / n)

    def binomial_cdf(probability):
        term = (1.0 - probability) ** n
        total = term
        ratio = probability / (1.0 - probability)
        for observed in range(failures):
            term *= (n - observed) / (observed + 1) * ratio
            total += term
        return total

    low, high = 0.0, 1.0 - 1e-15
    for _ in range(80):
        middle = (low + high) / 2.0
        if binomial_cdf(middle) > delta:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0

def cp_upper(x: int, n: int, delta: float) -> float:
    return 1.0 if x == n else float(beta.ppf(1.0 - delta, x + 1, n - x))

def build_id(seed: int, history: str) -> str:
    return f"seed{seed}_{history}"

def arm(action: int, shift, failures: int, ucb: float, response_sha: str, eligible: bool):
    return {
        "candidate_efSearch": action,
        "shift": shift,
        "selection_failures": failures,
        "selection_ucb": ucb,
        "response_sha256": response_sha,
        "eligible_selection_screen": eligible,
    }

def decide(dataset, target_id, source_id, arm_name, action, z_by_action, response_sha):
    candidate_failures = int(z_by_action[action].sum())
    endpoint_failures = int(z_by_action[ENDPOINT].sum())
    candidate_ucb = cp_upper(candidate_failures, 500, CANDIDATE_DELTA)
    endpoint_ucb = cp_upper(endpoint_failures, 500, ENDPOINT_DELTA)
    candidate_ok = candidate_ucb <= RISK_LIMIT
    endpoint_ok = endpoint_ucb <= RISK_LIMIT
    if candidate_ok and endpoint_ok:
        outcome, execute_action = "EXECUTE_CANDIDATE", action
    elif endpoint_ok:
        outcome, execute_action = "FALLBACK_ENDPOINT", ENDPOINT
    else:
        outcome, execute_action = "ABSTAIN", None
    return {
        "dataset": dataset,
        "source_build_id": source_id,
        "target_build_id": target_id,
        "arm": arm_name,
        "candidate_efSearch": action,
        "candidate_failures": candidate_failures,
        "candidate_cp_ucb": candidate_ucb,
        "candidate_delta": CANDIDATE_DELTA,
        "endpoint_failures": endpoint_failures,
        "endpoint_cp_ucb": endpoint_ucb,
        "endpoint_delta": ENDPOINT_DELTA,
        "candidate_qualified": candidate_ok,
        "endpoint_qualified": endpoint_ok,
        "decision": outcome,
        "execute_efSearch": execute_action,
        "response_sha256": response_sha,
    }

def build(vectors, raw_ids, args, index_path, stem, faiss):
    if args.history == "random":
        order = np.random.RandomState(args.seed).permutation(len(raw_ids))
    else:
        norms = np.empty(len(raw_ids), dtype=np.float64)
        for begin in range(0, len(raw_ids), 8192):
            end = min(begin + 8192, len(raw_ids))
            block = vectors[raw_ids[begin:end]].astype(np.float64)
            norms[begin:end] = np.einsum("ij,ij->i", block, block)
        order = np.lexsort((raw_ids, norms))
    metric = faiss.METRIC_L2 if args.dataset == "sift-1m-heldout" else faiss.METRIC_INNER_PRODUCT
    core = faiss.IndexHNSWFlat(vectors.shape[1], 16, metric)
    core.hnsw.efConstruction = 100
    index = faiss.IndexIDMap2(core)
    started = time.monotonic()
    for begin in range(0, len(order), 8192):
        selected = raw_ids[order[begin:begin + 8192]]
        index.add_with_ids(np.ascontiguousarray(vectors[selected]), selected)
        if begin == 0 or (begin // 8192 + 1) % 20 == 0:
            print(json.dumps({"stem": stem, "inserted": min(begin + 8192, len(order)),
                              "total": len(order)}), flush=True)
    elapsed = time.monotonic() - started
    if index.ntotal != len(raw_ids):
        raise ValueError("Incomplete Faiss index")
    mapped = faiss.vector_to_array(index.id_map)
    if not np.array_equal(mapped, raw_ids[order]):
        raise ValueError("Faiss external ID map does not preserve insertion order")
    faiss.write_index(index, str(index_path))
    replay = faiss.read_index(str(index_path))
    if replay.ntotal != index.ntotal or not np.array_equal(faiss.vector_to_array(replay.id_map), mapped):
        raise ValueError("Faiss serialization or external ID replay mismatch")
    return {'build_seconds':elapsed,'base_count':int(index.ntotal),'order':order}

def response_source(query_ids, source, index_path, build_receipt, protocol, array_path, neighbors, required_actions, stem, faiss, h5py):
    design_ids=query_ids
    receipt=build_receipt
    cp_upper=source_cp_upper
    order = np.argsort(design_ids)
    with h5py.File(source, "r") as handle:
        train = handle["train"]
        sorted_vectors = np.asarray(train[design_ids[order]], dtype=np.float32)
    queries = np.ascontiguousarray(sorted_vectors[np.argsort(order)])
    index = faiss.read_index(str(index_path))
    if index.ntotal != receipt["effective_base_count"]:
        raise ValueError("Faiss index cardinality mismatch")
    core = faiss.downcast_index(index.index)
    grid = np.asarray(protocol["source_design"]["native_efSearch_grid"], dtype=np.int32)
    topk = np.empty((len(grid), 500, 10), dtype=np.int64)
    hits = np.empty((len(grid), 500), dtype=np.uint8)
    for j, action in enumerate(grid):
        core.hnsw.efSearch = int(action)
        _, labels = index.search(queries, 10)
        if labels.shape != (500, 10) or np.any(labels < 0):
            raise ValueError("Native Faiss top-k invalid")
        topk[j] = labels
        hits[j] = np.fromiter((len(set(a.tolist()) & set(b.tolist())) for a, b in zip(labels, neighbors)),
                              dtype=np.uint8, count=500)
        print(json.dumps({"stem": stem, "efSearch": int(action),
                          "raw_failures": int(np.count_nonzero(hits[j] < 10))}), flush=True)
    z_rec = hits < 10
    z_censor = z_rec[-1].copy()
    z_abs = np.logical_or(z_rec, z_censor[None, :])
    failure_counts = z_abs.sum(axis=1).astype(int)
    per_action_delta = 0.05 / len(grid)
    ucbs = [cp_upper(int(x), 500, per_action_delta) for x in failure_counts]
    accepted = [j for j, upper in enumerate(ucbs) if upper <= 0.05]
    selected = accepted[0] if accepted else None
    endpoint_failures = int(failure_counts[-1])
    endpoint_ucb = cp_upper(endpoint_failures, 500, 0.05)
    np.savez_compressed(array_path, query_ids=design_ids, action_grid=grid, topk=topk,
                        hits=hits, z_rec=z_rec, z_censor=z_censor, z_abs=z_abs)
    return {'selected_source_action':None if selected is None else int(grid[selected]),'cp_ucb':ucbs,'endpoint_gate_pass':endpoint_ucb<=.05}

def response_selection(query_ids, source, index_path, build_receipt, protocol, array_path, neighbors, required_actions, stem, faiss, h5py):
    order = np.argsort(query_ids)
    with h5py.File(source, "r") as handle:
        train = handle["train"]
        sorted_vectors = np.asarray(train[query_ids[order]], dtype=np.float32)
    queries = np.ascontiguousarray(sorted_vectors[np.argsort(order)])
    index = faiss.read_index(str(index_path))
    if index.ntotal != build_receipt["effective_base_count"]:
        raise ValueError("Faiss index cardinality mismatch")
    core = faiss.downcast_index(index.index)
    grid = np.asarray(protocol["native_search"]["action_grid"], dtype=np.int32)
    topk = np.empty((len(grid), 500, 10), dtype=np.int64)
    hits = np.empty((len(grid), 500), dtype=np.uint8)
    for j, action in enumerate(grid):
        core.hnsw.efSearch = int(action)
        _, labels = index.search(queries, 10)
        if labels.shape != (500, 10) or np.any(labels < 0):
            raise ValueError("Native Faiss top-k invalid")
        topk[j] = labels
        hits[j] = np.fromiter((len(set(a.tolist()) & set(b.tolist())) for a, b in zip(labels, neighbors)),
                              dtype=np.uint8, count=500)
    z_rec = hits < 10
    z_censor = z_rec[-1].copy()
    z_abs = np.logical_or(z_rec, z_censor[None, :])
    np.savez_compressed(array_path, query_ids=query_ids, action_grid=grid, topk=topk,
                        hits=hits, z_rec=z_rec, z_censor=z_censor, z_abs=z_abs)
    return {'raw_failure_counts':z_rec.sum(axis=1).astype(int).tolist(),'absolute_failure_counts':z_abs.sum(axis=1).astype(int).tolist()}

def response_certify(query_ids, source, index_path, build_receipt, protocol, array_path, neighbors, required_actions, stem, faiss, h5py):
    order = np.argsort(query_ids)
    with h5py.File(source, "r") as handle:
        train = handle["train"]
        sorted_vectors = np.asarray(train[query_ids[order]], dtype=np.float32)
    queries = np.ascontiguousarray(sorted_vectors[np.argsort(order)])
    index = faiss.read_index(str(index_path))
    if index.ntotal != build_receipt["effective_base_count"]:
        raise ValueError("Faiss index cardinality mismatch")
    core = faiss.downcast_index(index.index)
    topk = np.empty((len(required_actions), 500, 10), dtype=np.int64)
    hits = np.empty((len(required_actions), 500), dtype=np.uint8)
    for j, action in enumerate(required_actions):
        core.hnsw.efSearch = action
        _, labels = index.search(queries, 10)
        if labels.shape != (500, 10) or np.any(labels < 0):
            raise ValueError("Native Faiss top-k invalid")
        topk[j] = labels
        hits[j] = np.fromiter((len(set(a.tolist()) & set(b.tolist())) for a, b in zip(labels, neighbors)), dtype=np.uint8, count=500)
    z_rec = hits < 10
    z_censor = z_rec[-1].copy()
    z_abs = np.logical_or(z_rec, z_censor[None, :])
    np.savez_compressed(array_path, query_ids=query_ids, action_grid=np.asarray(required_actions, dtype=np.int32),
                        topk=topk, hits=hits, z_rec=z_rec, z_censor=z_censor, z_abs=z_abs)
    return {'raw_failure_counts':z_rec.sum(axis=1).astype(int).tolist(),'absolute_failure_counts':z_abs.sum(axis=1).astype(int).tolist()}

def response_evaluate(query_ids, source, index_path, build_receipt, protocol, array_path, neighbors, required_actions, stem, faiss, h5py):
    order = np.argsort(query_ids)
    with h5py.File(source, "r") as handle:
        train = handle["train"]
        sorted_vectors = np.asarray(train[query_ids[order]], dtype=np.float32)
    queries = np.ascontiguousarray(sorted_vectors[np.argsort(order)])
    index = faiss.read_index(str(index_path))
    if index.ntotal != build_receipt["effective_base_count"]:
        raise ValueError("Faiss index cardinality mismatch")
    core = faiss.downcast_index(index.index)
    topk = np.empty((len(required_actions), 1000, 10), dtype=np.int64)
    hits = np.empty((len(required_actions), 1000), dtype=np.uint8)
    for j, action in enumerate(required_actions):
        core.hnsw.efSearch = action
        _, labels = index.search(queries, 10)
        if labels.shape != (1000, 10) or np.any(labels < 0):
            raise ValueError("Native Faiss top-k invalid")
        topk[j] = labels
        hits[j] = np.fromiter((len(set(a.tolist()) & set(b.tolist())) for a, b in zip(labels, neighbors)), dtype=np.uint8, count=1000)
    recall = hits.astype(np.float64) / 10.0
    z_rec = recall < 0.95
    z_censor = z_rec[-1].copy()
    z_abs = np.logical_or(z_rec, z_censor[None, :])
    np.savez_compressed(array_path, query_ids=query_ids, action_grid=np.asarray(required_actions, dtype=np.int32),
                        topk=topk, hits=hits, recall=recall, z_rec=z_rec, z_censor=z_censor, z_abs=z_abs)
    return {'raw_failure_counts':z_rec.sum(axis=1).astype(int).tolist(),'absolute_failure_counts':z_abs.sum(axis=1).astype(int).tolist()}

def select_dataset(dataset, responses, source_rows):
    direction_rows=[]
    global_rows=[]
    for target_seed in SEEDS:
        for target_history in HISTORIES:
            tid = build_id(target_seed, target_history)
            response = responses[tid]
            z_abs = response["z_abs"]
            global_ucbs = [cp_upper(int(z_abs[j].sum()), 500, 0.05 / 9) for j in range(9)]
            qualified = [j for j, value in enumerate(global_ucbs) if value <= 0.05]
            gj = qualified[0] if qualified else 8
            global_rows.append({
                "dataset": dataset,
                "target_build_id": tid,
                "arm": "target_global",
                **arm(GRID[gj], None, int(z_abs[gj].sum()), global_ucbs[gj], response["array_sha"], bool(qualified)),
                "selection_cp_delta_per_action": 0.05 / 9,
                "certification_status": "NOT_ACCESSED",
            })
            for source_seed in SEEDS:
                for source_history in HISTORIES:
                    sid = build_id(source_seed, source_history)
                    if sid == tid:
                        continue
                    source = next(r for r in source_rows if (r["dataset"], r["seed"], r["history"]) == (dataset, source_seed, source_history))
                    source_ef = int(source["selected_source_action"])
                    source_j = GRID.index(source_ef)
                    rungs = []
                    seen = set()
                    for shift in range(4):
                        j = min(source_j + shift, 8)
                        if GRID[j] in seen:
                            continue
                        seen.add(GRID[j])
                        failures = int(z_abs[j].sum())
                        ucb = cp_upper(failures, 500, 0.05 / 4)
                        rungs.append(arm(GRID[j], shift, failures, ucb, response["array_sha"], ucb <= 0.05))
                    selected = next((r for r in rungs if r["eligible_selection_screen"]), None)
                    selected = selected if selected is not None else arm(
                        GRID[-1], None, int(z_abs[-1].sum()), cp_upper(int(z_abs[-1].sum()), 500, 0.05 / 4),
                        response["array_sha"], False,
                    )
                    source_reuse = next(r for r in rungs if r["shift"] == 0)
                    one_j = min(source_j + 1, 8)
                    one_fail = int(z_abs[one_j].sum())
                    one_rung = arm(GRID[one_j], 1, one_fail, cp_upper(one_fail, 500, 0.05 / 4), response["array_sha"], cp_upper(one_fail, 500, 0.05 / 4) <= 0.05)
                    direction_rows.append({
                        "dataset": dataset,
                        "source_build_id": sid,
                        "target_build_id": tid,
                        "source_design_action": source_ef,
                        "source_reuse": {"arm": "source_reuse", **source_reuse},
                        "one_rung": {"arm": "one_rung", **one_rung},
                        "selected_ladder": {"arm": "selected_ladder", **selected},
                        "ladder_rungs": rungs,
                        "selection_cp_delta_per_shift": 0.05 / 4,
                        "fallback_candidate_if_no_eligible_rung": not any(r["eligible_selection_screen"] for r in rungs),
                        "certification_status": "NOT_ACCESSED",
                    })
    return {'directed_pair_actions':direction_rows,'target_global_actions':global_rows}

def certify_dataset(dataset, response_by_target, action_lock):
    decisions=[]
    for tid, (z_by_action, response_sha) in response_by_target.items():
        endpoint_failures = int(z_by_action[ENDPOINT].sum())
        endpoint_ucb = cp_upper(endpoint_failures, 500, ENDPOINT_DELTA)
        endpoint_ok = endpoint_ucb <= RISK_LIMIT
        decisions.append({
            "dataset": dataset,
            "source_build_id": None,
            "target_build_id": tid,
            "arm": "fixed_endpoint",
            "candidate_efSearch": ENDPOINT,
            "candidate_failures": endpoint_failures,
            "candidate_cp_ucb": endpoint_ucb,
            "candidate_delta": ENDPOINT_DELTA,
            "endpoint_failures": endpoint_failures,
            "endpoint_cp_ucb": endpoint_ucb,
            "endpoint_delta": ENDPOINT_DELTA,
            "candidate_qualified": endpoint_ok,
            "endpoint_qualified": endpoint_ok,
            "decision": "EXECUTE_ENDPOINT" if endpoint_ok else "ABSTAIN",
            "execute_efSearch": ENDPOINT if endpoint_ok else None,
            "response_sha256": response_sha,
        })
        global_row = next(row for row in action_lock["target_global_actions"] if row["dataset"] == dataset and row["target_build_id"] == tid)
        decisions.append(decide(dataset, tid, None, "target_global", int(global_row["candidate_efSearch"]), z_by_action, response_sha))
        for direction in (row for row in action_lock["directed_pair_actions"] if row["dataset"] == dataset and row["target_build_id"] == tid):
            for key in ("source_reuse", "one_rung", "selected_ladder"):
                decisions.append(decide(dataset, tid, direction["source_build_id"], key,
                                        int(direction[key]["candidate_efSearch"]), z_by_action, response_sha))
    return decisions

