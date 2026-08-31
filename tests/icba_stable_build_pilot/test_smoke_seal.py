#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[2]
decision = json.loads((root / "manifests/icba_stable_build_pilot_decision.json").read_text())
checks = [
    decision["decision"] == "STRUCTURAL_SURROGATE_LINK_FAILED_IN_PILOT",
    decision["stop_reason"] == "EARLY_STRUCTURAL_SURROGATE_FAILURE",
    decision["resource_gate"] == "PASS",
    decision["tracer_fields_passed"] == 24,
    decision["native_trace_equivalence"] == "PASS_600_OF_600",
    decision["query_roles"]["non_diagonal_overlap"] == 0,
    decision["repair_invariants"] == "PASS_10_OF_10",
    decision["protected_survival"] == "1522_OF_1522",
    decision["sift_full"] == "NOT_AUTHORIZED",
    decision["arxiv"] == "NOT_AUTHORIZED",
    not decision["independent_confirmation_authorized"],
    not decision["validation_dev_accessed"],
    not decision["formal_test_accessed"],
    not decision["certification_reserved_accessed"],
    not decision["evaluation_reserved_accessed"],
    decision["calibration"]["affected_trace_rate"] >= .10,
    decision["calibration"]["recall_delta"] < -.001,
    len(list((root / "figures/icba_stable_build_pilot").glob("*.png"))) >= 12,
    len(list((root / "figures/icba_stable_build_pilot").glob("*.pdf"))) >= 12,
    len(pd.read_csv(root / "results/icba_stable_build_pilot/expansion_budget_results.csv")) == 4,
    len(pd.read_csv(root / "results/icba_stable_build_pilot/ef_budget_results.csv")) == 4,
    (root / "results/icba_stable_build_pilot/checksums.sha256").stat().st_size > 0,
]
assert all(checks), [index for index, passed in enumerate(checks, 1) if not passed]
print(f"PASS_COUNT={len(checks)}")
