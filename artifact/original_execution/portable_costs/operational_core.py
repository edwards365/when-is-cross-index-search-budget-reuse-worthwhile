"""Exact original timed blocks, with explicit input and output bindings."""
import hashlib,json,os,resource,struct,time
from pathlib import Path
import numpy as np
import h5py
from scipy.stats import beta

ROLE_NAMES=("source_design","target_selection","target_certification","target_evaluation")
DATASETS=(("sift-1m-heldout","sift"),("arxiv-nomic-1.34m-heldout","arxiv"))

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()

def checked(path, expected):
    if sha(path) != expected:
        raise ValueError("SHA mismatch: " + str(path))

def fresh_ids(name, seed, available, counts):
    key = hashlib.sha256(f"{name}:{seed}".encode("ascii")).digest()
    generator = np.random.Generator(np.random.PCG64(int.from_bytes(key[:8], "little")))
    chosen = generator.choice(available, size=sum(counts.values()), replace=False)
    answer = {}
    cursor = 0
    for role in ROLE_NAMES:
        count = counts[role]
        answer[role] = np.sort(chosen[cursor:cursor + count]).astype(np.int64)
        cursor += count
    return answer

def scan_content(train, all_query_ids, all_roles):
    query_vectors = np.asarray(train[all_query_ids.tolist()], dtype=np.float32)
    known = {}
    query_duplicates = []
    for raw_id, vector in zip(all_query_ids.tolist(), query_vectors):
        digest = hashlib.sha256(vector.tobytes(order="C")).digest()
        if digest in known and np.array_equal(known[digest][1], vector):
            query_duplicates.append([known[digest][0], raw_id])
        else:
            known[digest] = (raw_id, vector.copy())
    query_set = set(all_query_ids.tolist())
    counterparts = []
    for begin in range(0, len(train), 2048):
        block = np.asarray(train[begin:begin + 2048], dtype=np.float32)
        for offset, vector in enumerate(block):
            raw_id = begin + offset
            if raw_id in query_set:
                continue
            digest = hashlib.sha256(vector.tobytes(order="C")).digest()
            prior = known.get(digest)
            if prior is not None and np.array_equal(prior[1], vector):
                counterparts.append([prior[0], raw_id, all_roles[prior[0]]])
        if begin == 0 or (begin // 2048 + 1) % 100 == 0:
            print(json.dumps({"content_scan_rows": min(begin + 2048, len(train)),
                              "total": len(train)}), flush=True)
    return query_duplicates, counterparts

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()

def check(path, expected):
    if digest(path) != expected:
        raise ValueError("SHA mismatch: " + str(path))

def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())

def cp_upper(failures, count):
    return 1.0 if failures == count else float(beta.ppf(.95, failures + 1, count - failures))

def load_role(audit, dataset, role, grid, build_ids):
    entry = next(x for x in audit["rows"] if x["dataset"] == dataset and x["role"] == role)
    path = Path(entry["array_path"])
    check(path, entry["array_sha256"])
    with np.load(path, allow_pickle=False) as data:
        ids = np.asarray(data["query_ids"], dtype=np.int64)
        hits = np.asarray(data["hits"], dtype=np.int16)
        ndc = np.asarray(data["ndc"], dtype=np.uint64)
        if data["action_grid"].tolist() != grid or data["build_ids"].tolist() != build_ids:
            raise ValueError("Audited action/build axis")
    if hits.shape != (len(build_ids), len(grid), len(ids)) or ndc.shape != hits.shape:
        raise ValueError("Audited matrix dimensions")
    safe = hits >= 10
    stable = np.logical_and.accumulate(safe[:, ::-1, :], axis=1)[:, ::-1, :]
    labels = np.where(stable.any(axis=1), stable.argmax(axis=1), len(grid)).astype(np.int16)
    return ids, hits, ndc, labels

def candidates(labels, target, grid_length):
    sources = [i for i in range(len(labels)) if i != target]
    chosen = np.max(labels[sources], axis=0)
    abstain = chosen == grid_length
    return np.where(abstain, grid_length - 1, chosen), abstain, sources

