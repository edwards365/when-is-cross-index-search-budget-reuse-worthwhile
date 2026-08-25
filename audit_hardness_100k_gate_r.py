#!/usr/bin/env python3
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path("/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k")
OUT = ROOT / "results/hardness_portability_100k/gate_r"
RUNS = json.loads((OUT / "gate_r_runs.json").read_text())
DATASETS = ["sift_100k", "glove100_100k", "arxiv_nomic_100k"]
ORDERS = ["random", "lid_ascending", "lid_descending"]
EFS = [10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


evidence = []
failures = []
for dataset in DATASETS:
    for order in ORDERS:
        paths = [OUT / f"{dataset}__seed43__{order}__rep{rep}.csv.gz" for rep in (1, 2)]
        signatures = []
        for path in paths:
            rows = []
            with gzip.open(path, "rt", newline="") as handle:
                reader = csv.DictReader(handle)
                required = {"dataset", "query_id", "ef_search", "returned_top10_ids", "recall_at_10", "exact_ndc", "graph_hash", "native_or_instrumented", "success"}
                if not required.issubset(reader.fieldnames or []):
                    failures.append(f"schema:{path.name}")
                for row in reader:
                    rows.append((int(row["query_id"]), int(row["ef_search"]), row["returned_top10_ids"], row["recall_at_10"], row["exact_ndc"], row["graph_hash"], row["entry_point"], row["max_level"]))
                    if row["native_or_instrumented"] != "instrumented_verified_against_native_per_row" or row["success"] != "True":
                        failures.append(f"native:{path.name}")
            counts = Counter((r[0], r[1]) for r in rows)
            if len(rows) != 12000 or len(counts) != 12000 or set(q for q, _ in counts) != set(range(1000)) or set(e for _, e in counts) != set(EFS):
                failures.append(f"coverage:{path.name}")
            signatures.append(rows)
            evidence.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "rows": len(rows)})
        if signatures[0] != signatures[1]:
            failures.append(f"repeat:{dataset}:{order}")

if len(RUNS) != 9 or any(not r["repeat_deterministic"] or not r["native_instrumented_exact"] for r in RUNS):
    failures.append("gate_r_runs")

decision = {
    "schema_version": 1,
    "protocol": "Query Hardness Is Not Portable 100K",
    "status": "PASS_100K_REPRODUCTION_GATE" if not failures else "INVALID_100K_REPRODUCTION_FAILURE",
    "datasets": 3,
    "graph_configurations": 9,
    "determinism_repetitions": 2,
    "physical_rows": 216000,
    "unique_query_ef_cells": 108000,
    "native_instrumented_label_recall_ndc_exact": not failures,
    "graph_hash_repeat_exact": not failures,
    "missing_cells": 0 if not failures else None,
    "failures": failures,
    "evidence": evidence,
    "temporary_indexes_deleted": True,
    "formal_test_accessed": False,
}
path = ROOT / "manifests/hardness_portability_100k/reproduction_gate.json"
path.write_text(json.dumps(decision, indent=2) + "\n")
print(json.dumps({k: decision[k] for k in ["status", "graph_configurations", "physical_rows", "unique_query_ef_cells", "failures"]}, indent=2))
if failures:
    raise SystemExit(1)
