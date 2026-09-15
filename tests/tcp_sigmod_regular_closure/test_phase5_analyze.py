import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/tcp_sigmod_regular_closure"))

from phase5_analyze import graded  # noqa: E402


def frame(failures, cost):
    return pd.DataFrame({"r": [0.0] * failures + [1.0] * (500 - failures),
                         "dists": [cost] * 500, "abstain": [False] * 500})


class Phase5AnalyzeTest(unittest.TestCase):
    def test_graded_fallback_uses_fixed_when_candidate_fails(self):
        selected, _, evaluation, ucb = graded(
            frame(15, 10), frame(15, 10), frame(5, 20), frame(5, 20),
            frame(0, 30), frame(0, 30))
        self.assertEqual(selected, "SOURCE_GLOBAL_FIXED")
        self.assertEqual(float(evaluation.dists.mean()), 20)
        self.assertLessEqual(ucb, .05)

    def test_graded_fallback_uses_candidate_when_certified(self):
        selected, _, evaluation, _ = graded(
            frame(10, 10), frame(10, 10), frame(5, 20), frame(5, 20),
            frame(0, 30), frame(0, 30))
        self.assertEqual(selected, "TCP_HM9_TC")
        self.assertEqual(float(evaluation.dists.mean()), 10)

    def test_mean_recall_gate_is_not_implied_by_risk_gate(self):
        candidate = pd.DataFrame({"r": [0.90] * 490 + [0.0] * 10})
        baseline = pd.DataFrame({"r": [1.0] * 500})
        candidate_risk = float((candidate.r < .90).mean())
        recall_difference = float(candidate.r.mean() - baseline.r.mean())
        self.assertLessEqual(candidate_risk, .05)
        self.assertLess(recall_difference, -.001)


if __name__ == "__main__":
    unittest.main()
