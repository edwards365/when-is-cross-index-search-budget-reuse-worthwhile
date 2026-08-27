#!/usr/bin/env python3
"""Deterministic finite-environment synthetic closure for ICBA/ECSE."""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

from ecse import BernoulliEnvironment, ambiguity_diameter, binom_pmf, ecse_allocation, exact_equal_tail_accepts
from lower_bound import point_loss

MASTER_SEED = 991
KS = (2, 4, 8)
LEVELS = (2, 3, 4, 6)
GAPS = (0, 1, 2, 4)
SEPARATIONS = (0.0, 0.25, 0.5, 1.0)
CHECKPOINTS = (0, 8, 16, 32, 64, 128, 256)
DELTAS = (0.01, 0.05, 0.10)
ALPHAS = (0.01, 0.05)
WORKLOADS = (1_000, 10_000, 100_000, 1_000_000, 10_000_000)
SENTINEL_UNIT_COST = 0.001
TRUTH_UNIT_COST = 0.001


def make_library(k_env, levels, gap_steps, separation):
    actions = tuple(i / (levels - 1) for i in range(levels))
    ps = [0.5] if k_env == 1 else [0.5 - separation/2 + separation*i/(k_env-1) for i in range(k_env)]
    envs = []
    for j, p in enumerate(ps):
        shift = 0 if k_env == 1 else round(gap_steps * j / (k_env - 1))
        base = (0, max(0, (levels-1)//2), levels-1)
        budgets = tuple(actions[min(levels-1, x + shift)] for x in base)
        envs.append(BernoulliEnvironment(f"e{j}", p, budgets))
    return envs, actions


def exact_source_minimax(envs, actions):
    best = math.inf
    for policy in itertools.product(actions, repeat=3):
        worst = max(sum(point_loss(policy[q], e.budgets[q], 1.0) for q in range(3))/3 for e in envs)
        best = min(best, worst)
    return best


def pair_lower_bound(envs):
    best = 0.0
    for a, b in itertools.combinations(envs, 2):
        diffs = [max(0.0, y-x) for x, y in zip(a.budgets, b.budgets)]
        positive = [x for x in diffs if x > 0]
        if not positive:
            continue
        delta = min(positive)
        rho = sum(x >= delta-1e-12 for x in diffs)/3
        # Source-visible state has identical distribution in this construction.
        best = max(best, 0.5 * delta * rho)
    return best


def transition(states, envs, target, previous_k, k, alpha_each):
    out = defaultdict(float)
    increment = k - previous_k
    for (successes, names), mass in states.items():
        for add in range(increment + 1):
            probability = binom_pmf(add, increment, target.sentinel_p)
            total = successes + add
            accepted = {e.name for e in envs if exact_equal_tail_accepts(total, k, e.sentinel_p, alpha_each)}
            out[(total, frozenset(set(names) & accepted))] += mass * probability
    return out


def exact_ecse_path(envs, alpha):
    envmap = {e.name: e for e in envs}
    alpha_each = alpha / (len(CHECKPOINTS)-1)
    rows = []
    for target in envs:
        states = {(0, frozenset(envmap)): 1.0}
        previous = 0
        for k in CHECKPOINTS:
            if k:
                states = transition(states, envs, target, previous, k, alpha_each)
            miss = under = over = diameter = fallback = 0.0
            for (_, names), mass in states.items():
                miss += mass * (target.name not in names)
                for q in range(3):
                    allocation, used_fallback = ecse_allocation(envmap, names, q, 1.0)
                    truth = target.budgets[q]
                    under += mass * (allocation < truth-1e-12) / 3
                    over += mass * max(0.0, allocation-truth) / 3
                    diameter += mass * ambiguity_diameter(envmap, names, q) / 3
                    fallback += mass * used_fallback / 3
            rows.append({"target": target.name, "k": k, "identification_error": miss,
                         "under_budget_risk": under, "over_budget_cost": over,
                         "ambiguity_size": sum(mass*len(names) for (_, names), mass in states.items()),
                         "ambiguity_diameter": diameter, "fallback_rate": fallback})
            previous = k
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    bounds = []; grid = []
    for k_env, levels, gap, separation, alpha in itertools.product(KS, LEVELS, GAPS, SEPARATIONS, ALPHAS):
        envs, actions = make_library(k_env, levels, gap, separation)
        minimax = exact_source_minimax(envs, actions)
        lower = pair_lower_bound(envs)
        bound_ratio = lower/minimax if minimax else (1.0 if lower == 0 else math.inf)
        path = exact_ecse_path(envs, alpha)
        for delta_q in DELTAS:
            key = {"K": k_env, "levels": levels, "gap_steps": gap, "separation": separation,
                   "delta_q": delta_q, "alpha": alpha, "exact_source_minimax": minimax,
                   "source_lower_bound": lower, "lower_exact_ratio": bound_ratio}
            bounds.append(key)
            for row in path:
                full = dict(key); full.update(row)
                full["safe"] = row["under_budget_risk"] <= delta_q + 1e-12
                for n in WORKLOADS:
                    full[f"probe_adjusted_cost_N{n}"] = row["over_budget_cost"] + row["k"]*(SENTINEL_UNIT_COST+TRUTH_UNIT_COST)/n
                grid.append(full)
    def write_csv(path, rows):
        tmp = path.with_suffix(path.suffix+".tmp")
        with tmp.open("w", newline="") as h:
            w=csv.DictWriter(h, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        tmp.replace(path)
    write_csv(args.output_dir/"synthetic_bounds.csv", bounds)
    write_csv(args.output_dir/"synthetic_grid.csv", grid)
    counter = {
      "master_seed": MASTER_SEED,
      "nondiscriminative": "separation=0 keeps ambiguity unless sampling noise wrongly excludes models",
      "perfect_single_probe_identification": "Bernoulli endpoint models are mutually singular only at p=0 versus p=1",
      "zero_gap": "gap_steps=0 has zero minimax tax and zero lower bound",
      "unsafe_endpoint": "not simulated as feasible; ECSE theorem requires a separately safe endpoint",
      "parquet": "NOT_MATERIALIZED_DISK_BELOW_10_GIB"
    }
    p=args.output_dir/"synthetic_counterexamples.json"; tmp=p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(counter,indent=2)+"\n"); tmp.replace(p)


if __name__ == "__main__": main()
