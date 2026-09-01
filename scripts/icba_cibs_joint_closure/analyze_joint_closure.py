#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
from scipy.stats import beta, hypergeom


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/icba_cibs_joint_closure"
DOC = ROOT / "docs/icba_cibs_joint_closure"
DATASETS = ("sift_100k", "arxiv_nomic_100k")
BUILDS = ("G1", "G2", "G3")
EFS = (10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512)
R = 5000
SEED = 991


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[dict], fields: Optional[List[str]] = None) -> None:
    if not rows and fields is None:
        raise ValueError("empty rows need explicit fields")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def cp_bounds(x: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    lo = 0.0 if x == 0 else float(beta.ppf(alpha, x, n - x + 1))
    hi = 1.0 if x == n else float(beta.ppf(1 - alpha, x + 1, n - x))
    return lo, hi


def percentile_interval(values: np.ndarray) -> Tuple[float, float]:
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def eval_rows(dataset: str, build: str, ef: int) -> List[dict]:
    path = ROOT / f"results/icba_cibs_stage1/evaluation/{dataset}__{build}__evaluation_all_actions.csv"
    rows = [row for row in read_csv(path) if int(row["requested_ef"]) == ef]
    rows.sort(key=lambda row: int(row["query_row"]))
    if len(rows) != 500 or [int(r["query_row"]) for r in rows] != list(range(500)):
        raise AssertionError(f"invalid paired evaluation rows {dataset} {build} {ef}")
    return rows


def arrays(rows: List[dict]) -> Dict[str, np.ndarray]:
    return {
        "recall": np.asarray([float(r["raw_recall_at_10"]) for r in rows]),
        "failure": np.asarray([int(r["Z_abs"]) for r in rows]),
        "ndc": np.asarray([int(r["native_ndc"]) for r in rows]),
        "wall": np.asarray([int(r["wall_clock_ns"]) for r in rows]),
        "endpoint": np.asarray([0 if r["endpoint_status"] == "PASS" else 1 for r in rows]),
    }


def bootstrap_compare(a: Dict[str, np.ndarray], b: Dict[str, np.ndarray], seed_offset: int) -> dict:
    rng = np.random.default_rng(SEED + seed_offset)
    n = len(a["ndc"])
    recall, gain, p95, endpoint, wall = [], [], [], [], []
    for _ in range(R):
        idx = rng.integers(0, n, size=n)
        ma = float(np.mean(a["ndc"][idx]))
        mb = float(np.mean(b["ndc"][idx]))
        recall.append(float(np.mean(a["recall"][idx] - b["recall"][idx])))
        gain.append((mb - ma) / mb)
        p95.append(float(np.percentile(a["ndc"][idx], 95) - np.percentile(b["ndc"][idx], 95)))
        endpoint.append(float(np.mean(a["endpoint"][idx] - b["endpoint"][idx])))
        wall.append((float(np.mean(b["wall"][idx])) - float(np.mean(a["wall"][idx]))) / float(np.mean(b["wall"][idx])))
    return {
        "recall": percentile_interval(np.asarray(recall)),
        "gain": percentile_interval(np.asarray(gain)),
        "p95": percentile_interval(np.asarray(p95)),
        "endpoint": percentile_interval(np.asarray(endpoint)),
        "wall": percentile_interval(np.asarray(wall)),
    }


def finite_population_upper(x: int, n: int, population: int, alpha: float = 0.05) -> float:
    accepted = [k for k in range(population + 1) if hypergeom.cdf(x, population, k, n) > alpha]
    return max(accepted) / population if accepted else 0.0


def action_geometry() -> Tuple[List[dict], dict]:
    selected = load_json(ROOT / "manifests/icba_cibs_stage1_selected_actions.json")
    cert = load_json(ROOT / "results/icba_cibs_stage1/sentinel/sentinel_procedure_certificate.json")
    cost = load_json(ROOT / "results/icba_cibs_stage1/analysis/cost_ledger.json")
    sent = {
        ds: {a["action_id"]: a["statistics"] for a in cert["actions"][ds]}
        for ds in DATASETS
    }
    all_rows, arrays_by_dataset = [], {}
    for dsi, dataset in enumerate(DATASETS):
        b1_id = selected["datasets"][dataset]["B1"]["action_id"]
        b1_build, b1_ef = b1_id.split(":ef=")
        b1 = arrays(eval_rows(dataset, b1_build, int(b1_ef)))
        extra_fixed = cost["datasets"][dataset]["incremental_B4_vs_B1"]["extra_fixed_wall_clock_ns"]
        arrays_by_dataset[dataset] = {"B1": b1, "actions": {}}
        for bi, build in enumerate(BUILDS):
            for ei, ef in enumerate(EFS):
                action_id = f"{build}:ef={ef}"
                a = arrays(eval_rows(dataset, build, ef))
                arrays_by_dataset[dataset]["actions"][action_id] = a
                boot = bootstrap_compare(a, b1, dsi * 100 + bi * 20 + ei)
                failures = int(np.sum(a["failure"]))
                risk_l, risk_u = cp_bounds(failures, 500)
                recall_delta = float(np.mean(a["recall"] - b1["recall"]))
                mean_a, mean_b = float(np.mean(a["ndc"])), float(np.mean(b1["ndc"]))
                gain = (mean_b - mean_a) / mean_b
                p95_delta = float(np.percentile(a["ndc"], 95) - np.percentile(b1["ndc"], 95))
                endpoint_delta = float(np.mean(a["endpoint"] - b1["endpoint"]))
                wall_gain = (float(np.mean(b1["wall"])) - float(np.mean(a["wall"]))) / float(np.mean(b1["wall"]))
                saving = float(np.mean(b1["wall"])) - float(np.mean(a["wall"]))
                break_even = math.ceil(extra_fixed / saving) if saving > 0 else None
                s = sent[dataset][action_id]
                point = {
                    "sentinel": bool(s["certified"]),
                    "recall": recall_delta >= -0.001,
                    "gain": gain >= 0.01,
                    "p95": p95_delta <= 0,
                    "endpoint": endpoint_delta <= 0,
                    "break_even": break_even is not None,
                }
                ci = {
                    "sentinel": bool(s["certified"]),
                    "recall": boot["recall"][0] >= -0.001,
                    "gain": boot["gain"][0] >= 0.01,
                    "p95": boot["p95"][1] <= 0,
                    "endpoint": boot["endpoint"][1] <= 0,
                    "break_even": break_even is not None and break_even <= 10_000_000,
                }
                first_point = next((k for k in ("sentinel", "recall", "gain", "p95", "endpoint", "break_even") if not point[k]), "PASS")
                first_ci = next((k for k in ("sentinel", "recall", "gain", "p95", "endpoint", "break_even") if not ci[k]), "PASS")
                all_rows.append({
                    "dataset": dataset,
                    "action_id": action_id,
                    "build": build,
                    "raw_ef": ef,
                    "is_B1": action_id == b1_id,
                    "is_frozen_CIBS": action_id == selected["datasets"][dataset]["B4_CIBS_FIXED"]["action_id"],
                    "sentinel_failures": s["failures"],
                    "sentinel_risk_ucb": s["risk_cp_ucb"],
                    "simultaneously_certified": s["certified"],
                    "evaluation_recall": float(np.mean(a["recall"])),
                    "recall_delta_vs_B1": recall_delta,
                    "recall_delta_ci_low": boot["recall"][0],
                    "recall_delta_ci_high": boot["recall"][1],
                    "evaluation_failures": failures,
                    "evaluation_failure_rate": failures / 500,
                    "evaluation_risk_lcb": risk_l,
                    "evaluation_risk_ucb": risk_u,
                    "evaluation_risk_wording": "INDEPENDENT_RISK_UCB_PASS" if risk_u <= 0.05 else ("NO_CLEAR_CONTRADICTION_WITH_SENTINEL_CERTIFICATE" if risk_l <= 0.05 else "EVALUATION_RISK_UNCERTAIN"),
                    "mean_ndc": mean_a,
                    "mean_ndc_gain_vs_B1": gain,
                    "mean_ndc_gain_ci_low": boot["gain"][0],
                    "mean_ndc_gain_ci_high": boot["gain"][1],
                    "p95_ndc": float(np.percentile(a["ndc"], 95)),
                    "p95_delta_vs_B1": p95_delta,
                    "p95_delta_ci_low": boot["p95"][0],
                    "p95_delta_ci_high": boot["p95"][1],
                    "p95_point_pass": p95_delta <= 0,
                    "p95_ci_supported_pass": boot["p95"][1] <= 0,
                    "wall_clock_gain_vs_B1": wall_gain,
                    "wall_clock_gain_ci_low": boot["wall"][0],
                    "wall_clock_gain_ci_high": boot["wall"][1],
                    "endpoint_infeasibility": float(np.mean(a["endpoint"])),
                    "endpoint_delta_vs_B1": endpoint_delta,
                    "endpoint_delta_ci_low": boot["endpoint"][0],
                    "endpoint_delta_ci_high": boot["endpoint"][1],
                    "offline_portfolio_cost_ns": extra_fixed,
                    "break_even_queries": break_even if break_even is not None else "NO_FINITE_BREAK_EVEN",
                    "point_joint_pass": all(point.values()),
                    "ci_joint_pass": all(ci.values()),
                    "first_point_gate_failure": first_point,
                    "first_ci_gate_failure": first_ci,
                    "bootstrap_replicates": R,
                    "bootstrap_seed": SEED,
                })
    return all_rows, arrays_by_dataset


def pareto(rows: List[dict]) -> List[dict]:
    out = []
    for dataset in DATASETS:
        ds = [r for r in rows if r["dataset"] == dataset]
        for row in ds:
            dominated = any(
                other is not row
                and other["evaluation_recall"] >= row["evaluation_recall"]
                and other["mean_ndc"] <= row["mean_ndc"]
                and other["p95_ndc"] <= row["p95_ndc"]
                and other["evaluation_risk_ucb"] <= row["evaluation_risk_ucb"]
                and (
                    other["evaluation_recall"] > row["evaluation_recall"]
                    or other["mean_ndc"] < row["mean_ndc"]
                    or other["p95_ndc"] < row["p95_ndc"]
                    or other["evaluation_risk_ucb"] < row["evaluation_risk_ucb"]
                )
                for other in ds
            )
            out.append({
                "dataset": dataset,
                "action_id": row["action_id"],
                "pareto_nondominated": not dominated,
                "simultaneously_certified": row["simultaneously_certified"],
                "point_joint_pass": row["point_joint_pass"],
                "ci_joint_pass": row["ci_joint_pass"],
                "evaluation_recall": row["evaluation_recall"],
                "evaluation_risk_ucb": row["evaluation_risk_ucb"],
                "mean_ndc": row["mean_ndc"],
                "p95_ndc": row["p95_ndc"],
                "wall_clock_gain_vs_B1": row["wall_clock_gain_vs_B1"],
                "break_even_queries": row["break_even_queries"],
            })
    return out


def decomposition(rows: List[dict]) -> List[dict]:
    selected = load_json(ROOT / "manifests/icba_cibs_stage1_selected_actions.json")
    lookup = {(r["dataset"], r["action_id"]): r for r in rows}
    result = []
    for dataset in DATASETS:
        b1 = selected["datasets"][dataset]["B1"]["action_id"]
        cibs = selected["datasets"][dataset]["B4_CIBS_FIXED"]["action_id"]
        b1_build, b1_ef = b1.split(":ef="); b1_ef = int(b1_ef)
        c_build, c_ef = cibs.split(":ef="); c_ef = int(c_ef)
        C = lambda build, ef: float(lookup[(dataset, f"{build}:ef={ef}")]["mean_ndc"])
        total = C(b1_build, b1_ef) - C(c_build, c_ef)
        lower = C(b1_build, b1_ef) - C(b1_build, c_ef)
        build_at_b1 = C(b1_build, b1_ef) - C(c_build, b1_ef)
        interaction = (C(b1_build, c_ef) - C(c_build, c_ef)) - build_at_b1
        if abs((lower + build_at_b1 + interaction) - total) > 1e-8:
            raise AssertionError("decomposition identity")
        recall_drop = lookup[(dataset, cibs)]["recall_delta_vs_B1"] < 0
        result.append({
            "dataset": dataset,
            "B1_action": b1,
            "CIBS_action": cibs,
            "total_ndc_saving": total,
            "lower_ef_effect": lower,
            "build_effect_at_B1_ef": build_at_b1,
            "interaction": interaction,
            "lower_ef_share_of_total": lower / total if total else 0.0,
            "build_share_of_total": build_at_b1 / total if total else 0.0,
            "interaction_share_of_total": interaction / total if total else 0.0,
            "recall_declined": recall_drop,
            "mechanism_label": "GAIN_DOMINATED_BY_QUALITY_SLACK_CONSUMPTION" if total > 0 and lower / total > 0.5 and recall_drop else "BUILD_OR_MIXED_EFFECT",
        })
    return result


def finite_pool_audit(rows: List[dict]) -> dict:
    population, n = 1000, 256
    observed = sorted({int(r["sentinel_failures"]) for r in rows})
    table = []
    all_conservative = True
    for x in range(n + 1):
        _, cp_u = cp_bounds(x, n, alpha=0.05 / 36)
        hg_u = finite_population_upper(x, n, population, alpha=0.05 / 36)
        all_conservative &= cp_u + 1e-12 >= hg_u
        if x in observed:
            table.append({"failures": x, "binomial_cp_ucb": cp_u, "finite_population_hypergeom_ucb": hg_u, "cp_is_conservative": cp_u + 1e-12 >= hg_u})
    return {
        "population": population,
        "sample_without_replacement": n,
        "alpha_per_action": 0.05 / 36,
        "all_x_0_to_n_checked": True,
        "cp_ucb_ge_hypergeom_ucb_for_all_x": all_conservative,
        "status": "FINITE_POOL_CP_CONSERVATIVE_VERIFIED" if all_conservative else "FINITE_POOL_CERTIFICATION_SEMANTICS_UNRESOLVED",
        "observed_failure_rows": table,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOC.mkdir(parents=True, exist_ok=True)
    rows, _ = action_geometry()
    write_csv(OUT / "all_action_geometry.csv", rows)
    feasible = [{k: r[k] for k in ("dataset", "action_id", "simultaneously_certified", "point_joint_pass", "ci_joint_pass", "first_point_gate_failure", "first_ci_gate_failure", "break_even_queries")} for r in rows]
    write_csv(OUT / "joint_feasible_sets.csv", feasible)
    write_csv(OUT / "pareto_front.csv", pareto(rows))
    write_csv(OUT / "gain_decomposition.csv", decomposition(rows))
    finite = finite_pool_audit(rows)
    (OUT / "finite_pool_audit.json").write_text(json.dumps(finite, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    qni = []
    for dataset in DATASETS:
        ds = [r for r in rows if r["dataset"] == dataset]
        qni.append({
            "dataset": dataset,
            "sentinel_deployable_point_actions": sum(bool(r["point_joint_pass"]) for r in ds),
            "sentinel_deployable_ci_actions": sum(bool(r["ci_joint_pass"]) for r in ds),
            "evaluation_oracle_best_ci_action": min((r for r in ds if r["ci_joint_pass"]), key=lambda r: r["mean_ndc"], default=None)["action_id"] if any(r["ci_joint_pass"] for r in ds) else "NONE",
            "oracle_is_deployable": False,
        })
    write_csv(OUT / "cibs_qni_counterfactual.csv", qni)


if __name__ == "__main__":
    main()
