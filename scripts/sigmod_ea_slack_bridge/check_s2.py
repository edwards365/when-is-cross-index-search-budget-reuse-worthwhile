#!/usr/bin/env python3
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
results = root / "results" / "sigmod_ea_slack_bridge"


def read(name):
    with (results / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


pairs = read("s2_certificate_pairs.csv")
summary = read("s2_certificate_summary.csv")
audits = read("s2_implication_audit.csv")
theory = read("s2_theory_contact.csv")
checks = []


def add(name, condition, detail):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


add("pair_row_count", len(pairs) == 11040, len(pairs))
add("summary_row_count", len(summary) == 40, len(summary))
add("audit_row_count", len(audits) == 4, len(audits))
add("all_implications_hold", all(int(r["implication_violations"]) == 0 for r in pairs), "zero violations")
add(
    "failure_bounded_by_stable_gap",
    all(int(r["target_failures"]) <= int(r["stable_gap_events"]) for r in pairs),
    "pairwise deterministic inequality",
)
for r in summary:
    partition = int(r["qualified_pairs"]) + int(r["indeterminate_pairs"]) + int(r["confidently_above_delta_pairs"])
    add(
        f"state_partition_{r['operator']}_{r['dataset']}_{r['lane']}_{r['allocation']}",
        partition == int(r["directed_pairs"]) == 552,
        partition,
    )
for r in audits:
    add(
        f"audit_pass_{r['operator']}_{r['dataset']}",
        r["status"] == "PASS" and int(r["finite_grid_implication_violations"]) == 0,
        r["status"],
    )
allowed = {
    "PROVED_UNDER_STATED_ASSUMPTIONS",
    "CLASSICAL_APPLICATION",
    "EMPIRICAL_CONTACT",
    "NOT_INSTANTIATED",
}
add("theory_status_vocabulary", all(r["status"] in allowed for r in theory), sorted({r["status"] for r in theory}))

passed = sum(c["pass"] for c in checks)
report = {
    "status": "PASS" if passed == len(checks) else "FAIL",
    "checks_passed": passed,
    "checks_total": len(checks),
    "checks": checks,
}
(results / "s2_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("status", "checks_passed", "checks_total")}, indent=2))
raise SystemExit(0 if report["status"] == "PASS" else 1)
