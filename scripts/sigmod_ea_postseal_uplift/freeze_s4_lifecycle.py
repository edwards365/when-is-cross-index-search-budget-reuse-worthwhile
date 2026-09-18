#!/usr/bin/env python3
"""Freeze S4 lifecycle accounting before deriving any S4 cost result."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "manifests/sigmod_ea_postseal_uplift_s4_preregistration.json"
INPUTS = [
    ROOT / "manifests/sigmod_ea_postseal_uplift_s3_decision.json",
    ROOT / "manifests/sigmod_ea_postseal_uplift_s3_preregistration.json",
    ROOT / "results/sigmod_ea_postseal_uplift/s3_analysis/s3_pair_results.csv",
    ROOT / "results/sigmod_ea_postseal_uplift/s3_analysis/s3_target_build_results.csv",
    ROOT / "results/sigmod_ea_postseal_uplift/s3_analysis/s3_summary.csv",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


decision = json.loads(INPUTS[0].read_text(encoding="utf-8"))
if decision["final_label"] != "S3_GATE_PASS_INDEPENDENT_TARGET_CERTIFICATION":
    raise RuntimeError("S3 gate is not closed")

payload = {
    "schema_version": 1,
    "phase": "S4",
    "status": "PREREGISTERED_BEFORE_S4_COST_DERIVATION",
    "parent_commit": "534e76b84ec63b8d7485d8233b4a0a05f630ba14",
    "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in INPUTS],
    "primary_currency": "faiss_hnsw_native_distance_computations",
    "registered_horizons": [1000, 10000, 100000, 1000000, 10000000],
    "fixed_accounting": {
        "base_rows_per_exact_label": 100000,
        "target_certification_labels": 500,
        "truth_distance_cost": "100000 * 500 per target truth set",
        "certification_search": "sum measured candidate and endpoint NDC; identical actions deduplicated",
        "serving_saving": "endpoint evaluation NDC minus executed-action evaluation NDC",
        "rebuild": "COMMON_CANCELS_SAME_TARGET_INDEX",
        "fallback": "already represented by executed_action",
        "control_extra_ndc": 0,
    },
    "scenarios": {
        "PAIRWISE_TARGET_CERTIFICATION": "one source-target deployment; target truth and required searches charged to that direction",
        "SHARED_TARGET_CERTIFICATION_23_SOURCES": "one target truth set and each unique required action replayed once, shared by 23 registered source policies",
    },
    "statistics": {
        "outer_unit": "target_build",
        "bootstrap_replicates": 5000,
        "seed": 991,
        "interval": 0.95,
        "robustness": ["LOBO", "delete_largest_net_saving_target_build"],
    },
    "gates": {
        "target_stage_ndc": "S3 gates pass and, on both datasets, N=1e6 net-NDC bootstrap lower bound, LOBO minimum, and delete-largest check are positive",
        "full_lifecycle": "requires measured source-policy acquisition plus target-stage terms; missing source terms force NOT_ESTIMABLE",
        "wall_clock": "truth/control wall time must be measured under a controlled protocol; otherwise only search-only timing is descriptive",
    },
    "scope_limits": [
        "source-policy acquisition NDC is unavailable in the historical Faiss response cube and is never set to zero",
        "exact-truth wall time was not recorded and is never inferred from NDC",
        "no new query, truth, index, action, or policy access is authorized",
        "no monetary or hardware-general wall-clock claim",
    ],
}
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": payload["status"], "inputs": len(payload["inputs"])}, indent=2))
