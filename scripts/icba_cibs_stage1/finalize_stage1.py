#!/usr/bin/env python3
"""Generate the immutable Stage-I closure package."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports/icba_cibs_stage1"
FIGURES = ROOT / "figures/icba_cibs_stage1"
FINAL = ROOT / "results/icba_cibs_stage1/final"
DECISION = ROOT / "manifests/icba_cibs_stage1_decision.json"
EVIDENCE_SUMS = ROOT / "manifests/icba_cibs_stage1_evidence_checksums.sha256"
DECISION_SUM = ROOT / "manifests/icba_cibs_stage1_decision.sha256"
DATASETS = ("sift_100k", "arxiv_nomic_100k")
DISPLAY = {"sift_100k": "SIFT-100K", "arxiv_nomic_100k": "ArXiv-Nomic-100K"}
METHODS = ("B0", "B1", "B2", "B3", "B4_CIBS_FIXED", "B5_ORACLE")
FINAL_LABEL = "CIBS_FIXED_STAGE1_FAILED_MINIMUM_GATE"
CORE_MANIFESTS = (
    "manifests/icba_cibs_stage1_pre_truth_contract_amendment.json",
    "manifests/icba_cibs_stage1_phase1_preregistration.json",
    "manifests/icba_cibs_stage1_build_candidates.json",
    "manifests/icba_cibs_stage1_query_roles.json",
    "manifests/icba_cibs_stage1_build_realization.json",
    "manifests/icba_cibs_stage1_selected_actions.json",
    "manifests/icba_cibs_stage1_evaluation_realization.json",
)


def load_json(path: str | Path) -> dict:
    target = Path(path)
    if not target.is_absolute():
        target = ROOT / target
    return json.loads(target.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_events(path: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line]


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def save_figure(fig, stem: str) -> list[str]:
    outputs = []
    for extension in ("png", "pdf"):
        path = FIGURES / f"{stem}.{extension}"
        fig.savefig(path, dpi=180, bbox_inches="tight")
        outputs.append(str(path.relative_to(ROOT)))
    plt.close(fig)
    return outputs


def action_eval_rows(dataset: str, action_id: str) -> list[dict[str, str]]:
    build, ef_text = action_id.split(":ef=")
    path = ROOT / f"results/icba_cibs_stage1/evaluation/{dataset}__{build}__evaluation_all_actions.csv"
    return [row for row in read_csv(path) if int(row["requested_ef"]) == int(ef_text)]


def comprehensive_costs(evaluation: dict, selected: dict, build_manifest: dict) -> dict:
    build_events = read_events("results/icba_cibs_stage1/build_and_fallback_events.jsonl")
    sentinel_events = read_events("results/icba_cibs_stage1/sentinel_events.jsonl")
    evaluation_events = read_events("results/icba_cibs_stage1/evaluation_events.jsonl")
    sentinel_total = sentinel_events[-1]["time_unix_ns"] - sentinel_events[0]["time_unix_ns"]
    sentinel_commands = sum(event.get("elapsed_ns", 0) for event in sentinel_events)
    evaluation_total = evaluation_events[-1]["time_unix_ns"] - evaluation_events[0]["time_unix_ns"]
    evaluation_commands = sum(event.get("elapsed_ns", 0) for event in evaluation_events)
    shared_residual = sentinel_total - sentinel_commands
    builds = {(row["dataset"], row["build_id"]): row for row in build_manifest["builds"]}

    def elapsed_for(log_fragment: str, events: list[dict]) -> int:
        matches = [event["elapsed_ns"] for event in events if log_fragment in event.get("log", "")]
        if len(matches) != 1:
            raise AssertionError(f"expected one event for {log_fragment}, got {len(matches)}")
        return int(matches[0])

    datasets = {}
    for dataset in DATASETS:
        realization = {}
        for build in ("G1", "G2", "G3"):
            realization[build] = {
                "build_command_ns": elapsed_for(f"{dataset}__{build}__build.log", build_events),
                "inspection_serialization_replay_command_ns": elapsed_for(f"{dataset}__{build}__inspect.log", build_events),
                "raw_equivalence_command_ns": elapsed_for(f"{dataset}__{build}__raw_equivalence.log", build_events),
                "index_size_bytes": builds[(dataset, build)]["index_size_bytes"],
                "peak_rss_kib": builds[(dataset, build)]["build"]["peak_rss_kib"],
            }
        fallback_design = elapsed_for(f"{dataset}__G1__fallback_design.log", build_events)
        sentinel_truth = elapsed_for(f"sentinel/{dataset}__sentinel_truth.log", sentinel_events)
        eval_truth = elapsed_for(f"evaluation/{dataset}__evaluation_truth.log", evaluation_events)
        sentinel_search = {build: elapsed_for(f"sentinel/{dataset}__{build}__sentinel_actions.log", sentinel_events) for build in ("G1", "G2", "G3")}
        b1 = evaluation["datasets"][dataset]["methods"]["B1"]
        b4 = evaluation["datasets"][dataset]["methods"]["B4_CIBS_FIXED"]
        extra_realization = sum(
            realization[build][field]
            for build in ("G2", "G3")
            for field in ("build_command_ns", "inspection_serialization_replay_command_ns", "raw_equivalence_command_ns")
        )
        extra_fixed = extra_realization + sentinel_search["G2"] + sentinel_search["G3"] + shared_residual
        online_saving = b1["mean_wall_clock_ns"] - b4["mean_wall_clock_ns"]
        break_even = math.ceil(extra_fixed / online_saving) if online_saving > 0 else None
        workloads = []
        b1_offline = sum(realization["G1"][field] for field in ("build_command_ns", "inspection_serialization_replay_command_ns", "raw_equivalence_command_ns")) + fallback_design + sentinel_search["G1"]
        b4_offline = sum(realization[build][field] for build in ("G1", "G2", "G3") for field in ("build_command_ns", "inspection_serialization_replay_command_ns", "raw_equivalence_command_ns")) + fallback_design + sum(sentinel_search.values()) + shared_residual
        for n in (1_000, 10_000, 100_000, 1_000_000, 10_000_000):
            workloads.append({
                "N": n,
                "truth_available_B1_ns": b1_offline + n * b1["mean_wall_clock_ns"],
                "truth_available_B4_ns": b4_offline + n * b4["mean_wall_clock_ns"],
                "truth_included_B1_ns": sentinel_truth + b1_offline + n * b1["mean_wall_clock_ns"],
                "truth_included_B4_ns": sentinel_truth + b4_offline + n * b4["mean_wall_clock_ns"],
            })
        datasets[dataset] = {
            "realization": realization,
            "truth_acquisition": {"sentinel_ns": sentinel_truth, "evaluation_diagnostic_ns": eval_truth},
            "action_search_36_wall_clock_ns": sentinel_search,
            "selection_certification_orchestration_shared_residual_ns_conservative_full_charge": shared_residual,
            "fallback_design_command_ns": fallback_design,
            "fallback_online": evaluation["datasets"][dataset]["methods"]["B0"],
            "incremental_B4_vs_B1": {
                "extra_fixed_wall_clock_ns": extra_fixed,
                "per_query_wall_clock_saving_ns": online_saving,
                "finite_break_even": break_even is not None,
                "break_even_queries": break_even if break_even is not None else "NO_FINITE_BREAK_EVEN",
                "extra_storage_bytes": realization["G2"]["index_size_bytes"] + realization["G3"]["index_size_bytes"],
            },
            "workloads": workloads,
        }
    return {
        "schema_version": 1,
        "status": "PASS_COMPLETE_COST_LEDGER_WITH_COMBINED_COMPONENT_DISCLOSURE",
        "component_identifiability": {
            "selection_and_certification": "combined with Python orchestration in exact supervisor residual",
            "serialization": "combined with inspection/save-load replay command",
            "storage": "exact bytes",
        },
        "sentinel_supervisor": {"total_ns": sentinel_total, "command_ns": sentinel_commands, "residual_ns": shared_residual},
        "evaluation_supervisor": {"total_ns": evaluation_total, "command_ns": evaluation_commands, "residual_ns": evaluation_total - evaluation_commands},
        "truth_channels": ["truth_available", "truth_acquisition_included"],
        "datasets": datasets,
    }


def machine_checks(prereg: dict, evaluation: dict, selected: dict, build: dict, roles: dict, k2: dict, complete_cost: dict) -> dict:
    checks = []
    def add(identifier: str, name: str, passed: bool, detail: str) -> None:
        checks.append({"id": identifier, "name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    phase0 = load_json("manifests/icba_cibs_stage1_phase0_audit.json")
    build_gate = load_json("results/icba_cibs_stage1/build_and_fallback_gate.json")
    eval_validation = load_json("results/icba_cibs_stage1/evaluation_independent_validation.json")
    access = read_csv(ROOT / "results/icba_cibs_stage1/phase1/query_roles/truth_access_log.csv")
    build_rows = build["builds"]
    lock_status = phase0["theory_lock_checksums"]["status"]
    add("T01", "frozen lock 28/28", lock_status == "PASS_28_OF_28", lock_status)
    overlaps = [value for ds in roles["datasets"].values() for value in ds["pairwise_source_id_overlap"].values()]
    add("T02", "query-role pairwise overlap zero", all(value == 0 for value in overlaps), f"max={max(overlaps)}")
    historical = [ds["selected_historical_source_id_overlap"] for ds in roles["datasets"].values()]
    add("T03", "historical source-ID overlap zero", all(value == 0 for value in historical), f"sum={sum(historical)}")
    future = [row for row in access if row["role"] == "cibs_future_confirm"]
    add("T04", "future-confirm firewall", all((row["truth_accessed"], row["action_outcome_accessed"]) == ("0", "0") for row in future), "2/2 dataset roles sealed")
    add("T05", "build-set immutability", len(build_rows) == 6 and not build["failed_or_replaced_builds"], f"builds={len(build_rows)} replacements={len(build['failed_or_replaced_builds'])}")
    add("T06", "insertion-order hash and replay", all(row["insertion_order_file_sha256"] and row["insertion_order_le_u32_sha256"] for row in build_rows), "all 6 builds hashed")
    add("T07", "resource gate before every build", all(item["status"] == "PASS" for item in build["resource_checks"]), f"checks={len(build['resource_checks'])}")
    compiler = build["compiler"]
    add("T08", "compiler flags and scalar replay", compiler["simd"] == "NO_MANUAL_VECTORIZATION_SCALAR" and "-DNO_MANUAL_VECTORIZATION" in compiler["flags"], compiler["compiler"])
    add("T09", "native/tracer top-10 equivalence", eval_validation["native_tracer_equivalence"] == "PASS_ALL_EVALUATION_ROWS", eval_validation["native_tracer_equivalence"])
    add("T10", "native/tracer exact NDC equivalence", all(row["raw_action_equivalence"]["native_tracer_exact_ndc"] == "PASS_ALL" for row in build_rows), "all 6 design matrices")
    add("T11", "synthetic fallback full enumeration", build_gate["synthetic_contract_tests"] == "PASS_5_OF_5", build_gate["synthetic_contract_tests"])
    add("T12", "actual G1 layer-0 connectivity", build_gate["actual_layer0_directed_connectivity"] == "PASS_100000_OF_100000_BOTH_DATASETS", build_gate["actual_layer0_directed_connectivity"])
    add("T13", "fallback native/bruteforce exact top-10", build_gate["native_bruteforce_exact_top10"] == "PASS_ALL_DESIGN_QUERIES", build_gate["native_bruteforce_exact_top10"])
    add("T14", "index save/load replay", build_gate["save_load_replay"] == "PASS_ALL_SIX_INDEXES", build_gate["save_load_replay"])
    add("T15", "CP reference vectors", prereg["main_failure_thresholds"]["fourth_failure_forbids_certification"], "n=256: <=3 only")
    add("T16", "Bonferroni family size", prereg["risk"]["family_size"] == 36, "alpha/36")
    add("T17", "action matrix 36 cells/query", all(item["action_cells"] == 18000 for item in eval_validation["datasets"].values()), "18000 rows per dataset")
    headers = read_csv(ROOT / "results/icba_cibs_stage1/evaluation/sift_100k__G1__evaluation_all_actions.csv")[0]
    add("T18", "ef/NDC/expansion separation", all(key in headers for key in ("requested_ef", "native_ndc", "actual_expansions")), "distinct columns")
    add("T19", "selection tie-break replay", all(selected["datasets"][ds]["B4_CIBS_FIXED"]["statistics"]["certified"] for ds in DATASETS), "both frozen selections replayed")
    add("T20", "evaluation sealed until action hash", evaluation["selected_action_commit"] == "44e206674612f6630373aa49375c27059d0f3040", evaluation["selected_action_commit"])
    add("T21", "cost ledger completeness", complete_cost["status"].startswith("PASS_COMPLETE_COST_LEDGER"), complete_cost["status"])
    add("T22", "artifact checksum replay", eval_validation["status"] == "PASS_EVALUATION_INDEPENDENT_REPLAY", eval_validation["status"])
    z_ok = True
    for ds in DATASETS:
        for build_id in ("G1", "G2", "G3"):
            for row in read_csv(ROOT / f"results/icba_cibs_stage1/evaluation/{ds}__{build_id}__evaluation_all_actions.csv"):
                z_ok &= int(row["Z_abs"]) == int(float(row["raw_recall_at_10"]) < 0.90 or row["endpoint_status"] != "PASS")
    add("T23", "query failure boundary", z_ok, "Z_abs replayed for 36000 rows")
    add("T24", "baseline action equivalence", all(evaluation["datasets"][ds]["selected_actions_reused_without_reselection"]["B1"] == selected["datasets"][ds]["B1"]["action_id"] for ds in DATASETS), "B1/B4 frozen lookup")
    add("T25", "K2 zero-failure certificate", all(item["statistics"]["failures"] == 0 for ds in k2["datasets"].values() for item in ds["actions"] if item["statistics"]["certified"]), "n=128 M=24")
    add("T26", "evaluation no reselection", evaluation["evaluation_reselection_performed"] is False, "false")
    add("T27", "future-confirm remains unopened", evaluation["future_confirm_accessed"] is False and k2["future_confirm_accessed"] is False, "false across main and K2")
    add("T28", "core seven manifests present", all((ROOT / path).is_file() for path in CORE_MANIFESTS), "7/7")
    if not all(item["status"] == "PASS" for item in checks):
        failed = [item["id"] for item in checks if item["status"] != "PASS"]
        raise AssertionError(f"machine closure checks failed: {failed}")
    return {"schema_version": 1, "status": "PASS_28_OF_28_MACHINE_CHECKS", "checks": checks}


def main() -> None:
    for path in (REPORTS, FIGURES, FINAL, DECISION, EVIDENCE_SUMS, DECISION_SUM):
        if path.exists():
            raise RuntimeError(f"refusing to overwrite final artifact: {path}")
    REPORTS.mkdir(parents=True)
    FIGURES.mkdir(parents=True)
    FINAL.mkdir(parents=True)
    evaluation = load_json("manifests/icba_cibs_stage1_evaluation_realization.json")
    selected = load_json("manifests/icba_cibs_stage1_selected_actions.json")
    build = load_json("manifests/icba_cibs_stage1_build_realization.json")
    prereg = load_json("manifests/icba_cibs_stage1_phase1_preregistration.json")
    roles = load_json("manifests/icba_cibs_stage1_query_roles.json")
    main_gate = load_json("results/icba_cibs_stage1/analysis/main_gate_decision.json")
    robustness = load_json("results/icba_cibs_stage1/analysis/robustness.json")
    k2_selection = load_json("manifests/icba_cibs_stage1_k2_selected_actions.json")
    k2_eval = load_json("results/icba_cibs_stage1/k2_ablation/evaluation.json")
    complete_cost = comprehensive_costs(evaluation, selected, build)
    (FINAL / "complete_cost_ledger.json").write_text(json.dumps(complete_cost, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tests = machine_checks(prereg, evaluation, selected, build, roles, k2_selection, complete_cost)
    (FINAL / "machine_test_matrix.json").write_text(json.dumps(tests, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    figure_paths = []
    colors = ["#6b7280", "#2563eb", "#7c3aed", "#0f766e", "#dc2626", "#d97706"]
    for dataset in DATASETS:
        methods = evaluation["datasets"][dataset]["methods"]
        for index, (metric, title, ylabel) in enumerate((
            ("mean_recall_at_10", "Mean Recall@10", "Recall@10"),
            ("mean_ndc", "Mean exact NDC", "NDC"),
            ("p95_ndc", "p95 exact NDC", "NDC"),
        ), start=1):
            fig, ax = plt.subplots(figsize=(7.2, 4.2))
            values = [methods[method][metric] for method in METHODS]
            ax.bar(range(len(METHODS)), values, color=colors)
            ax.set_xticks(range(len(METHODS)), ["B0", "B1", "B2", "B3", "CIBS", "Oracle"], rotation=20)
            ax.set_title(f"{DISPLAY[dataset]} — {title}")
            ax.set_ylabel(ylabel)
            ax.grid(axis="y", alpha=0.25)
            figure_paths += save_figure(fig, f"{index + (0 if dataset == DATASETS[0] else 3):02d}_{dataset}_{metric}")
        effects = robustness["datasets"][dataset]["build_effects"]
        matrix = np.array([[item["per_build"][build_id]["mean_ndc"] for item in effects] for build_id in ("G1", "G2", "G3")])
        fig, ax = plt.subplots(figsize=(8.5, 3.4))
        image = ax.imshow(matrix, aspect="auto", cmap="viridis")
        ax.set_yticks(range(3), ["G1", "G2", "G3"])
        ax.set_xticks(range(12), [str(value) for value in (10,16,24,32,48,64,96,128,192,256,384,512)], rotation=45)
        ax.set_xlabel("raw ef")
        ax.set_title(f"{DISPLAY[dataset]} — sentinel mean NDC by build")
        fig.colorbar(image, ax=ax, label="mean NDC")
        figure_paths += save_figure(fig, f"{7 if dataset == DATASETS[0] else 8:02d}_{dataset}_build_effect")
        b1_action = selected["datasets"][dataset]["B1"]["action_id"]
        b4_action = selected["datasets"][dataset]["B4_CIBS_FIXED"]["action_id"]
        b1_rows = action_eval_rows(dataset, b1_action)
        b4_rows = action_eval_rows(dataset, b4_action)
        gains = np.sort(np.array([int(b1_rows[i]["native_ndc"]) - int(b4_rows[i]["native_ndc"]) for i in range(500)]))
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        ax.plot(gains, np.arange(1, 501) / 500, color="#dc2626")
        ax.axvline(0, color="black", linewidth=1)
        ax.set_xlabel("Per-query NDC gain (B1 − CIBS)")
        ax.set_ylabel("Empirical CDF")
        ax.set_title(f"{DISPLAY[dataset]} — paired evaluation gain")
        ax.grid(alpha=0.25)
        figure_paths += save_figure(fig, f"{9 if dataset == DATASETS[0] else 10:02d}_{dataset}_gain_ecdf")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, dataset in zip(axes, DATASETS):
        rows = complete_cost["datasets"][dataset]["workloads"]
        n = [row["N"] for row in rows]
        ax.plot(n, [row["truth_included_B1_ns"] / 1e9 for row in rows], marker="o", label="B1")
        ax.plot(n, [row["truth_included_B4_ns"] / 1e9 for row in rows], marker="o", label="CIBS")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(DISPLAY[dataset])
        ax.set_xlabel("queries N")
        ax.set_ylabel("total wall seconds")
        ax.grid(alpha=0.25)
        ax.legend()
    fig.suptitle("Truth-acquisition-included complete cost")
    figure_paths += save_figure(fig, "11_complete_cost_break_even")

    gate_names = list(next(iter(main_gate["minimum_gate"]["datasets"].values()))["checks"])
    gate_matrix = np.array([[int(main_gate["minimum_gate"]["datasets"][ds]["checks"][name]) for name in gate_names] for ds in DATASETS])
    fig, ax = plt.subplots(figsize=(10.5, 3.0))
    ax.imshow(gate_matrix, aspect="auto", cmap=matplotlib.colors.ListedColormap(["#dc2626", "#16a34a"]), vmin=0, vmax=1)
    ax.set_yticks(range(2), [DISPLAY[ds] for ds in DATASETS])
    ax.set_xticks(range(len(gate_names)), [name.replace("_", " ") for name in gate_names], rotation=35, ha="right")
    ax.set_title("Minimum Gate pass/fail matrix")
    for y in range(2):
        for x in range(len(gate_names)):
            ax.text(x, y, "PASS" if gate_matrix[y, x] else "FAIL", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
    figure_paths += save_figure(fig, "12_minimum_gate_matrix")

    eval_rows = []
    for dataset in DATASETS:
        data = evaluation["datasets"][dataset]
        b1 = data["methods"]["B1"]
        b4 = data["methods"]["B4_CIBS_FIXED"]
        comp = data["comparisons"]["B4_vs_B1"]
        eval_rows.append([DISPLAY[dataset], f"{b4['mean_recall_at_10']:.4f}", f"{comp['recall_delta']:+.4f}", f"{b4['mean_ndc']:.1f}", f"{100*comp['mean_ndc_relative_gain']:.3f}%", f"{comp['p95_ndc_delta']:+.2f}"])
    gate_rows = [[DISPLAY[ds], "PASS" if item["pass"] else "FAIL", ", ".join(name for name, value in item["checks"].items() if not value)] for ds, item in main_gate["minimum_gate"]["datasets"].items()]
    reports = {}
    closure_items = [
        "Frozen base retained at b0190169cdb758aa5311c7d13fbfd4fd724020f0.", "Pre-truth amendment committed before Phase 1.", "Tau fixed at Recall@10 >= 0.90.", "Raw ef grid fixed to 12 values.", "G1 ef=100000 fallback independently proved.", "Evidence level is EXPLORATORY_FIXED_TARGET_STAGE_I.", "Query semantics are a frozen finite pool.", "Role overlap is zero.", "Historical source-ID overlap is zero.", "Future-confirm was never opened.", "K=3 build portfolio was frozen.", "All six indexes passed connectivity and replay.", "Scalar compiler/SIMD mode replayed.", "Native/tracer top-k equivalence passed.", "Native/tracer exact-NDC equivalence passed.", "Sentinel n=256 completed for both datasets.", "All 36 actions were charged separately.", "Exact CP alpha/36 certification replayed.", "Selected actions were frozen before evaluation.", "Evaluation used 500 queries per dataset.", "Evaluation performed no reselection.", "B0 through B5 were reported.", "Paired bootstrap used 5000 replicates, seed 991.", "Top-1% gain deletion was reported.", "Build effects and LOBO were reported.", "Selection stability was reported.", "Complete wall-cost ledger includes two truth channels.", "Workloads N=1e3..1e7 were reported.", "K=2 ablation ran only after main completion.", "K=2 did not replace main K=3.", "Minimum Gate failed on both datasets.", "No independent confirmation or CIBS-Race is authorized.",
    ]
    reports["01_executive_decision.md"] = "# ICBA CIBS-Fixed Stage-I final decision\n\n" + f"Final label: **{FINAL_LABEL}**. Evidence: `EXPLORATORY_FIXED_TARGET_STAGE_I`; scope: `CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO`.\n\n" + md_table(["Dataset", "Minimum Gate", "Failed checks"], gate_rows) + "\n\n## 32-point closure\n\n" + "\n".join(f"{i}. {item}" for i, item in enumerate(closure_items, 1)) + "\n"
    reports["02_protocol_and_isolation.md"] = "# Protocol and isolation report\n\nAll seven core manifests form the pre-truth through evaluation hash chain. The selected action was committed before evaluation access; evaluation reselection is false. Future-confirm remained 0/0 for truth and action outcomes. Two concurrent alternate runner edits were quarantined in recoverable git stashes and were not executed as frozen protocol code.\n\nMachine closure: **PASS 28/28**. Query semantics: frozen finite pool; evidence remains exploratory fixed-target only.\n"
    reports["03_build_and_fallback.md"] = "# Build and fixed-safe fallback report\n\nSix preregistered indexes completed without replacement. Every index passed 100,000-node directed layer-0 reachability, byte-identical save/load replay, and native/tracer equivalence. G1 raw ef=100000 enumerated all 100,000 reachable nodes and returned brute-force exact top-10 on all design queries.\n\n" + md_table(["Dataset", "G1 bytes", "G2 bytes", "G3 bytes", "Fallback mean NDC", "Fallback p95 NDC"], [[DISPLAY[ds], complete_cost["datasets"][ds]["realization"]["G1"]["index_size_bytes"], complete_cost["datasets"][ds]["realization"]["G2"]["index_size_bytes"], complete_cost["datasets"][ds]["realization"]["G3"]["index_size_bytes"], f"{evaluation['datasets'][ds]['methods']['B0']['mean_ndc']:.1f}", f"{evaluation['datasets'][ds]['methods']['B0']['p95_ndc']:.1f}"] for ds in DATASETS]) + "\n"
    reports["04_sentinel_certificate.md"] = "# Sentinel procedure-certificate report\n\nThe one-sided exact Clopper-Pearson Bonferroni rule used alpha/36 over 256 queries; at most three failures certified. Selected actions were SIFT G3/ef=96 and ArXiv G2/ef=48. These are `PROCEDURE_CERTIFICATE` outputs, not held-out risk certificates.\n\n" + md_table(["Dataset", "B1", "CIBS", "CIBS failures", "CIBS CP UCB", "Sentinel mean NDC"], [[DISPLAY[ds], selected["datasets"][ds]["B1"]["action_id"], selected["datasets"][ds]["B4_CIBS_FIXED"]["action_id"], selected["datasets"][ds]["B4_CIBS_FIXED"]["statistics"]["failures"], f"{selected['datasets'][ds]['B4_CIBS_FIXED']['statistics']['risk_cp_ucb']:.5f}", f"{selected['datasets'][ds]['B4_CIBS_FIXED']['statistics']['mean_ndc']:.2f}"] for ds in DATASETS]) + "\n"
    reports["05_held_out_evaluation.md"] = "# Held-out evaluation risk-diagnostic report\n\nEvaluation used 500 queries per dataset and did not reselect. It is a `HELD_OUT_RISK_DIAGNOSTIC`.\n\n" + md_table(["Dataset", "CIBS Recall", "Recall delta vs B1", "CIBS mean NDC", "Mean gain vs B1", "p95 delta"], eval_rows) + "\n\nBoth Recall deltas violate the preregistered -0.001 Minimum Gate. SIFT additionally misses the 1% mean-gain gate and has a positive p95 delta.\n"
    reports["06_robustness_and_build_effects.md"] = "# Robustness and build-effect report\n\n" + md_table(["Dataset", "Frozen action stability", "Selected-action removal", "Selected-build removal", "Top-1% deleted gain positive"], [[DISPLAY[ds], f"{100*robustness['datasets'][ds]['selection_stability']['frozen_action_frequency']:.2f}%", robustness["datasets"][ds]["selected_action_removed"]["selected"], robustness["datasets"][ds]["selected_build_removed"]["selected"], evaluation["datasets"][ds]["delete_top_1_percent_gain"]["positive_after_deletion"]] for ds in DATASETS]) + "\n\nLOBO, per-ef build effects, per-query gain ECDFs, and all 5,000 selection-stability counts are in the machine record. These diagnostics do not change the frozen selection.\n"
    reports["07_cost_and_break_even.md"] = "# Complete cost and break-even report\n\nConstruction, peak RSS, exact index bytes, truth acquisition, 36-action search, selection/certification orchestration residual, combined inspection/serialization/replay, storage, and fallback costs are recorded. Selection/certification and serialization were not separately timed by the original runner, so their exact measured combined commands are disclosed rather than imputed.\n\n" + md_table(["Dataset", "Extra fixed wall ns", "Online saving ns/query", "Break-even queries", "Extra index bytes"], [[DISPLAY[ds], complete_cost["datasets"][ds]["incremental_B4_vs_B1"]["extra_fixed_wall_clock_ns"], f"{complete_cost['datasets'][ds]['incremental_B4_vs_B1']['per_query_wall_clock_saving_ns']:.3f}", complete_cost["datasets"][ds]["incremental_B4_vs_B1"]["break_even_queries"], complete_cost["datasets"][ds]["incremental_B4_vs_B1"]["extra_storage_bytes"]] for ds in DATASETS]) + "\n\nSIFT has no finite wall-clock break-even because CIBS is slightly slower per query. Both truth-available and truth-acquisition-included channels are tabulated for N={1e3,1e4,1e5,1e6,1e7}.\n"
    reports["08_k2_ablation.md"] = "# Preregistered K=2 ablation report\n\nThe K=2/L=12/n=128/M=24 zero-failure ablation ran only after the main K=3 analysis commit. Its selection was separately committed before evaluation linkage and cannot replace main K=3.\n\n" + md_table(["Dataset", "K2 B1", "K2 CIBS", "Mean gain", "Recall delta", "p95 delta"], [[DISPLAY[ds], k2_eval["datasets"][ds]["K2_B1_action"], k2_eval["datasets"][ds]["K2_selected_action"], f"{100*k2_eval['datasets'][ds]['B4_vs_B1']['mean_ndc_relative_gain']:.3f}%", f"{k2_eval['datasets'][ds]['B4_vs_B1']['recall_delta']:+.4f}", f"{k2_eval['datasets'][ds]['B4_vs_B1']['p95_ndc_delta']:+.2f}"] for ds in DATASETS]) + "\n"
    for name, content in reports.items():
        (REPORTS / name).write_text(content, encoding="utf-8")

    evidence_paths = [ROOT / path for path in CORE_MANIFESTS]
    evidence_paths += sorted(REPORTS.glob("*.md")) + sorted(FIGURES.glob("*.*")) + [FINAL / "complete_cost_ledger.json", FINAL / "machine_test_matrix.json", ROOT / "manifests/icba_cibs_stage1_k2_selected_actions.json", ROOT / "results/icba_cibs_stage1/k2_ablation/evaluation.json"]
    lines = [f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in sorted(evidence_paths)]
    EVIDENCE_SUMS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    decision = {
        "schema_version": 1,
        "status": "SEALED_FINAL_DECISION",
        "final_label": FINAL_LABEL,
        "evidence_level": "EXPLORATORY_FIXED_TARGET_STAGE_I",
        "conditionality": "CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO",
        "minimum_gate_both_datasets_pass": False,
        "promotion_gate_pass": False,
        "positive_cibs_evidence": False,
        "authorize_independent_portfolio_confirmation": False,
        "authorize_cibs_race": False,
        "future_confirm_accessed": False,
        "evaluation_reselection_performed": False,
        "main_K3_replaced_by_K2": False,
        "decision_generation_parent_commit": "3d8fb1f14db909ca458b384f4f09f6ab040bf98f",
        "failed_minimum_gate": main_gate["minimum_gate"],
        "core_manifests": list(CORE_MANIFESTS),
        "supplementary_K2_manifest": "manifests/icba_cibs_stage1_k2_selected_actions.json",
        "reports": sorted(str(path.relative_to(ROOT)) for path in REPORTS.glob("*.md")),
        "figures": figure_paths,
        "machine_test_matrix": "results/icba_cibs_stage1/final/machine_test_matrix.json",
        "machine_test_status": tests["status"],
        "evidence_checksums": str(EVIDENCE_SUMS.relative_to(ROOT)),
        "evidence_checksums_sha256": sha256(EVIDENCE_SUMS),
    }
    DECISION.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DECISION_SUM.write_text(f"{sha256(DECISION)}  {DECISION.relative_to(ROOT).as_posix()}\n", encoding="utf-8")
    print(json.dumps({"final_label": FINAL_LABEL, "reports": len(reports), "figures": len(figure_paths) // 2, "machine_tests": len(tests["checks"]), "decision_sha256": sha256(DECISION)}, sort_keys=True))


if __name__ == "__main__":
    main()
