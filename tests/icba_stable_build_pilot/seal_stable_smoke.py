#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/icba_stable_build_pilot"
RES = ROOT / "results/icba_stable_build_pilot"
FIG = ROOT / "figures/icba_stable_build_pilot"
MANIFEST = ROOT / "manifests/icba_stable_build_pilot_decision.json"
for path in (DOC, RES, FIG):
    path.mkdir(parents=True, exist_ok=True)

smoke = pd.read_csv(RES / "smoke_analysis/smoke_metrics.csv")
values = {(r.query_role, r.graph, r.metric): float(r.value) for r in smoke.itertuples() if str(r.value) != "nan"}
inv = pd.read_csv(RES / "smoke_invariants/repair_invariant_results.csv")
eq = pd.read_csv(RES / "smoke_invariants/stable_native_equivalence.csv")
gate = json.loads((RES / "smoke_analysis/smoke_gate.json").read_text())


def metric(role, graph, name):
    return values[(role, graph, name)]


pd.DataFrame([
    {"dataset": "sift_100k", "phase": "smoke", "changed_sources": 2249,
     "protected_candidates": 2807, "mandatory_survived": 1522,
     "mandatory_total_checked": 1522, "design_trace_affected_rate": gate["design"]["affected_trace_rate"],
     "calibration_trace_affected_rate": gate["calibration"]["affected_trace_rate"]},
]).to_csv(RES / "structure_metrics.csv", index=False)

exp_rows, ef_rows, endpoint_rows, tail_rows = [], [], [], []
for role in ("design", "calibration"):
    for graph in ("baseline", "stable"):
        exp_rows.append({"dataset": "sift_100k", "query_role": role, "graph": graph,
                         "mean_B_exp_feasible": metric(role, graph, "mean_B_exp_feasible"),
                         "right_censor_rate": 1 - metric(role, graph, "endpoint_feasible_rate"),
                         "outer_build_count": 1, "uncertainty": "PILOT_BUILD_UNCERTAINTY_UNDERPOWERED"})
        ef_rows.append({"dataset": "sift_100k", "query_role": role, "graph": graph,
                        "mean_B_ef_feasible": metric(role, graph, "mean_B_ef_feasible"),
                        "B_ef_feasible_rate": metric(role, graph, "B_ef_feasible_rate"),
                        "ef_grid": "10;20;40", "bridge_status": "EMPIRICAL_ONLY"})
        endpoint_rows.append({"dataset": "sift_100k", "query_role": role, "graph": graph,
                              "endpoint_feasible_rate": metric(role, graph, "endpoint_feasible_rate"),
                              "right_censor_rate": 1 - metric(role, graph, "endpoint_feasible_rate")})
        tail_rows.append({"dataset": "sift_100k", "query_role": role, "graph": graph,
                          "mean_ndc": metric(role, graph, "mean_ndc"),
                          "p95_ndc": metric(role, graph, "p95_ndc"),
                          "mean_final_recall": metric(role, graph, "mean_final_recall")})
pd.DataFrame(exp_rows).to_csv(RES / "expansion_budget_results.csv", index=False)
pd.DataFrame(ef_rows).to_csv(RES / "ef_budget_results.csv", index=False)
pd.DataFrame(endpoint_rows).to_csv(RES / "endpoint_censoring.csv", index=False)
pd.DataFrame(tail_rows).to_csv(RES / "ndc_tail_results.csv", index=False)
inv.to_csv(RES / "repair_invariant_results.csv", index=False)

pd.DataFrame([{"dataset": "sift_100k", "paired_builds": 1, "bootstrap_replicates": 0,
               "status": "NOT_ESTIMABLE_SINGLE_SMOKE_BUILD",
               "limitation": "PILOT_BUILD_UNCERTAINTY_UNDERPOWERED"}]).to_csv(RES / "build_cluster_bootstrap.csv", index=False)
pd.DataFrame([{"analysis": "delete_top_1_percent_queries", "status": "NOT_RUN_AFTER_PREREGISTERED_SMOKE_STOP"},
              {"analysis": "leave_one_build_out", "status": "NOT_ESTIMABLE_ONE_BUILD"}]).to_csv(RES / "robustness_results.csv", index=False)
pd.DataFrame([{"N": n, "search_cost": "OBSERVED_NDC_ONLY", "shadow_cost": "OBSERVED_BUILD_NOT_TIMED_UNDER_FIXED_AFFINITY",
               "truth_cost": "SYMBOLIC", "trace_cost": "SYMBOLIC", "repair_cost": "SYMBOLIC",
               "cert_cost": "NOT_ACCESSED", "break_even": "NO_FINITE_BREAK_EVEN_WORKLOAD"}
              for n in (1000, 10000, 100000, 1000000, 10000000)]).to_csv(RES / "cost_ledger.csv", index=False)

