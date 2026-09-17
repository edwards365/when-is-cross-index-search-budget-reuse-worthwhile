#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "sigmod_ea_slack_bridge"


def rows(name):
    with (RESULTS / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


summary = rows("s1_slack_summary.csv")
targets = rows("s1_per_target.csv")
diagnostics = rows("s1_semantic_diagnostics.csv")
inventory = rows("s1_input_inventory.csv")

expected_primary = {
    ("hnswlib", "sift_100k"): 0.21547826086956523,
    ("hnswlib", "arxiv_nomic_100k"): 0.17173671497584542,
    ("faiss_hnsw", "sift_100k"): 0.23599275362318842,
    ("faiss_hnsw", "arxiv_nomic_100k"): 0.17765700483091787,
}

checks = []


def check(name, condition, detail):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


check("summary_row_count", len(summary) == 20, len(summary))
check("per_target_row_count", len(targets) == 480, len(targets))
check("diagnostic_row_count", len(diagnostics) == 4, len(diagnostics))
check("inventory_row_count", len(inventory) == 96, len(inventory))
check("inventory_unique_files", len({r["path"] for r in inventory}) == 96, "unique paths")
check("inventory_unique_hashes_nonempty", all(len(r["sha256"]) == 64 for r in inventory), "64-char SHA256")

by_key = {(r["operator"], r["dataset"], r["lane"]): r for r in summary}
for key, expected in expected_primary.items():
    actual = float(by_key[key + ("first_plus_0",)]["incremental_risk"])
    check(f"frozen_primary_{key[0]}_{key[1]}", abs(actual - expected) <= 1e-12, {"actual": actual, "expected": expected})
    base = actual
    for lane in ("first_plus_1", "first_plus_2"):
        value = float(by_key[key + (lane,)]["incremental_risk"])
        check(f"risk_nonincrease_{key[0]}_{key[1]}_{lane}", value <= base + 1e-15, {"lane": value, "base": base})
    lower = float(by_key[key + ("first_plus_2",)]["increment_ci_low"])
    check(f"plus2_ci_positive_{key[0]}_{key[1]}", lower > 0.0, lower)

for row in diagnostics:
    check(
        f"stable_ge_first_{row['operator']}_{row['dataset']}",
        row["stable_ge_first_when_both_finite"].lower() == "true",
        row["stable_ge_first_when_both_finite"],
    )

for row in summary:
    if row["operator"] == "faiss_hnsw":
        check(
            f"faiss_ndc_not_estimable_{row['dataset']}_{row['lane']}",
            row["ndc_status"] == "NDC_NOT_ESTIMABLE_BATCH_CUMULATIVE"
            and row["target_ndc_mean"] == "NOT_ESTIMABLE"
            and row["target_ndc_p95"] == "NOT_ESTIMABLE",
            row["ndc_status"],
        )
    else:
        check(
            f"hnsw_ndc_finite_{row['dataset']}_{row['lane']}",
            float(row["target_ndc_mean"]) > 0 and float(row["target_ndc_p95"]) > 0,
            {"mean": row["target_ndc_mean"], "p95": row["target_ndc_p95"]},
        )

for row in diagnostics:
    check(
        f"dataset_shape_{row['operator']}_{row['dataset']}",
        int(row["queries"]) == 750 and int(row["builds"]) == 24,
        {"queries": row["queries"], "builds": row["builds"]},
    )

passed = sum(c["pass"] for c in checks)
report = {
    "status": "PASS" if passed == len(checks) else "FAIL",
    "checks_passed": passed,
    "checks_total": len(checks),
    "summary_sha256": hashlib.sha256((RESULTS / "s1_slack_summary.csv").read_bytes()).hexdigest(),
    "checks": checks,
}
(RESULTS / "s1_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("status", "checks_passed", "checks_total", "summary_sha256")}, indent=2))
raise SystemExit(0 if report["status"] == "PASS" else 1)
