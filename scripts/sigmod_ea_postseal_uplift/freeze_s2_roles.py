#!/usr/bin/env python3
"""Freeze post-seal S2 query IDs without reading query vectors or truth."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "sigmod_ea_postseal_uplift"
MANIFEST = ROOT / "manifests" / "sigmod_ea_postseal_uplift_s2_query_roles.json"
WINDOW = range(500_000, 600_000)
DATASETS = {
    "sift_100k": {
        "seed": 991,
        "train_rows": 1_000_000,
        "source": "data/raw/sift-128-euclidean.hdf5",
        "source_sha256": "dd6f0a6ed6b7ebb8934680f861a33ed01ff33991eaee4fd60914d854a0ca5984",
        "external_roles": Path("/home/wlk/data500/graph_anns_faiss_external_validity/run/roles/sift_100k/role_ids.csv"),
    },
    "arxiv_nomic_100k": {
        "seed": 992,
        "train_rows": 1_344_643,
        "source": "data/raw/arxiv-nomic-768-normalized.hdf5",
        "source_sha256": "8be0993b978b0d0ef023d21d878251a5ed09e058adb25994553c08388d37d414",
        "external_roles": Path("/home/wlk/data500/graph_anns_faiss_external_validity/run/roles/arxiv_nomic_100k/role_ids.csv"),
    },
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def sha_ids(values: list[int]) -> str:
    return sha_bytes(json.dumps(values, separators=(",", ":")).encode())


def collect_id_lists(node, key="") -> set[int]:
    found: set[int] = set()
    if isinstance(node, dict):
        for child_key, value in node.items():
            found.update(collect_id_lists(value, child_key))
    elif (
        isinstance(node, list)
        and (key.lower().endswith("ids") or key.lower().endswith("_id"))
        and all(isinstance(v, int) for v in node)
    ):
        found.update(node)
    return found


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    registry_paths = sorted(
        set(ROOT.glob("manifests/**/*manifest*.json"))
        | set(ROOT.glob("manifests/**/*prereg*.json"))
        | set(ROOT.glob("results/**/*manifest*.json"))
        | set(ROOT.glob("results/**/*prereg*.json"))
        | set(ROOT.glob("results/**/*role*.json"))
        | set(ROOT.glob("results/**/*access*.json"))
    )
    registry_paths = [path for path in registry_paths if path != MANIFEST]
    tracked_ids: set[int] = set()
    registry_hashes = []
    for path in registry_paths:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        tracked_ids.update(collect_id_lists(doc))
        registry_hashes.append({"path": str(path.relative_to(ROOT)), "sha256": sha_file(path)})

    roles = {}
    audit_rows = []
    snapshots = []
    snapshot_rows = []
    for dataset, cfg in DATASETS.items():
        source = ROOT / cfg["source"]
        if not source.is_file():
            raise FileNotFoundError(source)
        if cfg["train_rows"] <= WINDOW.stop:
            raise RuntimeError(f"candidate window exceeds {dataset} train rows")
        external_path = cfg["external_roles"]
        external_rows = list(csv.DictReader(external_path.open(encoding="utf-8", newline="")))
        external_ids = {int(row["source_id"]) for row in external_rows}
        for row in external_rows:
            snapshot_rows.append(
                {"dataset": dataset, "role": row["role"], "source_id": int(row["source_id"])}
            )
        excluded = tracked_ids | external_ids
        eligible = [value for value in WINDOW if value not in excluded]
        rng = random.Random(cfg["seed"])
        selected = rng.sample(eligible, 1000)
        cert, evaluation = selected[:500], selected[500:]
        if set(cert) & set(evaluation) or set(selected) & excluded:
            raise RuntimeError(f"role overlap for {dataset}")
        roles[dataset] = {
            "namespace": "source_hdf5_train_row_index",
            "candidate_window": [WINDOW.start, WINDOW.stop],
            "allocation_seed": cfg["seed"],
            "target_certification_ids": cert,
            "target_evaluation_ids": evaluation,
            "certification_sha256": sha_ids(cert),
            "evaluation_sha256": sha_ids(evaluation),
            "within_dataset_overlap": 0,
            "known_registered_overlap": 0,
        }
        audit_rows.append(
            {
                "dataset": dataset,
                "candidate_window_start": WINDOW.start,
                "candidate_window_stop_exclusive": WINDOW.stop,
                "known_json_registry_ids_in_window": len(tracked_ids & set(WINDOW)),
                "faiss_external_role_ids_in_window": len(external_ids & set(WINDOW)),
                "eligible_after_exclusion": len(eligible),
                "certification_count": len(cert),
                "evaluation_count": len(evaluation),
                "within_dataset_overlap": 0,
                "known_registered_overlap": 0,
            }
        )
        snapshots.append(
            {
                "dataset": dataset,
                "source": str(external_path),
                "sha256": sha_file(external_path),
                "rows": len(external_rows),
            }
        )

    snapshot_path = OUT / "s2_faiss_external_role_snapshot.csv"
    with snapshot_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "role", "source_id"])
        writer.writeheader()
        writer.writerows(snapshot_rows)
    with (OUT / "s2_provisioning_audit.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)

    manifest = {
        "schema_version": 1,
        "phase": "S2",
        "status": "IDS_FROZEN_VECTORS_AND_TRUTH_UNACCESSED",
        "parent_s5r3": "49bd2910b122293f43c1a9063364a038fa4417b8",
        "resolves_blocked_audit_commit": "7c51328b0cf7ffb5e5d2bd1337f769d710c7e702",
        "definition_of_fresh": "not previously assigned or accessed as a query or truth role; rows may have appeared as index data in separate scale experiments",
        "sources": {
            dataset: {
                "path": cfg["source"],
                "sha256": cfg["source_sha256"],
                "train_rows": cfg["train_rows"],
                "metadata_source": "results/graph_anns_iclr_phase1_1/source_registry.csv",
            }
            for dataset, cfg in DATASETS.items()
        },
        "audited_json_registries": registry_hashes,
        "faiss_external_role_snapshots": snapshots,
        "roles": roles,
        "fixed_s3_contract": {
            "policy": "faiss_source_selected_plus_1_from_s4",
            "builds_per_dataset": 24,
            "directed_pairs_per_dataset": 552,
            "risk_event": "Recall@10 < 0.95",
            "risk_threshold": 0.05,
            "candidate_alpha": 0.025,
            "endpoint_alpha": 0.025,
            "bootstrap_replicates": 5000,
            "bootstrap_seed": 991,
        },
        "access_firewall": {
            "new_query_vector_reads": 0,
            "new_truth_reads": 0,
            "new_ann_searches": 0,
            "new_index_builds": 0,
            "validation_dev_accessed": False,
            "formal_test_accessed": False,
            "reserved_truth_accessed": False,
        },
        "s3_status": "AUTHORIZED_NOT_STARTED",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "datasets": list(roles), "s3": manifest["s3_status"]}))


if __name__ == "__main__":
    main()