pd.DataFrame([
    {"gate": "resource", "status": "PASS", "evidence": "15.024 GiB after recovery; 5 GiB reserve maintained"},
    {"gate": "instrumentation", "status": "PASS", "evidence": "24/24 fields; synthetic 22/22; SIFT native/tracer 300/300"},
    {"gate": "query_roles", "status": "PASS", "evidence": "4x250; non-diagonal overlap 0; reserved roles sealed"},
    {"gate": "repair_invariants", "status": "PASS", "evidence": "10/10; protected 1522/1522; reachability 100000/100000"},
    {"gate": "smoke_effect", "status": "FAIL", "evidence": "calibration B_exp and B_ef both worsened"},
    {"gate": "full_sift", "status": "NOT_AUTHORIZED", "evidence": "EARLY_STRUCTURAL_SURROGATE_FAILURE"},
    {"gate": "arxiv", "status": "NOT_AUTHORIZED", "evidence": "SIFT smoke gate failed"},
    {"gate": "independent_confirmation", "status": "NOT_AUTHORIZED", "evidence": "final decision is a stop label"},
]).to_csv(RES / "unified_gate_table.csv", index=False)

pd.DataFrame([{"field_count": 24, "synthetic_rows": 768, "sift_rows": 300,
               "complete_rows": 1068, "missing_rows": 0, "status": "PASS"}]).to_csv(RES / "trace_field_audit.csv", index=False)
pd.DataFrame([{"graph": "baseline_b7", "queries": 100, "efs": 3, "comparisons": 300, "topk_equal": 300, "ndc_equal": 300},
              {"graph": "stable_b43", "queries": 100, "efs": 3, "comparisons": len(eq), "topk_equal": int(eq.topk_equal.sum()), "ndc_equal": int(eq.ndc_equal.sum())}]).to_csv(RES / "native_trace_equivalence.csv", index=False)

chart_specs = [
    ("01_trace_affected", [0, gate["design"]["affected_trace_rate"], 0, gate["calibration"]["affected_trace_rate"]], "Trace affected rate"),
    ("02_B_exp", [metric("design","baseline","mean_B_exp_feasible"),metric("design","stable","mean_B_exp_feasible"),metric("calibration","baseline","mean_B_exp_feasible"),metric("calibration","stable","mean_B_exp_feasible")], "Mean B_exp (feasible)"),
    ("03_B_ef", [metric("design","baseline","mean_B_ef_feasible"),metric("design","stable","mean_B_ef_feasible"),metric("calibration","baseline","mean_B_ef_feasible"),metric("calibration","stable","mean_B_ef_feasible")], "Mean B_ef (feasible)"),
    ("04_recall", [metric("design","baseline","mean_final_recall"),metric("design","stable","mean_final_recall"),metric("calibration","baseline","mean_final_recall"),metric("calibration","stable","mean_final_recall")], "Mean Recall@10"),
    ("05_endpoint", [metric("design","baseline","endpoint_feasible_rate"),metric("design","stable","endpoint_feasible_rate"),metric("calibration","baseline","endpoint_feasible_rate"),metric("calibration","stable","endpoint_feasible_rate")], "Endpoint feasible rate"),
    ("06_mean_ndc", [metric("design","baseline","mean_ndc"),metric("design","stable","mean_ndc"),metric("calibration","baseline","mean_ndc"),metric("calibration","stable","mean_ndc")], "Mean NDC"),
    ("07_p95_ndc", [metric("design","baseline","p95_ndc"),metric("design","stable","p95_ndc"),metric("calibration","baseline","p95_ndc"),metric("calibration","stable","p95_ndc")], "p95 NDC"),
    ("08_budget_quadrant", [0,0,metric("calibration","stable","mean_B_exp_feasible")-metric("calibration","baseline","mean_B_exp_feasible"),metric("calibration","stable","mean_B_ef_feasible")-metric("calibration","baseline","mean_B_ef_feasible")], "Calibration budget deltas"),
    ("09_invariants", [1]*4, "Invariant groups passed"),
    ("10_protected", [1522,1522,0,0], "Protected edges checked/survived"),
    ("11_gate", [1,1,1,0], "Resource / tracer / invariant / effect"),
    ("12_cost", [1000,10000,100000,1000000], "Symbolic workload scale (no break-even)"),
]
labels = ["design base", "design stable", "cal base", "cal stable"]
for name, series, ylabel in chart_specs:
    fig, ax = plt.subplots(figsize=(7,4.5))
    ax.bar(range(4), series, color=["#7f8c8d","#2980b9","#95a5a6","#c0392b"])
    ax.set_xticks(range(4), labels, rotation=20)
    ax.set_ylabel(ylabel)
    ax.set_title("SIFT exploratory smoke — design/calibration; reserved roles sealed")
    ax.grid(axis="y", alpha=.25)
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", dpi=160)
    fig.savefig(FIG / f"{name}.pdf")
    plt.close(fig)

