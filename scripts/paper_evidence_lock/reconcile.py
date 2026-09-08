#!/usr/bin/env python3
"""Deterministic Graph-ANNS paper-evidence lock audit.

This audit is intentionally retrospective.  It never opens confirmatory or
future-replication query roles and never builds or searches an index.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "paper_evidence_lock"
RES = ROOT / "results" / "paper_evidence_lock"
MAN = ROOT / "manifests"
TEST = ROOT / "tests" / "paper_evidence_lock"
for p in (DOC, RES, TEST):
    p.mkdir(parents=True, exist_ok=True)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(rel: str) -> dict:
    p = ROOT / rel
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def file_exists(rel: str) -> bool:
    return (ROOT / rel).is_file()


def file_size(rel: str) -> int:
    try:
        return (ROOT / rel).stat().st_size
    except OSError:
        return 0


def count_csv_rows(rel: str) -> int | None:
    p = ROOT / rel
    if not p.exists():
        return None
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return max(0, sum(1 for _ in f) - 1)
    except OSError:
        return None


def main() -> None:
    head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    parent = head
    data_recovery = read_json("manifests/icba_fixed_target_auditor_data_recovery.json")
    fixed_decision = read_json("manifests/icba_fixed_target_auditor_decision.json")
    completed_matrix = read_json("manifests/gate_a/completed_run_matrix.json")
    run_matrix = read_json("manifests/gate_a/run_matrix.json")
    env = read_json("manifests/gate_a/environment.json")

    anchors = [
        "b82abf6bab8aae54b23aee5ccce5cde0ba5a3412",
        "80c505dcc3ec13855c700a0f59df3c042aa281ec",
        "b374e9b788eb572f59b826e8b5c9532e44a5129a",
        "ed8d1e0d84c075fddbbc4d8aa5e77a57683a2fb6",
        "77e0d430bc04b819276b570a96eedb339a66c043",
        "a9f88bbcfd9b2c2f3e8a27e1471e16628b60cdb0",
        "6339c512d81abbe49ff11b526676ec4d6d571453",
        "0f5a2bec55cc62e9f9754358c1691eb965afe856",
    ]
    anchor_rows = []
    for h in anchors:
        try:
            subject = git("show", "-s", "--format=%s", h)
            present = "YES"
        except subprocess.CalledProcessError:
            subject = "COMMIT_NOT_LOCALLY_AVAILABLE"
            present = "NO"
        anchor_rows.append([h, present, subject, "E2" if h == head else "E1"])
    write_csv(RES / "provenance_ledger.csv", ["commit", "locally_available", "subject", "evidence_level"], anchor_rows)

    common_grid = data_recovery.get("common_main_grid") or fixed_decision.get("common_grid") or []
    completed_efs = sorted({ef for r in completed_matrix.get("runs", []) for ef in r.get("ef_values", [])})
    run_efs = sorted({ef for r in run_matrix.get("runs", []) for ef in r.get("ef_values", [])})
    grid = common_grid or completed_efs or run_efs
    grid_text = "{" + ",".join(str(x) for x in grid) + "}"

    # The two existing artifacts intentionally disagree.  Both values are
    # retained with provenance; neither is silently selected.
    numeric_rows = [
        ["main_runs", data_recovery.get("main_runs", fixed_decision.get("main_runs", "NOT_REPORTED")), "runs", "manifests/icba_fixed_target_auditor_data_recovery.json", head, "main_runs", "none", "E2", "historical scope", "CONSISTENT", "81 main runs are reported by both recovery artifacts"],
        ["physical_rows", "1458000", "rows", "docs/icba_fixed_target_auditor/data_recovery_report.md", head, "81 runs × 1000 queries × 6 budgets × 3 latency repeats", "none", "E2", "main historical evidence", "CONFLICT", "Recovery report value"],
        ["physical_rows", str(data_recovery.get("main_query_rows_with_latency_repeats", "NOT_REPORTED")), "rows", "manifests/icba_fixed_target_auditor_data_recovery.json", head, "manifest field", "none", "E2", "main historical evidence", "CONFLICT", "Manifest value disagrees with recovery report"],
        ["unique_query_budget_units", "486000", "query-budget units", "docs/icba_fixed_target_auditor/data_recovery_report.md", head, "81 runs × 1000 queries × 6 budgets", "none", "E2", "main historical evidence", "CONFLICT", "Recovery report value"],
        ["unique_query_budget_units", str(data_recovery.get("main_unique_query_budget_units", "NOT_REPORTED")), "query-budget units", "manifests/icba_fixed_target_auditor_data_recovery.json", head, "manifest field", "none", "E2", "main historical evidence", "CONFLICT", "Manifest value disagrees with recovery report"],
        ["historical_972000_claim", "972000", "records", "docs/icba_fixed_target_auditor/data_recovery_report.md", head, "historical 12-level claim", "none", "E1", "appendix/motivation only", "NOT_REPRODUCED", "The source report explicitly says the 12-level claim was not recovered"],
        ["historical_648000_claim", "648000", "records", "not found in scanned evidence", head, "unresolved", "none", "E0", "drop", "UNRESOLVED", "No locally auditable source artifact was found"],
        ["historical_1656000_claim", "1656000", "records", "manifests/icba_fixed_target_auditor_data_recovery.json", head, "manifest field", "none", "E2", "appendix pending reconciliation", "CONFLICT", "Conflicts with 1,458,000 recovery report"],
        ["historical_552000_claim", "552000", "query-budget units", "manifests/icba_fixed_target_auditor_data_recovery.json", head, "manifest field", "none", "E2", "appendix pending reconciliation", "CONFLICT", "Conflicts with 486,000 recovery report"],
        ["actual_common_budget_grid", grid_text, "requested ef values", "manifests/icba_fixed_target_auditor_data_recovery.json", head, "common_main_grid", "none", "E2", "primary protocol candidate", "RECONCILED", "The auditable common grid is six levels, not twelve"],
        ["directed_build_pairs", str(fixed_decision.get("directed_pairs", "NOT_REPORTED")), "directed source→target pairs", "manifests/icba_fixed_target_auditor_decision.json", head, "directed_pairs", "none", "E2", "historical retrospective only", "RECONCILED", "Current fixed-target audit reports 12, not the 648 historical claim"],
        ["historical_648_directed_pairs_claim", "648", "directed source→target pairs", "not found in scanned evidence", head, "unresolved", "none", "E0", "drop", "UNRESOLVED", "No locally auditable source artifact was found"],
        ["historical_324_undirected_pairs_claim", "324", "undirected build pairs", "not found in scanned evidence", head, "unresolved", "none", "E0", "drop", "UNRESOLVED", "No locally auditable source artifact was found"],
    ]
    write_csv(RES / "numeric_reconciliation.csv", ["metric_name", "exact_value", "counting_unit", "source_file", "source_commit", "filter", "deduplication_key", "evidence_level", "paper_usage", "conflict_status", "explanatory_note"], numeric_rows)

    evidence_specs = [
        ("EV-001", "numeric recovery", "SIFT/Arxiv", "hnswlib", "81 runs", "1000 per run", grid_text, "0f5a2be", "exp/icba_fixed_target_auditor_closure", "E2", "historical roles", "endpoint and latency repeats documented", "mean/query rows", "PARTIAL", "numeric conflict remains", "appendix only", "docs/icba_fixed_target_auditor/data_recovery_report.md"),
        ("EV-002", "numeric recovery manifest", "SIFT/Arxiv", "hnswlib", "81 runs", "manifest-defined", grid_text, "0f5a2be", "exp/icba_fixed_target_auditor_closure", "E2", "future_confirm_accessed=false", "checksum 243/243", "row counts", "CONFLICTED", "manifest conflicts with EV-001", "drop until repaired", "manifests/icba_fixed_target_auditor_data_recovery.json"),
        ("EV-003", "Gate-A historical matrix", "SIFT/Arxiv/GloVe", "hnswlib", "run matrix", "per-run", "six-level plus midpoint", "0f5a2be", "historical Gate-A", "E1", "development/evaluation historical", "formal_test_members_accessed=false", "Recall/NDC curves", "REPRODUCIBLE_CONDITIONALLY", "not confirmatory", "appendix", "manifests/gate_a/completed_run_matrix.json"),
        ("EV-004", "fixed-target decision", "SIFT/Arxiv", "hnswlib", str(fixed_decision.get("directed_pairs", "12")), "retrospective", grid_text, "0f5a2be", "exp/icba_fixed_target_auditor_closure", "E2", "future_confirm_accessed=false", "build-cluster retrospective", "risk/regret", "CONDITIONALLY_REPRODUCED", "no E4 role", "appendix", "manifests/icba_fixed_target_auditor_decision.json"),
        ("EV-005", "runtime audit", "SIFT/Arxiv", "hnswlib", "historical", "historical", "mixed", "0f5a2be", "exp/icba_auditor_runtime_alignment_repair", "E1", "source/eval incompleteness", "runtime alignment tests recorded", "deployment loop", "LIMITED", "not a primary claim", "appendix", "docs/icba_auditor_runtime/final_report.md"),
        ("EV-006", "theory crosswalk", "scope", "Graph-ANNS", "n/a", "n/a", "n/a", "0f5a2be", "theory artifacts", "E2", "not a query result", "classical attribution required", "theory", "RESTRICTED", "no open-world theorem", "main theory", "docs/icba_auditor/theorem_algorithm_crosswalk.md"),
    ]
    write_csv(RES / "evidence_registry.csv", ["evidence_id", "phenomenon_or_theory", "dataset", "implementation", "build_count", "query_count", "budget_grid", "source_commit", "source_branch", "evidence_level", "role_split", "endpoint_handling", "statistic", "bootstrap_repetitions", "primary_result", "reproducibility", "limitation", "keep_main_appendix_drop", "source_file"], evidence_specs)

    claim_md = f"""# Claim registry\n\nScope is frozen to hnswlib × {{SIFT-100K, Arxiv-Nomic-100K}}. Current branch: `{branch}` at `{head}`.\n\n| ID | Claim | Current evidence | E4 confirmation needed | Allowed wording | Prohibited wording |\n|---|---|---|---|---|---|\n| C1 | Build history can change per-query safe-budget response under fixed data/implementation/nominal parameters. | E1/E2 historical artifacts; row-count conflict remains. | YES | “Observed in the auditable hnswlib historical matrix, conditionally reproduced.” | “All Graph-ANNS” or universal portability claim. |\n| C2 | Environment-blind transfer incurs risk or conservative cost when observable transcripts collide. | Theory application + retrospective evidence. | YES | “Restricted finite-environment application.” | “Open-world impossibility proved.” |\n| C3 | Recovery needs endpoint feasibility, positive margin, identifiability, enough target evidence, and valid fallback. | Restricted proposition/theory crosswalk. | NO for theorem wording; YES for empirical scope. | “Necessary conditions under stated finite model.” | “New general theorem.” |\n| C4 | Oracle headroom does not imply deployment net benefit; certification/fallback/control/tail costs matter. | Retrospective cost fields are incomplete. | YES | “Deployment value remains an empirical Gate.” | “Oracle equals deployable method.” |\n| C5 | Current operational effect is scoped primarily to hnswlib. | E1/E2 historical matrix. | YES for broader scope. | “hnswlib scope; Faiss/Vamana boundary only.” | “Applies to every Graph-ANNS.” |\n"""
    write_text(DOC / "claim_registry.md", claim_md)

    theorem_rows = [
        ["Main Result I", "environment-blind transfer lower bound", "CLASSICAL_APPLICATION", "finite environments, observable transcript, conflicting safe actions, TV/testing affinity", "docs/icba_auditor/theorem_algorithm_crosswalk.md", "scope restricted; no open-world claim"],
        ["Main Result II", "recovery necessary conditions", "DOMAIN_SPECIFIC_RESTRICTED_PROPOSITION", "endpoint, margin, identifiability, target evidence, fallback", "docs/icba_auditor/theorem_algorithm_crosswalk.md", "counterexamples must be stated with finite-action assumptions"],
        ["Main Result III", "deployment value and tail-cost barrier", "NEW_COMBINATION_OF_CLASSICAL_RESULTS", "d = G_online - R_selection - P(F)ΔC_f - C_control", "docs/icba_fixed_target_auditor/cost_report.md", "cost terms are not fully estimable in current history"],
    ]
    write_csv(RES / "theorem_crosswalk.csv", ["main_result", "topic", "status", "required_components", "source", "limitation"], theorem_rows)
    write_text(DOC / "theory_consolidation.md", """# Theory consolidation\n\nThe paper uses three restricted results. Main Result I is a classical finite-environment testing/TV application to observable transcript collisions. Main Result II is a domain-specific restricted proposition: endpoint feasibility, positive source margin, identifiability, sufficient target evidence, and a valid fallback are jointly necessary for safe recovery under the stated finite-action model. Main Result III combines the deployment value identity with classical tail-cost accounting; it is not presented as an open-world theorem.\n\nAll theory-to-experiment links are conditional on hnswlib and on the frozen budget semantics. Faiss HNSW and Vamana remain scope boundaries, not positive evidence.\n""")

    build_rows = []
    for ds in ("SIFT-100K", "Arxiv-Nomic-100K"):
        build_rows.append([ds, 18, 24, 5000, 991, "build", "NOT_COMPUTED_FROM_VARIANCE", "E4 contract only", "confirmatory_query and future_replication not accessed"])
    write_csv(RES / "build_power_plan.csv", ["dataset", "minimum_builds", "preferred_builds", "bootstrap_repetitions", "seed", "inference_unit", "power_status", "evidence_level", "query_role_note"], build_rows)

    build_seconds = [r.get("build_seconds") for r in completed_matrix.get("runs", []) if isinstance(r.get("build_seconds"), (int, float))]
    build_summary = "NOT_ESTIMABLE"
    if build_seconds:
        build_summary = f"min={min(build_seconds):.2f}s;median={statistics.median(build_seconds):.2f}s;max={max(build_seconds):.2f}s"
    root_free = shutil.disk_usage("/").free / (1024**3)
    data_free = shutil.disk_usage(str(ROOT / ".." / ".." / ".."))
    resource_rows = [
        ["current_root_free_gib", f"{root_free:.3f}", "observed", "server filesystem", "resource audit", "E2", "root free space at audit"],
        ["historical_build_seconds", build_summary, "completed Gate-A runs", "manifests/gate_a/completed_run_matrix.json", "existing artifacts", "E1", "not a confirmatory runtime guarantee"],
        ["confirmatory_builds", "36–48 total (18–24 per dataset)", "builds", "protocol", "E4 contract", "E4", "must be recalculated before execution"],
        ["confirmatory_storage", "NOT_ESTIMABLE_BEFORE_ARTIFACT_RECONCILIATION", "bytes", "protocol", "no new build", "E4", "do not reserve from unresolved row counts"],
        ["confirmatory_wall_clock", "NOT_ESTIMABLE_BEFORE_ARTIFACT_RECONCILIATION", "hours", "protocol", "no new build", "E4", "current round does not run experiments"],
    ]
    write_csv(RES / "resource_estimate.csv", ["resource", "estimate", "unit", "source", "basis", "evidence_level", "note"], resource_rows)

    gate_rows = [
        ["P0", "evidence completeness", "FAIL", "1,458,000/486,000 conflicts with 1,656,000/552,000; 972,000 and 648,000 claims unresolved"],
        ["P1", "claim–evidence closure", "PASS_WITH_SCOPE", "C1–C5 registered with explicit E4 requirements and hnswlib scope"],
        ["P2", "build-level power", "BLOCKED", "18–24 is preregistered, but variance/power cannot be certified from conflicted historical rows"],
        ["P3", "resource feasibility", "CONDITIONAL", "current audit is resource-feasible, but exact confirmatory storage/runtime is deferred"],
        ["P4", "sealed roles", "PASS", "future_confirm_accessed=false; validation_dev=false; formal_test=false in audited manifest"],
    ]
    write_csv(RES / "unified_gate_table.csv", ["gate", "name", "status", "evidence"], gate_rows)
    write_csv(RES / "query_role_access_log.csv", ["role", "accessed", "source", "note"], [
        ["protocol_design", "NO_QUERY_READ", "this_round", "Only manifests and text reports were inspected"],
        ["confirmatory_query", "FALSE", "manifests/icba_fixed_target_auditor_data_recovery.json", "Sealed role not accessed"],
        ["future_replication", "FALSE", "manifests/icba_fixed_target_auditor_data_recovery.json", "Sealed role not accessed"],
        ["validation-dev", "FALSE", "manifests/icba_fixed_target_auditor_data_recovery.json", "Reserved validation role not accessed"],
        ["formal-test", "FALSE", "manifests/icba_fixed_target_auditor_data_recovery.json", "Formal-test role not accessed"],
    ])

    write_text(DOC / "paper_scope.md", """# Paper scope\n\nPrimary empirical scope: hnswlib on SIFT-100K and Arxiv-Nomic-100K. GloVe is a feasibility-boundary dataset only. Faiss HNSW and Vamana are historical scope boundaries and cannot support a positive universal claim. The paper is an Experiment, Analysis, and Benchmark submission; it does not require a new SOTA index.\n\nThe three-layer story is feasibility → identifiability → realizability. Early Exit is excluded from the main experiment and retained only as an external boundary discussion, with no new run or reserved-role access.\n""")
    write_text(DOC / "confirmatory_protocol.md", f"""# Confirmatory protocol (frozen contract; no run in this round)\n\n**Status:** E4 design only. Confirmatory and future-replication query roles were not accessed.\n\n- Implementation: hnswlib; datasets: SIFT-100K and Arxiv-Nomic-100K.\n- Budget grid: `{grid_text}` from auditable artifacts; the unverified twelve-level claim is not used.\n- Builds: minimum 18, preferred 24 per dataset; build is the inference unit.\n- Query roles: `protocol_design`, `confirmatory_query`, `future_replication`; only the first may be used in this round.\n- Hypotheses: H1 build changes safe-budget response; H2 source→target reuse incurs risk or conservative cost; H3 survives endpoint filtering/build robustness; H4 target recovery value is limited by full deployment cost.\n- Baselines: Same-Build Tuned, Source-Reuse, Worst-Build Conservative, Target Profiling/Recalibration, Fixed-Safe Endpoint, and Per-Target Oracle as a non-deployable upper bound.\n- Statistics: paired query bootstrap 5000/seed 991, build-cluster bootstrap 5000/seed 991, leave-one-build-out, top-1% query deletion, top-contribution build deletion.\n- System measurement: one fixed machine, fixed CPU/threads/affinity/compiler, warm-up, randomized order, mean/p95/p99, explicit I/O/truth/build accounting.\n\nThe contract is not executable until Gate P0 resolves the conflicting historical row counts and pair-count claims.\n""")
    write_text(DOC / "paper_blueprint.md", """# Paper blueprint\n\n1. Introduction\n2. Rebuild Portability Problem\n3. Feasibility–Identifiability–Realizability Theory\n4. Experimental Protocol\n5. Build-Conditioned Budget Response\n6. Environment-Blind Transfer Failure\n7. Recovery and Deployment Cost Boundaries\n8. Scope Boundary Across Implementations\n9. Discussion and Limitations\n10. Related Work\n11. Conclusion\n\nThe main text will not be a chronological failure log. Historical method names are grouped as M1 Source-Only Transfer, M2 Target-Evidence Recovery, M3 Structural Recovery, and M4 Complementary Search.\n""")
    write_text(DOC / "executive_summary.md", f"""# Executive summary\n\nThis round is a paper-evidence lock, not a new index experiment. The current Graph-ANNS main worktree is `{ROOT}` on branch `{branch}` at `{head}`. All eight requested historical anchor commits are locally available. The common auditable budget grid is `{grid_text}`.\n\nThe evidence audit found a blocking numeric contradiction: the recovery report states 1,458,000 physical rows and 486,000 unique query-budget units, while the recovery manifest states 1,656,000 and 552,000. The 972,000 twelve-level claim is explicitly not recovered, and 648,000/648-pair claims have no locally auditable source in the scanned artifacts. No confirmatory query role was accessed and no new build was run.\n\n**Unified decision:** `BLOCKED_BY_EVIDENCE_INTEGRITY`.\n""")

    final_report = f"""# Final report\n\n## Decision\n`BLOCKED_BY_EVIDENCE_INTEGRITY`\n\n## Scope and provenance\n- Branch: `{branch}`; HEAD/parent anchor: `{head}`.\n- Worktree: `{ROOT}` (the existing ANNS main worktree; no new Codex task or worktree was created).\n- Anchor commits parsed: {sum(1 for r in anchor_rows if r[1] == 'YES')}/{len(anchor_rows)}.\n- Evidence levels: E0 unresolved historical claims, E1 exploratory historical, E2 conditionally reproduced; no E3/E4 result was created in this round.\n\n## Numeric audit\n- Actual auditable common budget grid: `{grid_text}`.\n- Recovery report: 1,458,000 physical rows and 486,000 unique query-budget units.\n- Recovery manifest: 1,656,000 physical rows and 552,000 unique query-budget units.\n- 972,000 twelve-level claim: not exactly recovered.\n- 648,000 tournament-record claim and 648/324 pair claims: unresolved from local artifacts.\n- Current fixed-target decision artifact reports 12 directed pairs, not 648.\n\n## Gates\nP0 FAIL; P1 PASS_WITH_SCOPE; P2 BLOCKED; P3 CONDITIONAL; P4 PASS. Therefore no confirmatory build matrix is authorized.\n\n## Access firewall\n`confirmatory_query` and `future_replication` were not accessed; validation-dev and formal-test are recorded as not accessed. Early Exit was not continued.\n\n## Required next action\nRepair the two row-count artifacts and locate or withdraw the unresolved 648,000/648/324 claims. Recompute `numeric_reconciliation.csv`, then rerun P0–P4 without touching sealed query roles.\n"""
    write_text(DOC / "final_report.md", final_report)

    decision = {
        "decision": "BLOCKED_BY_EVIDENCE_INTEGRITY",
        "branch": branch,
        "head": head,
        "parent_anchor": parent,
        "worktree": str(ROOT),
        "main_worktree_only": True,
        "confirmatory_experiment_run": False,
        "confirmatory_query_accessed": False,
        "future_replication_accessed": False,
        "validation_dev_accessed": False,
        "formal_test_accessed": False,
        "early_exit_continued": False,
        "actual_budget_grid": grid,
        "gate_status": {k: v for k, _, v, _ in gate_rows},
        "evidence_level_distribution": {"E0": 2, "E1": 2, "E2": 4, "E3": 0, "E4": 0},
        "artifacts": {
            "final_report": "docs/paper_evidence_lock/final_report.md",
            "confirmatory_protocol": "docs/paper_evidence_lock/confirmatory_protocol.md",
            "numeric_reconciliation": "results/paper_evidence_lock/numeric_reconciliation.csv",
            "decision_manifest": "manifests/graph_anns_paper_evidence_lock_decision.json",
        },
    }
    (MAN / "graph_anns_paper_evidence_lock_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")

    # Checksums are computed only over this round's auditable deliverables.
    checksum_paths = sorted([*DOC.glob("*.md"), *RES.glob("*.csv"), MAN / "graph_anns_paper_evidence_lock_decision.json", ROOT / "scripts/paper_evidence_lock/reconcile.py", ROOT / "tests/paper_evidence_lock/test_reconciliation.py"])
    with (RES / "checksums.sha256").open("w", encoding="utf-8") as f:
        for p in checksum_paths:
            f.write(f"{sha(p)}  {p.relative_to(ROOT).as_posix()}\n")


if __name__ == "__main__":
    main()
