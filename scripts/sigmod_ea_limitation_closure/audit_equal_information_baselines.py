#!/usr/bin/env python3
"""Audit simple baselines under the frozen Recall@10=.95 refresh protocol.

This is a post-hoc, frozen-response attribution audit.  It performs no search,
index construction, tuning, or access to a new query role.  The registered TCP
lane must reproduce the paper's compact paired arrays before any new comparison
is accepted.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np


ALPHA_SELECT = 0.05
ALPHA_CANDIDATE = 0.025
ALPHA_ENDPOINT = 0.025
LIMIT = 0.05
REPS = 5000
BOOTSTRAP_SEED = 991


def load_frozen_module(repo: Path):
    path = repo / "scripts/graph_anns_phase3_ea85/analyze_phase2_refresh95.py"
    spec = importlib.util.spec_from_file_location("refresh95", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def target_global_action(module, selection_recalls: np.ndarray) -> int:
    """Smallest native action passing a selection-only CP screen."""
    for idx in range(len(module.EFS)):
        failures = int(np.sum(selection_recalls[idx] < 0.95))
        if module.cp_upper(failures, selection_recalls.shape[1], 1 - ALPHA_SELECT) <= LIMIT:
            return idx
    return len(module.EFS) - 1


def source_global_action(module, source_selection: dict[int, np.ndarray], target_seed: int) -> int:
    """Smallest action passing separately on every leave-one-target source build."""
    for idx in range(len(module.EFS)):
        passes = []
        for seed, recalls in source_selection.items():
            if seed == target_seed:
                continue
            failures = int(np.sum(recalls[idx] < 0.95))
            ucb = module.cp_upper(failures, recalls.shape[1], 1 - ALPHA_SELECT)
            passes.append(ucb <= LIMIT)
        if passes and all(passes):
            return idx
    return len(module.EFS) - 1


def certify_and_execute(module, cert_candidate_idx: np.ndarray,
                        eval_candidate_idx: np.ndarray, cert_r: np.ndarray,
                        eval_r: np.ndarray, eval_d: np.ndarray) -> dict:
    endpoint_idx = np.full(cert_r.shape[1], len(module.EFS) - 1, dtype=int)
    candidate_cert, _ = module.outcomes(
        cert_r, np.empty_like(cert_r), cert_candidate_idx
    )
    endpoint_cert, _ = module.outcomes(cert_r, np.empty_like(cert_r), endpoint_idx)
    candidate_failures = int(np.sum(candidate_cert < 0.95))
    endpoint_failures = int(np.sum(endpoint_cert < 0.95))
    candidate_ucb = module.cp_upper(candidate_failures, candidate_cert.size, 1 - ALPHA_CANDIDATE)
    endpoint_ucb = module.cp_upper(endpoint_failures, endpoint_cert.size, 1 - ALPHA_ENDPOINT)
    candidate_ok = candidate_ucb <= LIMIT
    endpoint_ok = endpoint_ucb <= LIMIT
    if candidate_ok and endpoint_ok:
        deploy_idx = eval_candidate_idx
        action = "CANDIDATE"
    else:
        deploy_idx = np.full(eval_r.shape[1], len(module.EFS) - 1, dtype=int)
        action = "ENDPOINT" if endpoint_ok else "UNQUALIFIED_ENDPOINT"
    recalls, dists = module.outcomes(eval_r, eval_d, deploy_idx)
    return {
        "recalls": recalls,
        "dists": dists,
        "candidate_failures": candidate_failures,
        "candidate_ucb": candidate_ucb,
        "endpoint_failures": endpoint_failures,
        "endpoint_ucb": endpoint_ucb,
        "candidate_accepted": candidate_ok,
        "qualified": candidate_ok or endpoint_ok,
        "action": action,
    }


def crossed_draws(arrays: dict[str, np.ndarray], reps: int = REPS,
                  seed: int = BOOTSTRAP_SEED) -> dict[str, np.ndarray]:
    """Product bootstrap over target builds and shared query IDs."""
    rng = np.random.default_rng(seed)
    builds, queries = next(iter(arrays.values())).shape
    output = {key: np.empty(reps, dtype=float) for key in arrays}
    for start in range(0, reps, 100):
        count = min(100, reps - start)
        build_weights = rng.multinomial(builds, np.ones(builds) / builds, size=count) / builds
        query_weights = rng.multinomial(queries, np.ones(queries) / queries, size=count) / queries
        for key, values in arrays.items():
            output[key][start:start + count] = np.einsum(
                "ij,ij->i", build_weights @ values, query_weights
            )
    return output


def interval(values: np.ndarray) -> list[float]:
    return [float(x) for x in np.quantile(values, [0.025, 0.975])]


def analyze(repo: Path, replay: Path, output: Path) -> dict:
    module = load_frozen_module(repo)
    expected = len(module.DATASETS) * 2 * len(module.SEEDS) * len(module.ROLES) * len(module.EFS)
    actual = sum(1 for _ in replay.rglob("ef_*.csv"))
    if actual != expected or (replay / "STATUS").read_text().strip() != "COMPLETE":
        raise RuntimeError(f"incomplete frozen replay: {actual}/{expected}")

    paper_arrays = repo / "paper/sigmod2027/evidence/w6_audit"
    per_build: list[dict] = []
    summaries: list[dict] = []
    decisions: dict[str, dict] = {}
    reproduction: list[dict] = []

    for dataset in module.DATASETS:
        source_minima = {role: {} for role in module.ROLES}
        source_selection: dict[int, np.ndarray] = {}
        target: dict[tuple[int, str], tuple[np.ndarray, np.ndarray]] = {}
        for role in module.ROLES:
            for seed in module.SEEDS:
                _, old_r, _ = module.load_tensor(replay, dataset, "old", seed, role)
                source_minima[role][seed] = module.minimal_action_indices(old_r)
                if role == "selection":
                    source_selection[seed] = old_r
                _, target_r, target_d = module.load_tensor(
                    replay, dataset, "target_refresh05", seed, role
                )
                target[seed, role] = (target_r, target_d)

        method_arrays = {
            name: {"dists": [], "risk": []}
            for name in ("ENDPOINT", "SOURCE_GLOBAL", "TARGET_GLOBAL", "TCP_REGISTERED")
        }

        for seed in module.SEEDS:
            selection_r, _ = target[seed, "selection"]
            cert_r, _ = target[seed, "certification"]
            eval_r, eval_d = target[seed, "cold_evaluation"]
            base = {
                role: module.source_pool_indices(source_minima[role], seed)
                for role in module.ROLES
            }
            shift, _, _ = module.choose_shift(selection_r, base["selection"])
            tcp_idx = module.shift_indices(base["cold_evaluation"], shift)
            target_idx_value = target_global_action(module, selection_r)
            source_idx_value = source_global_action(module, source_selection, seed)
            candidate_indices = {
                "ENDPOINT": np.full(eval_r.shape[1], len(module.EFS) - 1, dtype=int),
                "SOURCE_GLOBAL": np.full(eval_r.shape[1], source_idx_value, dtype=int),
                "TARGET_GLOBAL": np.full(eval_r.shape[1], target_idx_value, dtype=int),
                "TCP_REGISTERED": tcp_idx,
            }
            cert_indices = {
                "ENDPOINT": np.full(cert_r.shape[1], len(module.EFS) - 1, dtype=int),
                "SOURCE_GLOBAL": np.full(cert_r.shape[1], source_idx_value, dtype=int),
                "TARGET_GLOBAL": np.full(cert_r.shape[1], target_idx_value, dtype=int),
                "TCP_REGISTERED": module.shift_indices(base["certification"], shift),
            }

            for method in candidate_indices:
                result = certify_and_execute(
                    module, cert_indices[method], candidate_indices[method],
                    cert_r, eval_r, eval_d
                )
                method_arrays[method]["dists"].append(result["dists"])
                method_arrays[method]["risk"].append(result["recalls"] < 0.95)
                per_build.append({
                    "dataset": dataset,
                    "seed": seed,
                    "method": method,
                    "selected_action": (
                        int(module.EFS[target_idx_value]) if method == "TARGET_GLOBAL" else
                        int(module.EFS[source_idx_value]) if method == "SOURCE_GLOBAL" else
                        "PER_QUERY_SHIFT_" + str(shift) if method == "TCP_REGISTERED" else
                        int(module.EFS[-1])
                    ),
                    "candidate_cert_failures": result["candidate_failures"],
                    "candidate_ucb_025": result["candidate_ucb"],
                    "endpoint_cert_failures": result["endpoint_failures"],
                    "endpoint_ucb_025": result["endpoint_ucb"],
                    "candidate_accepted": int(result["candidate_accepted"]),
                    "qualified": int(result["qualified"]),
                    "executed_action": result["action"],
                    "evaluation_risk": float(np.mean(result["recalls"] < 0.95)),
                    "mean_ndc": float(np.mean(result["dists"])),
                    "p95_ndc": float(np.quantile(result["dists"], 0.95)),
                    "p99_ndc": float(np.quantile(result["dists"], 0.99)),
                })

        stacked = {
            method: {
                key: np.stack(values) for key, values in payload.items()
            }
            for method, payload in method_arrays.items()
        }
        compact_name = "sift100k" if dataset == "sift100k" else "arxiv_nomic_100k"
        reference = np.load(paper_arrays / f"{compact_name}_paired_arrays.npz")
        tcp_reproduced = bool(
            np.array_equal(stacked["TCP_REGISTERED"]["dists"], reference["joint"])
            and np.array_equal(stacked["TCP_REGISTERED"]["risk"], reference["joint_risk"])
            and np.array_equal(stacked["ENDPOINT"]["dists"], reference["end"])
            and np.array_equal(stacked["ENDPOINT"]["risk"], reference["end_risk"])
        )
        reproduction.append({"dataset": dataset, "paper_joint_arrays_exact": tcp_reproduced})
        if not tcp_reproduced:
            raise RuntimeError(f"paper TCP reproduction failed for {dataset}")

        draw_inputs = {}
        for method, payload in stacked.items():
            draw_inputs[f"{method}_mean"] = payload["dists"]
            draw_inputs[f"{method}_risk"] = payload["risk"].astype(float)
        draws = crossed_draws(draw_inputs)
        endpoint_mean = float(stacked["ENDPOINT"]["dists"].mean())
        for method, payload in stacked.items():
            mean_ndc = float(payload["dists"].mean())
            risk = float(payload["risk"].mean())
            gain_draw = 1 - draws[f"{method}_mean"] / draws["ENDPOINT_mean"]
            summaries.append({
                "dataset": dataset,
                "method": method,
                "evaluation_risk": risk,
                "risk_ci_low": interval(draws[f"{method}_risk"])[0],
                "risk_ci_high": interval(draws[f"{method}_risk"])[1],
                "mean_ndc": mean_ndc,
                "mean_gain_vs_endpoint": 1 - mean_ndc / endpoint_mean,
                "gain_ci_low": interval(gain_draw)[0],
                "gain_ci_high": interval(gain_draw)[1],
                "p95_ndc": float(np.quantile(payload["dists"], 0.95)),
                "p99_ndc": float(np.quantile(payload["dists"], 0.99)),
                "accepted_builds": sum(
                    row["candidate_accepted"] for row in per_build
                    if row["dataset"] == dataset and row["method"] == method
                ),
            })

        tcp = stacked["TCP_REGISTERED"]["dists"]
        baseline = stacked["TARGET_GLOBAL"]["dists"]
        comparison_draw = 1 - draws["TCP_REGISTERED_mean"] / draws["TARGET_GLOBAL_mean"]
        build_gains = 1 - tcp.mean(axis=1) / baseline.mean(axis=1)
        lobo = [
            float(1 - np.delete(tcp, idx, axis=0).mean() /
                  np.delete(baseline, idx, axis=0).mean())
            for idx in range(len(module.SEEDS))
        ]
        decisions[dataset] = {
            "primary_comparator": "TARGET_GLOBAL",
            "comparison_is_post_hoc_frozen_response": True,
            "tcp_mean_gain_vs_target_global": float(1 - tcp.mean() / baseline.mean()),
            "tcp_gain_ci95": interval(comparison_draw),
            "tcp_p95_ratio_vs_target_global": float(
                np.quantile(tcp, 0.95) / np.quantile(baseline, 0.95)
            ),
            "tcp_p99_ratio_vs_target_global": float(
                np.quantile(tcp, 0.99) / np.quantile(baseline, 0.99)
            ),
            "tcp_risk": float(stacked["TCP_REGISTERED"]["risk"].mean()),
            "target_global_risk": float(stacked["TARGET_GLOBAL"]["risk"].mean()),
            "min_loto_gain": min(lobo),
            "delete_largest_gain": lobo[int(np.argmax(build_gains))],
            "tcp_accepted_builds": sum(
                row["candidate_accepted"] for row in per_build
                if row["dataset"] == dataset and row["method"] == "TCP_REGISTERED"
            ),
            "target_global_accepted_builds": sum(
                row["candidate_accepted"] for row in per_build
                if row["dataset"] == dataset and row["method"] == "TARGET_GLOBAL"
            ),
            "mean_advantage_positive": bool(interval(comparison_draw)[0] > 0),
            "p95_noninferior_5pct": bool(
                np.quantile(tcp, 0.95) / np.quantile(baseline, 0.95) <= 1.05
            ),
        }
        np.savez_compressed(
            output / f"{dataset}_arrays.npz",
            **{
                f"{method.lower()}_{key}": values
                for method, payload in stacked.items()
                for key, values in payload.items()
            },
        )

    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "per_build.csv", per_build)
    write_csv(output / "summary.csv", summaries)
    payload = {
        "status": "POST_HOC_FROZEN_RESPONSE_EQUAL_INFORMATION_BASELINE_AUDIT",
        "risk_event": "Recall@10 < 0.95",
        "target_roles": {"selection": 500, "certification": 500, "evaluation": 1000},
        "native_grid": [int(x) for x in module.EFS],
        "error_allocation": {
            "selection_screen": ALPHA_SELECT,
            "candidate_certification": ALPHA_CANDIDATE,
            "endpoint_certification": ALPHA_ENDPOINT,
        },
        "bootstrap": {"type": "crossed target-build x shared-query", "reps": REPS,
                      "seed": BOOTSTRAP_SEED},
        "paper_reproduction": reproduction,
        "decisions": decisions,
        "claim_boundary": (
            "Attribution within the registered response cube only; not a prospective result, "
            "new-build certificate, runtime claim, or universal baseline ranking."
        ),
    }
    (output / "decision.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.mkdir(parents=True)
    print(json.dumps(analyze(args.repo.resolve(), args.replay.resolve(), args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
