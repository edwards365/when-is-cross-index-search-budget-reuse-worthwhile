#!/usr/bin/env python3
"""Freeze the S3 execution manifest before query-vector or truth access."""

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
S2 = ROOT / "manifests" / "sigmod_ea_postseal_uplift_s2_query_roles.json"
S4 = ROOT / "results" / "sigmod_ea_slack_bridge" / "s4_fresh_preregistration.json"
POLICY = ROOT / "results" / "sigmod_ea_slack_bridge" / "s3_source_policy.csv"
OUT = ROOT / "manifests" / "sigmod_ea_postseal_uplift_s3_preregistration.json"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


s2 = json.loads(S2.read_text(encoding="utf-8"))
s4 = json.loads(S4.read_text(encoding="utf-8"))
policies = list(csv.DictReader(POLICY.open(encoding="utf-8", newline="")))
faiss_policy = [row for row in policies if row["operator"] == "faiss_hnsw"]
if s2["status"] != "IDS_FROZEN_VECTORS_AND_TRUTH_UNACCESSED":
    raise RuntimeError("S2 role gate is not frozen")
if len(faiss_policy) != 48 or len(s4["faiss_indexes"]) != 48:
    raise RuntimeError("expected 48 Faiss policy rows and indexes")
if sha(POLICY) != s4["source_policy_sha256"]:
    raise RuntimeError("source policy hash drift")

manifest = {
    "schema_version": 1,
    "phase": "S3",
    "status": "PREREGISTERED_BEFORE_QUERY_OR_TRUTH_ACCESS",
    "parent_commit": "c593dd6f9bcc9caa3c237cb96d2f92733f0badcb",
    "s2_role_manifest": str(S2.relative_to(ROOT)),
    "s2_role_manifest_sha256": sha(S2),
    "source_policy": str(POLICY.relative_to(ROOT)),
    "source_policy_sha256": sha(POLICY),
    "policy_rows": faiss_policy,
    "faiss_registry_sha256": s4["faiss_registry_sha256"],
    "faiss_indexes": s4["faiss_indexes"],
    "roles": s2["roles"],
    "fixed": {
        "candidate_lane": "source_selected_plus_1",
        "grid": [16, 32, 64, 128, 256, 512],
        "target_certification_n": 500,
        "target_evaluation_n": 500,
        "risk_event": "Recall@10 < 0.95",
        "risk_threshold": 0.05,
        "candidate_alpha": 0.025,
        "endpoint_alpha": 0.025,
        "bootstrap_replicates": 5000,
        "bootstrap_seed": 991,
        "inference_unit": "target_build",
        "timing_order": "deterministic_per_query_interleaving_seed_991",
        "threads": 1,
        "affinity": "cpu_0",
        "warmup_queries_per_action": 20,
    },
    "decision_rule": [
        "if endpoint CP-UCB > 0.05: NO_CERTIFIED_ACTION",
        "else if candidate CP-UCB <= 0.05: DEPLOY_CANDIDATE",
        "else: FALLBACK_ENDPOINT",
    ],
    "primary_gate": {
        "certification": "all executed actions independently certified with one-sided UCB <= 0.05",
        "evaluation_risk": "both datasets pooled risk <= 0.05",
        "mean_efficiency": "relative mean NDC saving CI lower > 0",
        "tail": "query-pooled p95 NDC ratio <= 1",
        "robustness": "LOBO and delete-largest-target-build retain positive mean saving",
    },
    "prohibitions": [
        "no policy, action, threshold, grid, or endpoint change after query access",
        "no evaluation-driven selection",
        "no index construction or mutation",
        "no validation-dev, formal-test, or reserved-truth access",
        "wall-clock remains exploratory unless the frozen timing controls hold",
    ],
}
OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": manifest["status"], "indexes": len(manifest["faiss_indexes"]), "policy_rows": len(faiss_policy)}))

