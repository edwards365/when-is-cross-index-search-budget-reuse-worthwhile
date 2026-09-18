#!/usr/bin/env python3
"""Validate and seal S3 target-certification evidence."""

import csv
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "results" / "sigmod_ea_postseal_uplift"
RAW = BASE / "s3_raw_faiss"
ANALYSIS = BASE / "s3_analysis"
PREREG = ROOT / "manifests" / "sigmod_ea_postseal_uplift_s3_preregistration.json"
ROLES = ROOT / "manifests" / "sigmod_ea_postseal_uplift_s2_query_roles.json"
DECISION = ROOT / "manifests" / "sigmod_ea_postseal_uplift_s3_decision.json"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


checks = {}
prereg = json.loads(PREREG.read_text(encoding="utf-8"))
roles = json.loads(ROLES.read_text(encoding="utf-8"))
checks["preregistration_precedes_access"] = prereg["status"] == "PREREGISTERED_BEFORE_QUERY_OR_TRUTH_ACCESS"
checks["role_manifest_hash"] = sha(ROLES) == prereg["s2_role_manifest_sha256"]
checks["frozen_policy_hash"] = sha(ROOT / prereg["source_policy"]) == prereg["source_policy_sha256"]
checks["index_count"] = len(prereg["faiss_indexes"]) == 48

raw_paths = sorted(RAW.glob("*.csv.gz"))
checks["raw_file_count"] = len(raw_paths) == 48
total_rows = 0
raw_complete = True
for path in raw_paths:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    total_rows += len(rows)
    keys = {(int(row["query_id"]), int(row["ef"])) for row in rows}
    order_keys = {(int(row["query_id"]), int(row["action_order"])) for row in rows}
    raw_complete &= len(rows) == 6000 and len(keys) == 6000 and len(order_keys) == 6000
    raw_complete &= all((int(row["query_id"]) < 500) == (row["role"] == "target_certification") for row in rows)
    raw_complete &= all(float(row["ndc"]) > 0 and float(row["wall_ns"]) > 0 for row in rows)
checks["raw_cube_complete"] = raw_complete and total_rows == 288000

for dataset in ("sift_100k", "arxiv_nomic_100k"):
    role = roles["roles"][dataset]
    cert = set(role["target_certification_ids"])
    evaluation = set(role["target_evaluation_ids"])
    checks[f"{dataset}_role_counts"] = len(cert) == 500 and len(evaluation) == 500
    checks[f"{dataset}_role_overlap_zero"] = not cert.intersection(evaluation)

with (ANALYSIS / "s3_pair_results.csv").open(encoding="utf-8", newline="") as handle:
    pairs = list(csv.DictReader(handle))
with (ANALYSIS / "s3_summary.csv").open(encoding="utf-8", newline="") as handle:
    summaries = list(csv.DictReader(handle))
analysis_decision = json.loads((ANALYSIS / "s3_decision.json").read_text(encoding="utf-8"))
checks["pair_count"] = len(pairs) == 1104
checks["all_executed_actions_certified"] = all(
    float(row["endpoint_cert_ucb"]) <= 0.05
    and (row["deployment"] != "DEPLOY_CANDIDATE" or float(row["candidate_cert_ucb"]) <= 0.05)
    for row in pairs
)
checks["evaluation_role_size"] = all(int(row["evaluation_n"]) == 500 for row in pairs)
checks["two_dataset_summary"] = len(summaries) == 2
checks["all_registered_gates_pass"] = analysis_decision["decision"] == "S3_GATE_PASS" and all(
    row[key] == "PASS"
    for row in summaries
    for key in ("gate_certification", "gate_evaluation_risk", "gate_mean_ndc", "gate_p95", "gate_robustness")
)
if not all(checks.values()):
    raise RuntimeError({key: value for key, value in checks.items() if not value})

integrity = {
    "status": "PASS",
    "checks": checks,
    "checks_passed": sum(checks.values()),
    "checks_total": len(checks),
    "raw_rows": total_rows,
}
(ANALYSIS / "s3_integrity_checks.json").write_text(json.dumps(integrity, indent=2) + "\n", encoding="utf-8")

metrics = {}
for row in summaries:
    metrics[row["dataset"]] = {
        key: (float(value) if key not in {"dataset", "wall_clock_status"} and not key.startswith("gate_") else value)
        for key, value in row.items()
    }
decision = {
    "schema_version": 1,
    "phase": "S3",
    "final_label": "S3_GATE_PASS_INDEPENDENT_TARGET_CERTIFICATION",
    "evidence_scope": "FROZEN_FAISS_SOURCE_POLICY_NEW_TARGET_CERTIFICATION_AND_EVALUATION_QUERIES",
    "parent_preregistration_commit": "ba9cd70",
    "preregistration_sha256": sha(PREREG),
    "role_manifest_sha256": sha(ROLES),
    "raw_files": len(raw_paths),
    "raw_rows": total_rows,
    "integrity_checks": f"{sum(checks.values())}/{len(checks)}",
    "metrics": metrics,
    "access": {
        "new_query_roles_accessed": ["target_certification", "target_evaluation"],
        "validation_dev_accessed": False,
        "formal_test_accessed": False,
        "reserved_truth_accessed": False,
        "new_index_builds": 0,
        "index_mutations": 0,
    },
    "wall_clock_scope": "EXPLORATORY_FIXED_MACHINE_INTERLEAVED",
    "next_phase": "S4_LIFECYCLE_AND_WALL_CLOCK_ELIGIBLE_NOT_STARTED",
}
DECISION.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")

inventory_rows = []
paths = [
    PREREG,
    ROLES,
    BASE / "s3_inputs" / "input_inventory.json",
    BASE / "s3_inputs" / "truth_access_log.json",
    *raw_paths,
    *(ANALYSIS / name for name in ("s3_pair_results.csv", "s3_target_build_results.csv", "s3_summary.csv", "s3_decision.json", "s3_integrity_checks.json")),
    DECISION,
    ROOT / "docs" / "sigmod_ea_postseal_uplift" / "S3_REPORT.md",
    *(ROOT / "scripts" / "sigmod_ea_postseal_uplift" / name for name in (
        "freeze_s3_execution.py",
        "prepare_s3_inputs.py",
        "s3_faiss_replay.py",
        "analyze_s3_target_cert.py",
        "check_s3.py",
    )),
]
for path in paths:
    inventory_rows.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)})
with (BASE / "s3_output_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(inventory_rows)
print(json.dumps({"status": "PASS", "checks": f"{sum(checks.values())}/{len(checks)}", "raw_rows": total_rows}))
