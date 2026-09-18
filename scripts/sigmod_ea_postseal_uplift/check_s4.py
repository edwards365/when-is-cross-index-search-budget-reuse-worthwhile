#!/usr/bin/env python3
"""Fail-closed integrity checks for S4 lifecycle outputs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/sigmod_ea_postseal_uplift/s4_lifecycle"


def rows(name):
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


checks = []
pair = rows("pairwise_cost_ledger.csv")
target = rows("shared_target_cost_ledger.csv")
horizon = rows("horizon_summary.csv")
summary = rows("dataset_summary.csv")
decision = json.loads((ROOT / "manifests/sigmod_ea_postseal_uplift_s4_decision.json").read_text())
checks += [
    ("pair_rows", len(pair) == 1104),
    ("target_rows", len(target) == 48),
    ("horizon_rows", len(horizon) == 20),
    ("summary_rows", len(summary) == 4),
    ("truth_cost", all(float(r["truth_ndc"]) == 50_000_000 for r in pair + target)),
    ("pair_required_actions_deduplicated", all(len(r["required_cert_actions"].split(";")) == len(set(r["required_cert_actions"].split(";"))) for r in pair)),
    ("source_directions", all(int(r["source_directions"]) == 23 for r in target)),
    ("both_scenarios_both_datasets", {(r["dataset"], r["scenario"]) for r in summary} == {(d, s) for d in ("sift_100k", "arxiv_nomic_100k") for s in ("PAIRWISE_TARGET_CERTIFICATION", "SHARED_TARGET_CERTIFICATION_23_SOURCES")}),
    ("n1m_gate", all(r["gate_positive"] == "1" for r in horizon if r["N_queries_per_direction"] == "1000000")),
    ("full_lifecycle_not_overclaimed", all(r["full_end_to_end_lifecycle_status"].startswith("NOT_ESTIMABLE") for r in summary)),
    ("wall_not_overclaimed", all("NOT_ESTIMABLE" in r["wall_clock_status"] for r in summary)),
    ("decision_label", decision["final_label"] == "S4_TARGET_STAGE_NDC_LIFECYCLE_GATE_PASSED_FULL_LIFECYCLE_NOT_ESTIMABLE"),
    ("no_new_access", decision["new_query_or_truth_access"] is False and decision["new_index_builds"] == 0),
]
inventory = rows("output_inventory.csv")
checks.append(("inventory_hashes", all(sha256(ROOT / r["path"]) == r["sha256"] for r in inventory)))
failed = [name for name, ok in checks if not ok]
payload = {"checks": len(checks), "passed": len(checks) - len(failed), "failed": failed, "status": "PASS" if not failed else "FAIL"}
(OUT / "validation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
seal_paths = [
    ROOT / "docs/sigmod_ea_postseal_uplift/S4_PROTOCOL.md",
    ROOT / "docs/sigmod_ea_postseal_uplift/S4_REPORT.md",
    ROOT / "manifests/sigmod_ea_postseal_uplift_s4_preregistration.json",
    ROOT / "manifests/sigmod_ea_postseal_uplift_s4_decision.json",
    ROOT / "scripts/sigmod_ea_postseal_uplift/freeze_s4_lifecycle.py",
    ROOT / "scripts/sigmod_ea_postseal_uplift/analyze_s4_lifecycle.py",
    ROOT / "scripts/sigmod_ea_postseal_uplift/check_s4.py",
    OUT / "pairwise_cost_ledger.csv",
    OUT / "shared_target_cost_ledger.csv",
    OUT / "horizon_summary.csv",
    OUT / "dataset_summary.csv",
    OUT / "output_inventory.csv",
    OUT / "validation.json",
]
if all(p.exists() for p in seal_paths):
    (OUT / "S4_SHA256.txt").write_text(
        "".join(f"{sha256(p)}  {p.relative_to(ROOT)}\n" for p in seal_paths),
        encoding="utf-8",
    )
print(json.dumps(payload, indent=2))
if failed:
    raise SystemExit(1)
