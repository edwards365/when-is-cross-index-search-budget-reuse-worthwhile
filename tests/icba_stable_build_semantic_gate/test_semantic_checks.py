from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "icba_stable_build_semantic_gate"
    / "semantic_checks.py"
)
SPEC = importlib.util.spec_from_file_location("semantic_checks", SCRIPT)
assert SPEC and SPEC.loader
semantic_checks = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = semantic_checks
SPEC.loader.exec_module(semantic_checks)


class SemanticChecksTest(unittest.TestCase):
    def test_all_registered_witnesses_pass(self) -> None:
        rows = semantic_checks.witnesses()
        self.assertGreaterEqual(len(rows), 12)
        self.assertTrue(all(row["passed"] == "true" for row in rows))

    def test_ef_one_can_expand_arbitrarily_more_than_one_node(self) -> None:
        graph = {index: [index + 1] for index in range(11)} | {11: []}
        distances = {index: float(12 - index) for index in range(12)}
        result = semantic_checks.simulate_hnsw_base(graph, distances, entry=0, ef=1)
        self.assertEqual(len(result.expansions), 12)

    def test_tied_fixed_ef_runs_need_not_have_prefix_equivalent_traces(self) -> None:
        graph = {0: [2, 1], 1: [], 2: []}
        distances = {0: 10.0, 1: 1.0, 2: 1.0}
        rank = {1: 1, 2: 2}
        small = semantic_checks.simulate_hnsw_base(graph, distances, entry=0, ef=1, tie_rank=rank)
        large = semantic_checks.simulate_hnsw_base(graph, distances, entry=0, ef=2, tie_rank=rank)
        self.assertEqual(small.expansions, (0, 2))
        self.assertEqual(large.expansions[:2], (0, 1))

    def test_first_discovery_parent_changes_with_tie_order(self) -> None:
        graph = {0: [1, 2], 1: [3], 2: [3], 3: []}
        distances = {0: 9.0, 1: 1.0, 2: 1.0, 3: 0.5}
        left = semantic_checks.simulate_hnsw_base(graph, distances, entry=0, ef=4, tie_rank={1: 1, 2: 2})
        right = semantic_checks.simulate_hnsw_base(graph, distances, entry=0, ef=4, tie_rank={1: 2, 2: 1})
        self.assertEqual(dict(left.introduction_parent)[3], 1)
        self.assertEqual(dict(right.introduction_parent)[3], 2)

    def test_right_censoring_is_not_endpoint_imputation(self) -> None:
        minimum = semantic_checks.minimum_safe_ef({0: []}, {0: 1.0}, [1, 2, 4], {9})
        self.assertEqual(minimum, float("inf"))

    def test_same_mean_can_have_worse_empirical_p95(self) -> None:
        baseline = [5.0] * 100
        shifted = [1.0] * 94 + [406.0 / 6.0] * 6
        self.assertLess(abs(sum(baseline) / 100 - sum(shifted) / 100), 1e-12)
        self.assertGreater(
            semantic_checks.empirical_quantile(shifted, 0.95),
            semantic_checks.empirical_quantile(baseline, 0.95),
        )


if __name__ == "__main__":
    unittest.main()
