#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "sigmod_ea_slack_bridge"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


role_path = ROOT / "manifests" / "graph_anns_e4_role_manifest.json"
roles = json.loads(role_path.read_text())["roles"]
source_policy_path = OUT / "s3_source_policy.csv"
source_policies = read_csv(source_policy_path)
hnsw_manifest_path = ROOT / "results" / "graph_anns_e4" / "build_manifest.csv"
faiss_registry_path = ROOT / "results" / "graph_anns_iclr_phase1_1_repair" / "faiss100k_reuse_registry.csv"
hnsw = read_csv(hnsw_manifest_path)
faiss = read_csv(faiss_registry_path)

fresh_roles = {}
for dataset in ("sift_100k", "arxiv_nomic_100k"):
    ids = list(map(int, roles[dataset]["future_replication_ids"]))
    if len(ids) != 1000 or len(set(ids)) != 1000:
        raise RuntimeError("invalid future-replication role")
    cert, evaluation = ids[:500], ids[500:]
    fresh_roles[dataset] = {
        "fresh_source_certification_ids": cert,
        "fresh_target_evaluation_ids": evaluation,
        "certification_sha256": hashlib.sha256(json.dumps(cert, separators=(",", ":")).encode()).hexdigest(),
        "evaluation_sha256": hashlib.sha256(json.dumps(evaluation, separators=(",", ":")).encode()).hexdigest(),
        "overlap": len(set(cert) & set(evaluation)),
    }

manifest = {
    "phase": "S4",
    "status": "FROZEN_BEFORE_FUTURE_VECTOR_OR_TRUTH_ACCESS",
    "parent_commit": "5a2b8d7901dfc42b581cf52e0d5e549b3de26e47",
    "evidence_target": "FRESH_QUERY_CONFIRMATION",
    "role_source": str(role_path),
    "role_source_sha256": sha(role_path),
    "roles": fresh_roles,
    "source_policy_sha256": sha(source_policy_path),
    "source_policies": source_policies,
    "hnsw_build_manifest_sha256": sha(hnsw_manifest_path),
    "hnsw_indexes": [
        {
            "dataset": r["dataset"],
            "build_id": r["build_id"],
            "path": f"/home/wlk/data500/graph_anns_e4/raw/{r['build_id']}/index.bin",
            "sha256": r["index_sha256"],
            "bytes": int(r["index_size_bytes"]),
        }
        for r in hnsw
    ],
    "faiss_registry_sha256": sha(faiss_registry_path),
    "faiss_indexes": [
        {
            "dataset": r["dataset"],
            "build_id": r["build_id"],
            "path": r["source_index"],
            "sha256": r["index_sha256"],
        }
        for r in faiss
    ],
    "fixed": {
        "risk_event": "Recall@10 < 0.95",
        "delta": 0.05,
        "candidate_alpha": 0.025,
        "endpoint_alpha": 0.025,
        "lanes": ["source_selected_plus_0", "source_selected_plus_1", "source_selected_plus_2", "endpoint"],
        "bootstrap_replicates": 5000,
        "bootstrap_seed": 991,
        "base_count": 100000,
        "truth_k": 10,
    },
    "prohibitions": [
        "no index construction or mutation",
        "no target-evaluation-driven selection",
        "no requested-ef-as-NDC substitution",
        "no validation-dev or formal-test access",
        "no W6 edit",
    ],
}
if len(manifest["hnsw_indexes"]) != 48 or len(manifest["faiss_indexes"]) != 48:
    raise RuntimeError("expected 48 indexes per implementation")
(OUT / "s4_fresh_preregistration.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"status": manifest["status"], "hnsw_indexes": 48, "faiss_indexes": 48}, indent=2))
