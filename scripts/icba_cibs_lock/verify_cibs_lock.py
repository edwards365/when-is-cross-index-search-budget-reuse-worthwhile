#!/usr/bin/env python3
"""Deterministic finite checks for the CIBS theory/semantic lock."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from scipy.stats import beta


def cp_upper(x: int, n: int, alpha_cell: float) -> float:
    """One-sided Clopper--Pearson upper endpoint."""
    if x == n:
        return 1.0
    return float(beta.ppf(1.0 - alpha_cell, x + 1, n - x))


def cp_row(k: int, ell: int, n: int, alpha: float, delta: float) -> dict[str, object]:
    m = k * ell
    alpha_cell = alpha / m
    accepted = [x for x in range(n + 1) if cp_upper(x, n, alpha_cell) <= delta]
    x_max = max(accepted) if accepted else -1
    return {
        "K": k,
        "L": ell,
        "M": m,
        "n": n,
        "alpha": alpha,
        "delta": delta,
        "alpha_per_action": alpha_cell,
        "max_certifiable_failures": x_max,
        "ucb_at_max": cp_upper(x_max, n, alpha_cell) if x_max >= 0 else "",
        "ucb_at_next": cp_upper(x_max + 1, n, alpha_cell) if x_max < n else "",
        "zero_failure_ucb": cp_upper(0, n, alpha_cell),
        "zero_failure_min_n": math.ceil(math.log(alpha_cell) / math.log(1 - delta)),
    }


def counterexamples() -> list[dict[str, object]]:
    """Return exact finite witnesses for all catalogued failure modes."""
    rows: list[dict[str, object]] = []
    rows.append({"id": "CE01", "name": "per-action-to-familywise", "witness": "M=36, independent 0.05 errors", "quantity": 1 - 0.95**36, "pass": 1 - 0.95**36 > 0.8})
    recalls = [1.0] * 94 + [0.0] * 6
    rows.append({"id": "CE02", "name": "mean-recall-vs-failure-risk", "witness": "94 perfect, 6 zero-recall; tau=0.9", "quantity": sum(x < 0.9 for x in recalls) / 100, "pass": sum(recalls) / 100 >= 0.9 and sum(x < 0.9 for x in recalls) / 100 > 0.05})
    rows.append({"id": "CE03", "name": "raw-ef-nonmonotonicity", "witness": "same query recall: ef=40 -> 1, ef=80 -> 0.9", "quantity": -0.1, "pass": 0.9 < 1.0})
    rows.append({"id": "CE04", "name": "budget-proxy-vs-ndc", "witness": "a: ef=20,NDC=100; b: ef=40,NDC=80", "quantity": -20, "pass": 20 < 40 and 100 > 80})
    cost_a = [0.0] * 94 + [100.0] * 6
    cost_b = [7.0] * 100
    rows.append({"id": "CE05", "name": "mean-vs-p95", "witness": "a mean=6,p95=100; b mean=p95=7", "quantity": sum(cost_a) / 100 - sum(cost_b) / 100, "pass": sum(cost_a) / 100 < sum(cost_b) / 100 and sorted(cost_a)[94] > sorted(cost_b)[94]})
    rows.append({"id": "CE06", "name": "sentinel-evaluation-reversal", "witness": "sentinel costs a=1,b=2; evaluation a=3,b=2", "quantity": 2.0, "pass": 1 < 2 and 3 > 2})
    rows.append({"id": "CE07", "name": "post-hoc-candidate", "witness": "pick one of 20 independent 95% intervals", "quantity": 1 - 0.95**20, "pass": 1 - 0.95**20 > 0.05})
    rows.append({"id": "CE08", "name": "empty-certified-set", "witness": "U=(0.08,0.09), delta=0.05", "quantity": 0, "pass": not any(u <= 0.05 for u in (0.08, 0.09))})
    rows.append({"id": "CE09", "name": "endpoint-imputation", "witness": "10 endpoint-infeasible queries imputed successful", "quantity": 0.1, "pass": 10 / 100 > 0.05})
    rows.append({"id": "CE10", "name": "shared-truth-not-free-search", "witness": "truth=100; 36 action searches=10 each", "quantity": 460, "pass": 100 + 36 * 10 == 460})
    rows.append({"id": "CE11", "name": "portfolio-reversal", "witness": "portfolio P1 prefers a; P2 prefers b", "quantity": 1, "pass": 1 < 2 and 4 > 3})
    rows.append({"id": "CE12", "name": "no-finite-break-even", "witness": "offline=1000, g=-0.1", "quantity": math.inf, "pass": -0.1 <= 0})
    rows.append({"id": "CE13", "name": "negative-paired-covariance", "witness": "varA=varB=1,cov=-0.5", "quantity": 3.0, "pass": 1 + 1 - 2 * (-0.5) > 1 + 1})
    rows.append({"id": "CE14", "name": "bonferroni-conservative-correlation", "witness": "36 perfectly correlated tests", "quantity": 0.05 / 36, "pass": 0.05 / 36 < 0.05})
    return rows


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_tree(root: Path) -> dict[str, object]:
    thresholds = [cp_row(3, 12, 256, 0.05, 0.05), cp_row(2, 12, 128, 0.05, 0.05), cp_row(3, 12, 250, 0.05, 0.05)]
    assert [r["max_certifiable_failures"] for r in thresholds] == [3, 0, 3]
    ces = counterexamples()
    assert len(ces) == 14 and all(bool(r["pass"]) for r in ces)
    required = [
        root / "docs/icba_cibs_lock/full_theory_report.md",
        root / "docs/icba_cibs_lock/proof_appendix.md",
        root / "docs/icba_cibs_lock/cibs_fixed_pilot_contract.md",
        root / "manifests/icba_cibs_theory_semantic_decision.json",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    if missing:
        raise AssertionError(f"missing deliverables: {missing}")
    decision = json.loads(required[-1].read_text())
    assert decision["primary_decision"] == "CIBS_FIXED_THEORY_AND_SEMANTICS_LOCKED"
    return {"thresholds": thresholds, "counterexamples": ces, "missing": missing}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = verify_tree(args.root)
    if args.json:
        print(json.dumps(result, indent=2, allow_nan=True))
    else:
        print(f"PASS: {len(result['counterexamples'])} counterexamples; CP maxima 3/0/3")


if __name__ == "__main__":
    main()
