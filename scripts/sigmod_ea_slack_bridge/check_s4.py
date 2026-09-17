#!/usr/bin/env python3
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "sigmod_ea_slack_bridge"


def rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


checks = []


def check(name, condition, detail=""):
    checks.append({"check": name, "pass": bool(condition), "detail": str(detail)})


manifest = json.loads((RES / "s4_fresh_preregistration.json").read_text())
check("fresh_role_overlap_zero", all(int(v["overlap"]) == 0 for v in manifest["roles"].values()))
check("future_access_frozen_before_replay", manifest["status"] == "FROZEN_BEFORE_FUTURE_VECTOR_OR_TRUTH_ACCESS")
check("hnsw_index_count", len(manifest["hnsw_indexes"]) == 48)
check("faiss_index_count", len(manifest["faiss_indexes"]) == 48)

for family in ("hnsw", "faiss"):
    files = sorted((RES / f"s4_raw_{family}").glob("*.csv.gz"))
    check(f"{family}_raw_file_count", len(files) == 48, len(files))
    for path in files:
        with gzip.open(path, "rt", newline="") as handle:
            rr = list(csv.DictReader(handle))
        check(f"{family}_{path.stem}_rows", len(rr) == 6000, len(rr))
        check(f"{family}_{path.stem}_ndc_positive", all(float(r["ndc"]) > 0 for r in rr))

source = rows(RES / "s4_source_certification.csv")
pairs = rows(RES / "s4_pair_results.csv")
summary = rows(RES / "s4_summary.csv")
check("source_row_count", len(source) == 384, len(source))
check("pair_row_count", len(pairs) == 8832, len(pairs))
check("summary_row_count", len(summary) == 16, len(summary))
check("source_cert_n_500", all(int(r["certification_n"]) == 500 for r in source))
check("target_eval_n_500", all(int(r["target_n"]) == 500 for r in pairs))
check("legal_action_grid", all(int(r["executed_action"]) in {10,20,40,80,120,200,16,32,64,128,256,512} for r in pairs))
check("no_target_tuning", all(r["deployment"] in {"DEPLOY_CANDIDATE","FALLBACK_ENDPOINT","NO_CERTIFIED_ACTION"} for r in pairs))
check("pair_state_partition", all(int(r["target_qualified_pairs"])+int(r["target_indeterminate_pairs"])+int(r["target_confidently_above_delta_pairs"]) == 552 for r in summary))
check("summary_ndc_positive", all(float(r["ndc_mean"]) > 0 and float(r["endpoint_ndc_mean"]) > 0 for r in summary))
check("risk_below_delta_all_lanes", all(float(r["target_risk_ci_high"]) < 0.05 for r in summary))
check("stable_tail_not_deployed", json.loads((RES / "s4_decision.json").read_text())["stable_tail"] == "NON_DEPLOYABLE_TRUTH_DEPENDENT_NOT_USED")

inventory = []
for path in sorted((RES / "s4_inputs").glob("*")):
    if path.is_file():
        inventory.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
check("input_inventory_count", len(inventory) == 11, len(inventory))

result = {"phase": "S4", "passed": sum(x["pass"] for x in checks), "total": len(checks), "all_pass": all(x["pass"] for x in checks), "checks": checks, "input_inventory": inventory}
(RES / "s4_validation.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("phase", "passed", "total", "all_pass")}, indent=2))
raise SystemExit(0 if result["all_pass"] else 1)
