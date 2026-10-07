"""Historical policy arithmetic; paths supplied by new verified array receipts."""
import hashlib
from pathlib import Path
import numpy as np
from scipy.stats import beta

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check(path, expected):
    if digest(path) != expected:
        raise ValueError("SHA mismatch: " + str(path))


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



def certify(audit, policy):
    grid=policy["action_grid"]; build_ids=policy["build_ids"]
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
    return rows

def evaluate(audit, policy, lock):
    grid=policy["action_grid"]; build_ids=policy["build_ids"]
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
    return rows