docs = {
"cfsr_lite_algorithm.md": """# CFSR-Lite algorithm\n\nThe sole preregistered configuration used layer-0 post-build repair with weights critical=.45, backup=.20, presence=.20, frontier=.10 and intruder penalty=.05. It changed 2,249 sources. All invariants passed, but the independent calibration endpoints did not improve. No ablation or tuning was authorized.\n""",
"smoke_test_report.md": f"""# SIFT micro smoke report\n\nInfrastructure and repair gates passed: 24/24 tracer fields, native/tracer equality, 10/10 invariants, 1,522/1,522 mandatory edges survived, and 39% of calibration traces changed. Independent calibration mean B_exp changed {metric('calibration','baseline','mean_B_exp_feasible'):.3f} to {metric('calibration','stable','mean_B_exp_feasible'):.3f}; mean B_ef changed {metric('calibration','baseline','mean_B_ef_feasible'):.3f} to {metric('calibration','stable','mean_B_ef_feasible'):.3f}. This triggered `EARLY_STRUCTURAL_SURROGATE_FAILURE`.\n""",
"sift_pilot_report.md": "# SIFT pilot report\n\nOnly the preregistered micro smoke was run. The full 3+3 paired SIFT pilot was not authorized after the smoke stop.\n",
"arxiv_pilot_report.md": "# Arxiv pilot report\n\n`NOT_RUN`: the preregistered SIFT smoke gate failed. Running Arxiv to search for a positive result was forbidden.\n",
"dual_endpoint_analysis.md": "# Dual-endpoint analysis\n\nOn independent bridge-calibration queries both mean B_exp and mean B_ef worsened. The smoke quadrant is `NO_BUDGET_CONTRACTION`; this is exploratory single-build evidence and not an outer-build certification.\n",
"cost_break_even_report.md": "# Cost and break-even\n\nNo efficacy gate passed, so no finite break-even workload is claimed. Certification was not accessed and its cost remains symbolic. Wall-clock is `WALL_CLOCK_EXPLORATORY_ONLY`.\n",
"limitations.md": "# Limitations\n\nThis is a one-paired-build smoke with 100 design and 100 calibration queries at three ef values. `PILOT_BUILD_UNCERTAINTY_UNDERPOWERED`; bootstrap, LOBO and top-1% robustness were not estimable after the mandatory early stop.\n",
"executive_summary.md": "# Executive summary\n\nCFSR-Lite was implemented and mechanically valid, but its structural intervention did not contract either budget endpoint on independent calibration queries. The route stops without tuning, full SIFT, Arxiv, or confirmation. Final label: `STRUCTURAL_SURROGATE_LINK_FAILED_IN_PILOT`.\n",
"final_report.md": "# Final report\n\nThe resource, instrumentation, role-firewall and repair-invariant gates passed. The SIFT micro smoke effect gate failed because independent calibration B_exp and B_ef both worsened. Mean and p95 NDC improved slightly, but the method's registered structure-to-budget mechanism did not. Full SIFT and Arxiv were correctly not run.\n",
}
for name, text in docs.items():
    (DOC / name).write_text(text)

decision = {
    "schema_version": 2,
    "decision": "STRUCTURAL_SURROGATE_LINK_FAILED_IN_PILOT",
    "stop_reason": "EARLY_STRUCTURAL_SURROGATE_FAILURE",
    "evidence_level": "EXPLORATORY_PAIRED_SINGLE_BUILD_SMOKE",
    "resource_gate": "PASS",
    "tracer_fields_passed": 24,
    "native_trace_equivalence": "PASS_600_OF_600",
    "query_roles": {"design":250,"bridge_calibration":250,"certification_reserved":250,"evaluation_reserved":250,"non_diagonal_overlap":0},
    "repair_invariants": "PASS_10_OF_10",
    "protected_survival": "1522_OF_1522",
    "sift_smoke": "FAIL_DUAL_BUDGET_DIRECTION_ON_CALIBRATION",
    "sift_full": "NOT_AUTHORIZED",
    "arxiv": "NOT_AUTHORIZED",
    "independent_confirmation_authorized": False,
    "validation_dev_accessed": False,
    "formal_test_accessed": False,
    "certification_reserved_accessed": False,
    "evaluation_reserved_accessed": False,
    "wall_clock_status": "WALL_CLOCK_EXPLORATORY_ONLY",
    "build_uncertainty": "PILOT_BUILD_UNCERTAINTY_UNDERPOWERED",
    "calibration": gate["calibration"],
}
MANIFEST.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")

checksum = RES / "checksums.sha256"
targets = []
for directory in (DOC, RES, FIG, ROOT / "tests/icba_stable_build_pilot"):
    targets.extend(path for path in directory.rglob("*") if path.is_file() and path != checksum)
with checksum.open("w") as handle:
    for path in sorted(targets):
        handle.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT)}\n")
print(json.dumps(decision, sort_keys=True))