def role_firewall(repo, config_path, config, roles_path, e1b_path, roles, exclusions, output, ops):
    start = time.monotonic()
    receipt = {"schema_version": "icde2027-tcp-fresh-role-receipt-v1", "status": "RUNNING",
               "config_sha256": sha(config_path), "previous_roles_sha256": sha(roles_path),
               "previous_e1b_sha256": sha(e1b_path), "datasets": [],
               "forbidden_hdf5_datasets_not_accessed": config["forbidden_hdf5_datasets"]}
    arrays = {}
    try:
        with np.load(e1b_path, allow_pickle=False) as e1b:
            for name, prefix in DATASETS:
                prior = next(row for row in roles["datasets"] if row["name"] == name)
                old_ex = next(row for row in exclusions["datasets"] if row["name"] == name)
                source = repo / prior["relative_path"]
                checked(source, prior["source_sha256"])
                old_roles = {int(i): "old_" + role for role, ids in prior["roles"].items() for i in ids}
                e1b_roles = {int(i): "e1b_" + role for role in ROLE_NAMES for i in e1b[f"{prefix}_{role}_ids"]}
                if len(old_roles) != 2500 or len(e1b_roles) != 2500 or set(old_roles) & set(e1b_roles):
                    raise ValueError("Prior query ID partition")
                unavailable = set(old_roles) | set(e1b_roles) | set(old_ex["excluded_index_row_ids"])
                available = np.asarray(sorted(set(range(prior["train_shape"][0])) - unavailable), dtype=np.int64)
                new = fresh_ids(name, config["seed"], available, config["role_counts"])
                all_roles = dict(old_roles)
                all_roles.update(e1b_roles)
                for role in ROLE_NAMES:
                    for raw_id in new[role]:
                        raw_id = int(raw_id)
                        if raw_id in all_roles:
                            raise ValueError("Fresh role overlap")
                        all_roles[raw_id] = "new_" + role
                    arrays[f"{prefix}_{role}_ids"] = new[role]
                if len(all_roles) != 7500:
                    raise ValueError("All role count")
                with h5py.File(source, "r") as handle:
                    train = handle["train"]
                    if list(train.shape) != prior["train_shape"] or str(train.dtype) != "float32":
                        raise ValueError("Train shape/dtype")
                    query_duplicates, counterparts = scan_content(train, np.asarray(sorted(all_roles), dtype=np.int64), all_roles)
                if query_duplicates:
                    raise ValueError("Cross-role exact query-content duplicate; preserve failure")
                exclude = np.asarray(sorted({int(row[1]) for row in counterparts} | set(old_ex["excluded_index_row_ids"])), dtype=np.int64)
                arrays[f"{prefix}_base_exclusion_ids"] = exclude
                base_count = int(prior["train_shape"][0] - len(all_roles) - len(exclude))
                row = {"dataset": name, "train_sha256": prior["source_sha256"],
                       "new_role_ids": {role: new[role].tolist() for role in ROLE_NAMES},
                       "all_query_count": len(all_roles), "query_query_exact_duplicate_pairs": query_duplicates,
                       "query_base_exact_counterparts": counterparts,
                       "base_exclusion_ids": exclude.tolist(), "effective_base_count": base_count}
                receipt["datasets"].append(row)
                print(json.dumps({"dataset": name, "new_queries": 2500,
                                  "base_exclusions": len(exclude), "effective_base_count": base_count}), flush=True)
        array_path = output / "membership.npz"
        with array_path.open("xb") as stream:
            np.savez_compressed(stream, **arrays)
        receipt["membership_sha256"] = sha(array_path)
        receipt["membership_bytes"] = array_path.stat().st_size
        receipt["status"] = "PASS_NEW_ROLE_AND_CONTENT_FIREWALL_BEFORE_OUTCOME"
    except BaseException as error:
        receipt["status"] = "FAILED_STOP_DEPENDENT_GRAPH_WORK"
        receipt["failure_type"] = type(error).__name__
        receipt["failure_message"] = str(error)[:1000]
        raise
    finally:
        receipt["wall_seconds"] = time.monotonic() - start
        path = ops / "final.json"
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(receipt, stream, sort_keys=True, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
        print(json.dumps({"status": receipt["status"], "final_sha256": sha(path)}), flush=True)
    return receipt

def profiles(source, ids, old_row, folder, op_folder, record, policy, spec, config, plan, binary_path, metric, repo, args, subprocess):
    started = time.perf_counter_ns()
    try:
        t0 = time.perf_counter_ns()
        with h5py.File(source, "r") as handle:
            train = handle["train"]
            if list(train.shape) != old_row["train_shape"] or str(train.dtype) != "float32":
                raise ValueError("Train shape/dtype")
            vectors = np.ascontiguousarray(train[ids.tolist()], dtype=np.float32)
        record["query_read_ns"] = time.perf_counter_ns() - t0
        qbin = folder / "queries.qbin"
        t0 = time.perf_counter_ns()
        with qbin.open("xb") as stream:
            stream.write(b"E1AQ0001")
            stream.write(struct.pack("<QQ", len(ids), vectors.shape[1]))
            for raw_id, vector in zip(ids, vectors):
                stream.write(struct.pack("<q", int(raw_id)))
                stream.write(vector.astype("<f4", copy=False).tobytes())
            stream.flush()
            os.fsync(stream.fileno())
        record["query_export_fsync_ns"] = time.perf_counter_ns() - t0
        record["qbin_sha256"] = digest(qbin)
        record["qbin_bytes"] = qbin.stat().st_size
        env = dict(os.environ)
        for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            env[key] = "1"
        for build in policy["build_ids"]:
            pin = spec["graphs"][build]
            receipt_path = Path(pin["receipt_path"])
            check(receipt_path, pin["receipt_sha256"])
            graph_receipt = json.loads(receipt_path.read_bytes())
            if graph_receipt["status"] != "BUILT_NO_QUERY_OUTCOME_ACCESSED" or graph_receipt["effective_base_count"] != spec["base_count"]:
                raise ValueError("Graph receipt mismatch")
            index_path = Path(graph_receipt["index_path"])
            check(index_path, graph_receipt["index_sha256"])
            csv_path = folder / (build + ".csv")
            argv = [str(binary_path), str(index_path), str(qbin), metric,
                    ",".join(map(str, config["action_grid"])), str(len(ids)),
                    str(spec["base_count"]), str(csv_path)]
            t0 = time.perf_counter_ns()
            with (op_folder / (build + ".stdout")).open("x", encoding="utf-8") as stdout, (op_folder / (build + ".stderr")).open("x", encoding="utf-8") as stderr:
                observed = subprocess.run(argv, cwd=repo, env=env, stdout=stdout, stderr=stderr,
                                          timeout=plan["wall_seconds_per_graph"], check=False)
            unit = {"build": build, "index_sha256": graph_receipt["index_sha256"],
                    "receipt_sha256": pin["receipt_sha256"], "actual_exit_code": observed.returncode,
                    "elapsed_ns_operational_including_native_reload": time.perf_counter_ns() - t0,
                    "csv_path": str(csv_path), "csv_sha256": digest(csv_path) if csv_path.exists() else None,
                    "csv_bytes": csv_path.stat().st_size if csv_path.exists() else None}
            write_json(op_folder / (build + ".json"), unit)
            record["profiles"].append(unit)
            print(json.dumps({"dataset": args.dataset, "role": args.role,
                              "build": build, "exit": observed.returncode,
                              "csv_bytes": unit["csv_bytes"]}), flush=True)
            if observed.returncode or not csv_path.exists() or not csv_path.stat().st_size:
                raise RuntimeError("Native profile failed: " + build)
        record["status"] = "NATIVE_PROFILES_COMPLETE_AUDIT_PENDING"
    except BaseException as error:
        record["status"] = "FAILED_STOP_DEPENDENT_POLICY"
        record["failure_type"] = type(error).__name__
        record["failure_message"] = str(error)[:1000]
        raise
    finally:
        record["whole_unit_ns"] = time.perf_counter_ns() - started
        record["process_maxrss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        path = op_folder / "final.json"
        write_json(path, record)
        print(json.dumps({"dataset": args.dataset, "role": args.role,
                          "status": record["status"], "final_sha256": digest(path)}), flush=True)
    return record

def certification(ops, args, policy, audit, grid, build_ids, config_path, audit_path, config):
    decision_started_ns = time.perf_counter_ns()
    if args.phase == "certify":
        lock_path = ops / "certification_decision_lock.json"
        if lock_path.exists():
            raise FileExistsError("Certification already locked")
        rows = []
        for dataset in policy["datasets"]:
            ids, hits, ndc, labels = load_role(audit, dataset, "target_certification", grid, build_ids)
            if len(ids) != 500:
                raise ValueError("Certification role count")
            for t, target in enumerate(build_ids):
                selected, abstain, sources = candidates(labels, t, len(grid))
                q = np.arange(len(ids))
                endpoint_fail = hits[t, -1] < 10
                candidate_fail = np.logical_or(hits[t, selected, q] < 10, endpoint_fail)
                endpoint_ucb = cp_upper(int(endpoint_fail.sum()), len(ids))
                candidate_ucb = cp_upper(int(candidate_fail.sum()), len(ids))
                if endpoint_ucb > policy["risk_limit"]:
                    decision = "UNDEPLOYABLE"
                elif candidate_ucb <= policy["risk_limit"]:
                    decision = "TCP"
                else:
                    decision = "ENDPOINT"
                rows.append({"dataset": dataset, "target_build": target, "decision": decision,
                             "cert_endpoint_failures": int(endpoint_fail.sum()), "cert_endpoint_cp95_ucb": endpoint_ucb,
                             "cert_tcp_failures": int(candidate_fail.sum()), "cert_tcp_cp95_ucb": candidate_ucb,
                             "cert_tcp_abstentions": int(abstain.sum()),
                             "cert_mean_source_ndc_per_query": float(ndc[sources].sum(axis=(0, 1)).mean())})
        record = {"schema_version": "icde2027-tcp-fresh-certification-lock-v1",
                  "status": "DECISIONS_LOCKED_BEFORE_EVALUATION_ARRAY_READ",
                  "config_sha256": digest(config_path), "profile_audit_sha256": digest(audit_path),
                  "rows": rows, "target_builds": len(rows),
                  "claim_boundary": "Conditional per-graph descriptive certification; no global ANN guarantee",
                  "decision_compute_ns_including_audited_array_read": time.perf_counter_ns() - decision_started_ns}
        write_json(lock_path, record)
        print(json.dumps({"status": record["status"], "targets": len(rows),
                          "lock_sha256": digest(lock_path)}), flush=True)
    else:
        lock_path = ops / "certification_decision_lock.json"
        expected_lock_sha = config["decision_lock_sha256"]
        check(lock_path, expected_lock_sha)
        lock = json.loads(lock_path.read_bytes())
        if lock["status"] != "DECISIONS_LOCKED_BEFORE_EVALUATION_ARRAY_READ" or len(lock["rows"]) != 16:
            raise ValueError("Decision lock state")
        final_path = ops / "evaluation.json"
        if final_path.exists():
            raise FileExistsError("Evaluation already exists")
        rows = []
        for dataset in policy["datasets"]:
            ids, hits, ndc, labels = load_role(audit, dataset, "target_evaluation", grid, build_ids)
            if len(ids) != 1000:
                raise ValueError("Evaluation role count")
            for t, target in enumerate(build_ids):
                locked = next(r for r in lock["rows"] if r["dataset"] == dataset and r["target_build"] == target)
                selected, abstain, sources = candidates(labels, t, len(grid))
                q = np.arange(len(ids))
                endpoint_fail = hits[t, -1] < 10
                candidate_fail = np.logical_or(hits[t, selected, q] < 10, endpoint_fail)
                endpoint_ndc = ndc[t, -1].astype(np.float64)
                candidate_ndc = ndc[t, selected, q].astype(np.float64)
                source_ndc = ndc[sources].sum(axis=(0, 1)).astype(np.float64)
                deployed = locked["decision"] == "TCP"
                selected_fail = candidate_fail if deployed else endpoint_fail
                selected_ndc = candidate_ndc if deployed else endpoint_ndc
                rows.append({"dataset": dataset, "target_build": target, "decision": locked["decision"],
                             "eval_queries": len(ids), "eval_endpoint_failures": int(endpoint_fail.sum()),
                             "eval_tcp_candidate_failures": int(candidate_fail.sum()),
                             "eval_selected_failures_descriptive": int(selected_fail.sum()),
                             "eval_selected_risk_descriptive": float(selected_fail.mean()),
                             "eval_mean_selected_ndc": float(selected_ndc.mean()),
                             "eval_mean_endpoint_ndc": float(endpoint_ndc.mean()),
                             "eval_mean_source_history_ndc_per_query": float(source_ndc.mean()),
                             "eval_tcp_abstentions": int(abstain.sum()),
                             "eval_queries_with_positive_candidate_ndc_saving": int(np.count_nonzero(endpoint_ndc > candidate_ndc))})
        record = {"schema_version": "icde2027-tcp-fresh-evaluation-v1",
                  "status": "PROSPECTIVE_NEW_ROLE_EVALUATION_COMPLETE_DESCRIPTIVE_NOT_GLOBAL_GUARANTEE",
                  "config_sha256": digest(config_path), "decision_lock_sha256": expected_lock_sha,
                  "profile_audit_sha256": digest(audit_path), "rows": rows, "target_builds": len(rows),
                  "decision_compute_ns_including_audited_array_read": time.perf_counter_ns() - decision_started_ns,
                  "limitations": ["Query-specific source labels require exact truth and paid source profiles before service.",
                                  "Shared target graphs and query IDs induce dependence; target build is the outer unit.",
                                  "NDC is not wall time. Lifecycle conclusions require a separate matched time ledger."]}
        write_json(final_path, record)
        print(json.dumps({"status": record["status"], "targets": len(rows),
                          "evaluation_sha256": digest(final_path)}), flush=True)
    return record

