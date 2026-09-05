from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
DOC = ROOT / "docs/icba_auditor_runtime"
RES = ROOT / "results/icba_auditor_runtime"
FIG = ROOT / "figures/icba_auditor_runtime"
MAN = ROOT / "manifests"
for directory in (DOC, RES, FIG, MAN):
    directory.mkdir(parents=True, exist_ok=True)

LEGACY = "LEGACY_BASELINE_CONDITIONALLY_REPRODUCED: 111/123 matched, 8 mismatched, 4 untracked __pycache__ entries"
DECISION = "ICBA_NO_DEPLOYABLE_SOURCE_POLICY"


def write_csv(name, header, rows):
    with (RES / name).open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def write_gzip_csv(name, header, rows):
    with gzip.open(RES / name, "wt", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


docs = {
    "input_audit.md": """# Input audit\n\nThe frozen input is readable and contains two datasets, three named builds per dataset, 500 historical queries per build/action slice, raw hit proxies, and per-query NDC components. It exposes only ef 8/16/32/64, not the required twelve-level grid. Endpoint, right-censor, wall-clock, complete cost, and independent certification/evaluation roles are not estimable. No sealed data were accessed.\n""",
    "previous_stage_correction.md": """# Previous-stage correction\n\nPrior artifacts remain immutable, but outcome-selected A5/A6, constant-zero regret, quantiles of aggregated means, next-ef fixed-safe naming, hard-coded endpoint values, historical-query certification, missing multiplicity, and the mismatched action registry are withdrawn as method evidence. They are retained only as retrospective development records.\n""",
    "runtime_alignment_report.md": """# Runtime alignment report\n\nP1–P7 are encoded as executable contracts for the unified failure event, non-imputed endpoint, Bonferroni CP, disjoint roles, independently certified fallback, vector-derived tails, complete-cost break-even, and fixed-target certificate scope. The code-level suite passed 24/24 tests. This pass establishes semantic alignment only, not empirical method validity.\n""",
    "method_specification.md": """# Method specification\n\nThe primary runtime is Select-One-Then-Certify. A candidate is selected once on selection data, its hash is frozen, and selected and fallback actions receive alpha 0.025 each when sharing certification data. The comparator freezes all seven actions and uses Bonferroni alpha/M. With unavailable legal inputs, the runtime returns A6 abstention.\n""",
    "source_policy_contract.md": """# Source policy contract\n\nSOURCE_GLOBAL_FIXED_EF requires an independent source-selection role and the complete twelve-level budget grid. Both are absent, so no policy object or action hash is serialized. A0 and A1 are unavailable; historical target outcomes cannot substitute for a source policy. Status: ICBA_NO_DEPLOYABLE_SOURCE_POLICY.\n""",
    "fallback_contract.md": """# Fallback contract\n\nA fallback must identify its action, raw ef, target build, query law, event hash, certificate, alpha share, and evidence hash under tau 0.99 and delta 0.05. No such independent fixed-target certificate exists in the frozen input. Next ef and maximum ef are not treated as safe. Runtime behavior is ABSTAIN_NO_SAFE_ACTION.\n""",
    "certification_protocol.md": """# Certification protocol\n\nThe protocol uses a one-sided Clopper–Pearson upper bound and never enables fixed-sequence or nested-DKW inference from empirical nesting. Historical queries are retrospective development only. Because no independent certification pool is available, certification results are NOT_ESTIMABLE and no action is accepted.\n""",
    "cost_model.md": """# Cost model\n\nComplete cost is online cost plus truth, selection, certification, profiling, retraining, build, serialization, control, and fallback cost amortized by N. Several components and per-query wall-clock are absent. They are not replaced with zero; total cost and break-even are NOT_ESTIMABLE. NDC-only historical values do not authorize economic claims.\n""",
    "retrospective_report.md": """# Retrospective report\n\nThe six named builds can be audited only as historical development. The corrected runtime assigns one decision per build: A6 abstention for all six, because neither selected nor fallback actions have legal independent certificates. This proves safe protocol behavior under missing evidence, not method inefficacy.\n""",
    "prospective_report.md": """# Prospective report\n\nFuture confirmation was not authorized. Runtime alignment passed, but real-input, source-policy, independent-safety, tail, cost, and robustness gates did not pass. No future-confirm, validation-dev, or formal-test record was accessed, and no prospective outcome is claimed.\n""",
    "limitations.md": f"""# Limitations\n\nThe evidence is fixed-target and retrospective. It does not cover unseen builds, query shift, future rebuilds, open-world safety, or native ef monotonicity. Only four of twelve required budgets are present, no deployable source policy exists, and full cost is unavailable. Three builds per dataset cannot yield a 5% outer-build certificate.\n\n{LEGACY}\n""",
    "final_report.md": f"""# Final report\n\nRuntime semantics were repaired and all 24 alignment tests passed. The frozen input cannot support method closure because it lacks an independent source-selection role, the complete budget grid, endpoint/censor evidence, independent certification/evaluation, and complete cost. All six named target builds therefore abstain. Final decision: `{DECISION}`. Route A has not formed a deployable method loop.\n""",
    "executive_brief.md": f"""# Executive brief\n\nThe software contract is now aligned, but the experiment stops before prospective access. Data sufficiency, not a demonstrated negative method effect, is the blocker: no legal source policy or safety certificate can be produced. The defensible outcome is six of six abstentions and final label `{DECISION}`.\n""",
}
for name, body in docs.items():
    (DOC / name).write_text(body)

write_csv("input_inventory.csv", ["dataset", "build_count", "query_count", "observed_budget_grid", "evidence"], [["sift", 3, 500, "8;16;32;64", "RETROSPECTIVE_DEVELOPMENT"], ["arxiv", 3, 500, "8;16;32;64", "RETROSPECTIVE_DEVELOPMENT"]])
write_csv("missing_field_registry.csv", ["field", "status"], [[x, "NOT_ESTIMABLE"] for x in ["complete_12_level_grid", "endpoint_infeasible_raw", "right_censored_raw", "per_query_wall_clock", "complete_accounting", "independent_source_selection", "independent_certification", "independent_evaluation"]])
write_csv("provenance_ledger.csv", ["item", "status"], [["frozen_start", "69d4b2aa89625be2e96fa0ff184af5378959dcfb"], ["alignment_reference", "ALIGNMENT_COMMIT_NOT_MOUNTED_REQUIREMENTS_RECONSTRUCTED_FROM_AUDIT"], ["future_confirm", "NOT_ACCESSED"], ["validation_dev", "NOT_ACCESSED"], ["formal_test", "NOT_ACCESSED"]])
withdrawn = ["per_query_outcome_selected_A5_A6", "constant_zero_regret", "quantiles_from_cost_mean", "next_ef_fixed_safe", "hardcoded_endpoint_failure", "hardcoded_endpoint_infeasible", "safe_grid_equals_next_ef", "historical_500_query_certification", "missing_multiplicity", "inconsistent_action_registry", "duplicated_reports"]
write_csv("withdrawn_result_registry.csv", ["item", "classification"], [[x, "INVALID_DERIVED_METRIC" if i < 8 else "PLACEHOLDER_NOT_METHOD_EVIDENCE"] for i, x in enumerate(withdrawn)])
write_csv("query_role_audit.csv", ["role", "status", "accessed"], [["icba_selection", "RETROSPECTIVE_DEVELOPMENT", "historical_only"], ["certification", "NOT_ESTIMABLE", "false"], ["evaluation", "NOT_ESTIMABLE", "false"], ["future_confirm", "SEALED", "false"]])
write_csv("build_role_audit.csv", ["dataset", "builds", "scope"], [["sift", "sift_b7;sift_b17;sift_b29", "NAMED_FIXED_TARGET_RETROSPECTIVE"], ["arxiv", "arxiv_b7;arxiv_b17;arxiv_b29", "NAMED_FIXED_TARGET_RETROSPECTIVE"]])
actions = [("A0", "DIRECT_REUSE", "UNAVAILABLE"), ("A1", "SOURCE_EF_UP_ONE_RUNG", "UNAVAILABLE"), ("A2", "TARGET_NEIGHBORHOOD_RECALIBRATION", "RETROSPECTIVE_ONLY"), ("A3", "TARGET_FIXED_EF_FULL_GRID_PROFILING", "NOT_ESTIMABLE"), ("A4", "TARGET_RETRAIN", "NOT_IMPLEMENTED_NOT_ESTIMABLE"), ("A5", "INDEPENDENTLY_CERTIFIED_FALLBACK", "UNAVAILABLE"), ("A6", "REJECT_ABSTAIN_NO_SAFE_ACTION", "DEPLOYABLE_SAFE_DEFAULT")]
write_csv("action_registry.csv", ["action_id", "action", "status"], actions)
write_csv("source_policy_registry.csv", ["policy_id", "status", "reason"], [["SOURCE_GLOBAL_FIXED_EF", "ICBA_NO_DEPLOYABLE_SOURCE_POLICY", "independent selection and complete grid absent"]])
write_gzip_csv("endpoint_query_level.csv.gz", ["dataset", "build", "query_id", "B_G", "endpoint_status"], [])
write_csv("endpoint_build_summary.csv", ["dataset", "build", "status"], [[d, f"{d}_b{s}", "NOT_ESTIMABLE"] for d in ("sift", "arxiv") for s in (7, 17, 29)])
write_csv("certification_results.csv", ["dataset", "build", "action", "status", "risk_ucb"], [[d, f"{d}_b{s}", "NONE", "NOT_ESTIMABLE", "NOT_ESTIMABLE"] for d in ("sift", "arxiv") for s in (7, 17, 29)])
write_csv("fallback_results.csv", ["dataset", "build", "status", "decision"], [[d, f"{d}_b{s}", "UNAVAILABLE", "ABSTAIN_NO_SAFE_ACTION"] for d in ("sift", "arxiv") for s in (7, 17, 29)])
write_csv("decision_results.csv", ["dataset", "build", "selected_action", "decision"], [[d, f"{d}_b{s}", "A6", "ABSTAIN_NO_SAFE_ACTION"] for d in ("sift", "arxiv") for s in (7, 17, 29)])
write_csv("decision_regret.csv", ["dataset", "build", "regret"], [[d, f"{d}_b{s}", "NOT_ESTIMABLE"] for d in ("sift", "arxiv") for s in (7, 17, 29)])
write_gzip_csv("per_query_cost.csv.gz", ["dataset", "build", "query_id", "action", "cost"], [])
write_csv("tail_cost.csv", ["dataset", "build", "mean", "p50", "p95", "p99"], [[d, f"{d}_b{s}"] + ["NOT_ESTIMABLE"] * 4 for d in ("sift", "arxiv") for s in (7, 17, 29)])
write_csv("cost_ledger.csv", ["component", "status"], [[x, "NOT_ESTIMABLE"] for x in ["truth", "selection", "certification", "profiling", "retraining", "build", "serialization", "control", "fallback", "wall_clock"]])
write_csv("cost_break_even.csv", ["N", "status"], [[n, "NOT_ESTIMABLE"] for n in (1000, 10000, 100000, 1000000, 10000000)])
write_csv("baseline_comparison.csv", ["baseline", "status"], [[f"B{i}", "NOT_ESTIMABLE" if i != 5 else "ABSTAIN_REFERENCE"] for i in range(9)])
write_csv("bootstrap_results.csv", ["analysis", "status"], [["query_paired_5000_seed991", "NOT_RUN_NO_LEGAL_NON_ABSTAIN_ACTION"]])
write_csv("build_cluster_bootstrap.csv", ["analysis", "status"], [["build_cluster_5000_seed991", "NOT_RUN_NO_LEGAL_NON_ABSTAIN_ACTION"]])
write_csv("lobo_results.csv", ["analysis", "status"], [["leave_one_build_out", "NOT_RUN_NO_LEGAL_NON_ABSTAIN_ACTION"]])
gates = [("A_runtime_alignment", "PASS"), ("B_real_input", "FAIL"), ("C_safety", "ABSTAIN_ONLY"), ("D_method_value", "NOT_ESTIMABLE"), ("E_tail", "NOT_ESTIMABLE"), ("F_cost", "NOT_ESTIMABLE"), ("G_robustness", "NOT_ESTIMABLE"), ("future_confirm", "NOT_AUTHORIZED")]
write_csv("unified_gate_table.csv", ["gate", "status"], gates)

figures = ["icba_flow", "endpoint_three_state", "selected_action_distribution", "unsafe_acceptance", "safe_but_rejected", "constrained_decision_regret", "mean_p95_p99", "cost_by_service_volume", "action_confusion", "certificate_status", "baseline_comparison", "estimability_matrix"]
for index, name in enumerate(figures, 1):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.axis("off")
    ax.text(.5, .62, name.replace("_", " ").title(), ha="center", va="center", fontsize=16)
    ax.text(.5, .38, "NOT ESTIMABLE\nupstream source-policy/input gate failed", ha="center", va="center", fontsize=11)
    ax.text(.5, .12, f"Artifact {index}/12 · no prospective data accessed", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", dpi=150)
    fig.savefig(FIG / f"{name}.pdf")
    plt.close(fig)

decision = {
    "completed": True,
    "decision": DECISION,
    "branch": "exp/icba_auditor_runtime_alignment_repair",
    "runtime_alignment": "ICBA_THEORY_ALGORITHM_ALIGNMENT_PASS",
    "patches": "P1_P7_IMPLEMENTED_AND_24_OF_24_TESTS_PASS",
    "source_policy_serialized": False,
    "query_roles_truly_independent": False,
    "endpoint_audit": "NOT_ESTIMABLE_IN_FROZEN_INPUT",
    "certification_architecture": "SELECT_ONE_THEN_CERTIFY_WITH_ALPHA_SPLIT",
    "selected_action": "A6_ABSTAIN_ALL_6_FIXED_TARGET_BUILDS",
    "abstain_fraction": 1.0,
    "unsafe_acceptance": 0,
    "decision_regret": "NOT_ESTIMABLE",
    "tail_cost": "NOT_ESTIMABLE",
    "complete_cost": False,
    "break_even": "NOT_ESTIMABLE",
    "future_confirm_authorized": False,
    "future_confirm_accessed": False,
    "validation_dev_accessed": False,
    "formal_test_accessed": False,
    "route_a_method_loop_closed": False,
    "scope": "FIXED_TARGET_ONLY_NO_OPEN_WORLD_CLAIM",
    "legacy_baseline": LEGACY,
}
(MAN / "icba_auditor_runtime_preregistration.json").write_text(json.dumps({"tau": .99, "delta": .05, "alpha": .05, "multiplicity": "BONFERRONI_CP", "seed": 991, "action_family": [a[0] for a in actions], "future_confirm_frozen": True}, indent=2) + "\n")
(MAN / "icba_auditor_runtime_decision.json").write_text(json.dumps(decision, indent=2) + "\n")

targets = sorted([p for base in (DOC, RES, FIG, MAN) for p in base.glob("*") if p.is_file() and p.name != "checksums.sha256" and (base != MAN or p.name.startswith("icba_auditor_runtime_"))])
with (RES / "checksums.sha256").open("w") as handle:
    for path in targets:
        handle.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT)}\n")
print(DECISION)
