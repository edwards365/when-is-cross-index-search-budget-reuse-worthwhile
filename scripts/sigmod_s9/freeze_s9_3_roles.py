#!/usr/bin/env python3
"""Freeze S9-3 role IDs without reading vectors, truth, indexes, or responses."""

import csv
import hashlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "manifests" / "sigmod_s9_3_query_roles.json"
WINDOW = range(700_000, 850_000)
DATASETS = {
    "sift_100k": {
        "seed": 1991,
        "rows": 1_000_000,
        "source": "data/raw/sift-128-euclidean.hdf5",
        "source_sha256": "dd6f0a6ed6b7ebb8934680f861a33ed01ff33991eaee4fd60914d854a0ca5984",
        "external_roles": "/home/wlk/data500/graph_anns_faiss_external_validity/run/roles/sift_100k/role_ids.csv",
    },
    "arxiv_nomic_100k": {
        "seed": 1992,
        "rows": 1_344_643,
        "source": "data/raw/arxiv-nomic-768-normalized.hdf5",
        "source_sha256": "8be0993b978b0d0ef023d21d878251a5ed09e058adb25994553c08388d37d414",
        "external_roles": "/home/wlk/data500/graph_anns_faiss_external_validity/run/roles/arxiv_nomic_100k/role_ids.csv",
    },
}


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha_ids(values):
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def collect_id_lists(node, key=""):
    found = set()
    if isinstance(node, dict):
        for child_key, value in node.items():
            found.update(collect_id_lists(value, child_key))
    elif isinstance(node, list) and (key.lower().endswith("ids") or key.lower().endswith("_id")):
        if all(isinstance(value, int) for value in node):
            found.update(node)
    return found


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    paths = sorted(
        set(ROOT.glob("manifests/**/*.json"))
        | set(ROOT.glob("results/**/*manifest*.json"))
        | set(ROOT.glob("results/**/*prereg*.json"))
        | set(ROOT.glob("results/**/*role*.json"))
        | set(ROOT.glob("results/**/*access*.json"))
        | set(ROOT.glob("results/**/*.external_ids.json"))
    )
    registered_ids = set()
    registry = []
    for path in paths:
        if path == OUTPUT:
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        registered_ids.update(collect_id_lists(document))
        if path.name.endswith(".external_ids.json") and isinstance(document, list):
            registered_ids.update(value for value in document if isinstance(value, int))
        registry.append({"path": str(path.relative_to(ROOT)), "sha256": sha_file(path)})

    roles = {}
    audits = []
    for dataset, config in DATASETS.items():
        source = ROOT / config["source"]
        if not source.is_file() or sha_file(source) != config["source_sha256"]:
            raise RuntimeError(f"source missing or hash drift: {dataset}")
        external_path = Path(config["external_roles"])
        external_ids = {
            int(row["source_id"])
            for row in csv.DictReader(external_path.open(encoding="utf-8", newline=""))
        }
        excluded = registered_ids | external_ids
        eligible = [value for value in WINDOW if value not in excluded]
        chosen = random.Random(config["seed"]).sample(eligible, 1500)
        source_design = chosen[:500]
        target_certification = chosen[500:1000]
        target_evaluation = chosen[1000:]
        role_sets = list(map(set, (source_design, target_certification, target_evaluation)))
        overlaps = [len(role_sets[i] & role_sets[j]) for i in range(3) for j in range(i + 1, 3)]
        known_overlap = len(set(chosen) & excluded)
        if any(overlaps) or known_overlap:
            raise RuntimeError(f"role firewall failed: {dataset}")
        roles[dataset] = {
            "namespace": "source_hdf5_train_row_index",
            "candidate_window": [WINDOW.start, WINDOW.stop],
            "allocation_seed": config["seed"],
            "source_design_ids": source_design,
            "target_certification_ids": target_certification,
            "target_evaluation_ids": target_evaluation,
            "source_design_sha256": sha_ids(source_design),
            "target_certification_sha256": sha_ids(target_certification),
            "target_evaluation_sha256": sha_ids(target_evaluation),
            "pairwise_role_overlaps": overlaps,
            "known_registered_overlap": known_overlap,
        }
        audits.append({
            "dataset": dataset,
            "eligible_ids": len(eligible),
            "registered_ids_in_window": len(registered_ids & set(WINDOW)),
            "external_ids_in_window": len(external_ids & set(WINDOW)),
            "pairwise_role_overlaps": overlaps,
            "known_registered_overlap": known_overlap,
        })
    payload = {
        "schema_version": 1,
        "phase": "S9-3",
        "status": "FROZEN_BEFORE_VECTOR_TRUTH_INDEX_OR_RESPONSE_ACCESS",
        "parent_commit": "dbc2f287e8b7a8dfcef0d3c1accc640277d624a7",
        "definition_of_fresh": "not present in any audited machine-readable registered role; source rows are outside the first-100K index base",
        "sources": {
            dataset: {"path": config["source"], "sha256": config["source_sha256"], "train_rows": config["rows"]}
            for dataset, config in DATASETS.items()
        },
        "audited_registries": registry,
        "roles": roles,
        "audit": audits,
        "access_firewall": {
            "new_query_vector_reads": 0,
            "new_truth_reads": 0,
            "new_ann_searches": 0,
            "new_index_builds": 0,
            "validation_dev_accessed": False,
            "formal_test_accessed": False,
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "audit": audits}, indent=2))


if __name__ == "__main__":
    main()
