#!/usr/bin/env python3
"""Regression tests for the Arxiv deep-pool semantic correction."""

import importlib.util
from pathlib import Path

import numpy as np


MODULE = Path(__file__).resolve().parents[2] / "scripts/graph_anns_score8/p1_arxiv_deep_pool.py"
spec = importlib.util.spec_from_file_location("deep_pool", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


checks = []


def check(name, condition):
    checks.append((name, bool(condition)))
    print(("PASS" if condition else "FAIL") + "  " + name)


check("rank_k9_alpha010", mod.conformal_action(np.ones((9, 2)), 0.10)[1] == 9)
check("rank_k19_alpha005", mod.conformal_action(np.ones((19, 2)), 0.05)[1] == 19)
check("rank_k25_alpha005", mod.conformal_action(np.ones((25, 2)), 0.05)[1] == 25)
check("rank_k49_alpha005", mod.conformal_action(np.ones((49, 2)), 0.05)[1] == 48)

src = np.array([[10.0, 10.0], [20.0, np.nan], [40.0, 40.0]])
a, m = mod.conformal_action(src, 0.50)
check("bot_is_positive_infinity", a[1] == 40.0 and m == 2)
a, m = mod.conformal_action(src, 0.10)
check("vacuous_rank_abstains", np.isnan(a).all() and m > len(src))

grid = np.array([10, 20, 40])
hits = np.array([[[9, 10, 10], [8, 9, 10]]])
b = mod.minimum_safe_actions(hits, grid)
check("minimum_safe_actions", b.tolist() == [[20.0, 40.0]])
z = mod.risk_from_raw_counts(hits[0], np.array([10.0, 40.0]), grid)
check("raw_count_risk", z.tolist() == [1.0, 0.0])

success = hits[0] >= mod.H
legacy = success[np.arange(2), [0, 2]] < mod.H
check("legacy_boolean_bug_detected", legacy.tolist() == [True, True] and z.tolist() != legacy.astype(float).tolist())

failed = [name for name, ok in checks if not ok]
print(f"{len(checks) - len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(f"failed: {failed}")
