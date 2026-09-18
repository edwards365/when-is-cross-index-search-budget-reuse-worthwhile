#!/usr/bin/env python3
"""Post-hoc grid, Recall-event, and risk-limit sensitivity on frozen responses."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np


CONDITIONS = (
    ("primary", (10, 20, 40, 80, 120, 160, 200), 0.95, 0.05),
    ("coarse_grid", (20, 40, 80, 160, 200), 0.95, 0.05),
    ("upper_grid", (40, 80, 120, 160, 200), 0.95, 0.05),
    ("recall_090", (10, 20, 40, 80, 120, 160, 200), 0.90, 0.05),
    ("risk_025", (10, 20, 40, 80, 120, 160, 200), 0.95, 0.025),
)
ALPHA_SELECT = 0.05
ALPHA_CANDIDATE = 0.025
ALPHA_ENDPOINT = 0.025
REPS = 5000
SEED = 991


def load_module(repo: Path):
    path = repo / "scripts/graph_anns_phase3_ea85/analyze_phase2_refresh95.py"
    spec = importlib.util.spec_from_file_location("refresh95", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def minima(recalls: np.ndarray, threshold: float) -> np.ndarray:
    good = recalls >= threshold
    first = np.argmax(good, axis=0)
    return np.where(np.any(good, axis=0), first, recalls.shape[0] - 1).astype(int)


def cp_pass(module, recalls: np.ndarray, threshold: float, limit: float,
            alpha: float) -> tuple[bool, float, int]:
    failures = int(np.sum(recalls < threshold))
    ucb = module.cp_upper(failures, recalls.size, 1 - alpha)
    return ucb <= limit, ucb, failures


def first_global(module, recalls: np.ndarray, threshold: float, limit: float) -> int:
    for idx in range(recalls.shape[0]):
        if cp_pass(module, recalls[idx], threshold, limit, ALPHA_SELECT)[0]:
            return idx
    return recalls.shape[0] - 1


def choose_shift(module, selection: np.ndarray, base: np.ndarray,
                 threshold: float, limit: float) -> int:
    for shift in range(selection.shape[0]):
        idx = np.minimum(base + shift, selection.shape[0] - 1)
        values = selection[idx, np.arange(idx.size)]
        if cp_pass(module, values, threshold, limit, ALPHA_SELECT)[0]:
            return shift
    return selection.shape[0] - 1


def deploy(module, cert: np.ndarray, evaluation_r: np.ndarray,
           evaluation_d: np.ndarray, cert_idx: np.ndarray, eval_idx: np.ndarray,
           threshold: float, limit: float) -> dict:
    endpoint_cert = cert[-1]
    candidate_cert = cert[cert_idx, np.arange(cert_idx.size)]
    candidate_ok, candidate_ucb, _ = cp_pass(
        module, candidate_cert, threshold, limit, ALPHA_CANDIDATE
    )
    endpoint_ok, endpoint_ucb, _ = cp_pass(
        module, endpoint_cert, threshold, limit, ALPHA_ENDPOINT
    )
    use = eval_idx if candidate_ok and endpoint_ok else np.full(
        evaluation_r.shape[1], evaluation_r.shape[0] - 1, dtype=int
    )
    recalls = evaluation_r[use, np.arange(use.size)]
    dists = evaluation_d[use, np.arange(use.size)]
    return {
        "recalls": recalls,
        "dists": dists,
        "candidate_ok": candidate_ok,
        "endpoint_ok": endpoint_ok,
        "candidate_ucb": candidate_ucb,
        "endpoint_ucb": endpoint_ucb,
    }


def crossed(values: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(SEED)
    builds, queries = next(iter(values.values())).shape
    output = {key: np.empty(REPS) for key in values}
    for start in range(0, REPS, 100):
        count = min(100, REPS - start)
        bw = rng.multinomial(builds, np.ones(builds) / builds, size=count) / builds
        qw = rng.multinomial(queries, np.ones(queries) / queries, size=count) / queries
        for key, array in values.items():
            output[key][start:start + count] = np.einsum("ij,ij->i", bw @ array, qw)
    return output


def interval(values: np.ndarray) -> tuple[float, float]:
    low, high = np.quantile(values, [0.025, 0.975])
    return float(low), float(high)


def load_subset(module, replay: Path, dataset: str, snapshot: str, seed: int,
                role: str, grid: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    _, recalls, dists = module.load_tensor(replay, dataset, snapshot, seed, role)
    lookup = {int(value): idx for idx, value in enumerate(module.EFS)}
    selected = [lookup[value] for value in grid]
    return recalls[selected], dists[selected]


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze(repo: Path, replay: Path, output: Path) -> dict:
    module = load_module(repo)
    base_arrays = repo / "results/sigmod_ea_limitation_closure/equal_information_baselines"
    rows: list[dict] = []
    decisions: dict[str, dict] = {}
    for name, grid, threshold, limit in CONDITIONS:
        decisions[name] = {}
        for dataset in module.DATASETS:
            source = {role: {} for role in module.ROLES}
            target = {}
            for role in module.ROLES:
                for seed in module.SEEDS:
                    old_r, _ = load_subset(module, replay, dataset, "old", seed, role, grid)
                    source[role][seed] = minima(old_r, threshold)
                    target[seed, role] = load_subset(
                        module, replay, dataset, "target_refresh05", seed, role, grid
                    )
            tcp_d, tcp_z, global_d, global_z = [], [], [], []
            tcp_accept = global_accept = endpoint_qualified = 0
            for seed in module.SEEDS:
                selection_r, _ = target[seed, "selection"]
                cert_r, _ = target[seed, "certification"]
                eval_r, eval_d = target[seed, "cold_evaluation"]
                pools = {
                    role: np.max(np.stack([
                        indices for source_seed, indices in source[role].items()
                        if source_seed != seed
                    ]), axis=0)
                    for role in module.ROLES
                }
                shift = choose_shift(module, selection_r, pools["selection"], threshold, limit)
                tcp_cert_idx = np.minimum(pools["certification"] + shift, len(grid) - 1)
                tcp_eval_idx = np.minimum(pools["cold_evaluation"] + shift, len(grid) - 1)
                global_action = first_global(module, selection_r, threshold, limit)
                global_cert_idx = np.full(cert_r.shape[1], global_action, dtype=int)
                global_eval_idx = np.full(eval_r.shape[1], global_action, dtype=int)
                tcp = deploy(module, cert_r, eval_r, eval_d, tcp_cert_idx, tcp_eval_idx,
                             threshold, limit)
                glob = deploy(module, cert_r, eval_r, eval_d, global_cert_idx, global_eval_idx,
                              threshold, limit)
                tcp_d.append(tcp["dists"]); tcp_z.append(tcp["recalls"] < threshold)
                global_d.append(glob["dists"]); global_z.append(glob["recalls"] < threshold)
                tcp_accept += int(tcp["candidate_ok"] and tcp["endpoint_ok"])
                global_accept += int(glob["candidate_ok"] and glob["endpoint_ok"])
                endpoint_qualified += int(tcp["endpoint_ok"])
            tcp_d = np.stack(tcp_d); tcp_z = np.stack(tcp_z)
            global_d = np.stack(global_d); global_z = np.stack(global_z)
            if name == "primary":
                reference = np.load(base_arrays / f"{dataset}_arrays.npz")
                if not (np.array_equal(tcp_d, reference["tcp_registered_dists"])
                        and np.array_equal(global_d, reference["target_global_dists"])):
                    raise RuntimeError(f"primary sensitivity reproduction failed: {dataset}")
            draws = crossed({"tcp": tcp_d, "global": global_d})
            gain_draw = 1 - draws["tcp"] / draws["global"]
            low, high = interval(gain_draw)
            build_gain = 1 - tcp_d.mean(axis=1) / global_d.mean(axis=1)
            lobo = [
                float(1 - np.delete(tcp_d, idx, axis=0).mean() /
                      np.delete(global_d, idx, axis=0).mean())
                for idx in range(len(module.SEEDS))
            ]
            row = {
                "condition": name,
                "dataset": dataset,
                "grid": "|".join(str(x) for x in grid),
                "recall_threshold": threshold,
                "risk_limit": limit,
                "tcp_risk": float(tcp_z.mean()),
                "target_global_risk": float(global_z.mean()),
                "tcp_mean_ndc": float(tcp_d.mean()),
                "target_global_mean_ndc": float(global_d.mean()),
                "tcp_gain_vs_target_global": float(1 - tcp_d.mean() / global_d.mean()),
                "gain_ci_low": low,
                "gain_ci_high": high,
                "tcp_p95_ratio": float(np.quantile(tcp_d, 0.95) / np.quantile(global_d, 0.95)),
                "tcp_p99_ratio": float(np.quantile(tcp_d, 0.99) / np.quantile(global_d, 0.99)),
                "tcp_accepted_builds": tcp_accept,
                "target_global_accepted_builds": global_accept,
                "endpoint_qualified_builds": endpoint_qualified,
                "min_loto_gain": min(lobo),
                "delete_largest_gain": lobo[int(np.argmax(build_gain))],
            }
            rows.append(row)
            decisions[name][dataset] = {
                "positive_mean_interval": low > 0,
                "p95_noninferior_5pct": row["tcp_p95_ratio"] <= 1.05,
                "all_endpoints_qualified": endpoint_qualified == len(module.SEEDS),
            }
    write_csv(output / "sensitivity.csv", rows)
    payload = {
        "status": "POST_HOC_FROZEN_RESPONSE_GRID_AND_RISK_SENSITIVITY",
        "primary_reproduction": "PASS",
        "decisions": decisions,
        "claim_boundary": "Sensitivity only; conditions are not independent confirmations.",
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
