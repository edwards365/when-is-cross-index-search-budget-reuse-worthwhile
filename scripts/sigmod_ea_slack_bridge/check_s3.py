#!/usr/bin/env python3
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
results = root / "results" / "sigmod_ea_slack_bridge"


def read(name):
    with (results / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


sources = read("s3_source_policy.csv")
pairs = read("s3_pair_replay.csv")
summary = read("s3_summary.csv")
roles = json.loads((results / "s3_query_role_manifest.json").read_text())
checks = []


def add(name, condition, detail):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


add("source_rows", len(sources) == 96, len(sources))
add("pair_rows", len(pairs) == 8832, len(pairs))
add("summary_rows", len(summary) == 16, len(summary))
role_sets = {k: set(v) for k, v in roles["roles"].items()}
add("role_sizes", [len(v) for v in role_sets.values()] == [375, 94, 281], [len(v) for v in role_sets.values()])
add("roles_disjoint", sum(len(a & b) for i, a in enumerate(role_sets.values()) for b in list(role_sets.values())[i + 1 :]) == 0, "zero overlap")
add("roles_cover_750", len(set.union(*role_sets.values())) == 750, len(set.union(*role_sets.values())))
add("evidence_role_limited", roles["evidence_level"] == "POST_HOC_ROLE_LIMITED", roles["evidence_level"])
add("all_source_qualification_valid", all(r["decision"] != "SOURCE_QUALIFIED" or float(r["source_certification_ucb_bonferroni"]) <= 0.05 for r in sources), "qualified UCB <= 0.05")

source_actions = {(r["operator"], r["dataset"], r["source_build"]): r["chosen_action"] for r in sources}
add(
    "source_action_invariant_across_targets",
    all(r["selected_action"] == source_actions[(r["operator"], r["dataset"], r["source_build"])] for r in pairs),
    "one frozen action per source",
)
grids = {"hnswlib": {10, 20, 40, 80, 120, 200}, "faiss_hnsw": {16, 32, 64, 128, 256, 512}}
add("native_actions_only", all(int(r["executed_action"]) in grids[r["operator"]] for r in pairs), "registered grids")
for r in summary:
    partition = int(r["target_qualified_pairs"]) + int(r["target_indeterminate_pairs"]) + int(r["target_confidently_above_delta_pairs"])
    add(f"partition_{r['operator']}_{r['dataset']}_{r['lane']}", partition == 552, partition)
    if r["operator"] == "faiss_hnsw":
        add(f"faiss_cost_semantics_{r['dataset']}_{r['lane']}", r["ndc_status"] == "NDC_NOT_ESTIMABLE_BATCH_CUMULATIVE", r["ndc_status"])
    else:
        add(f"hnsw_cost_semantics_{r['dataset']}_{r['lane']}", r["ndc_status"] == "ESTIMABLE" and float(r["target_ndc_mean"]) > 0, r["ndc_status"])

passed = sum(c["pass"] for c in checks)
report = {"status": "PASS" if passed == len(checks) else "FAIL", "checks_passed": passed, "checks_total": len(checks), "checks": checks}
(results / "s3_validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: report[k] for k in ("status", "checks_passed", "checks_total")}, indent=2))
raise SystemExit(0 if report["status"] == "PASS" else 1)
