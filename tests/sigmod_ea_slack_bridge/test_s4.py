#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "sigmod_ea_slack_bridge"))

from analyze_s4 import bootstrap_pair, cp
from s4_faiss_replay import per_query_ndc


class TestS4Fresh(unittest.TestCase):
    def test_zero_failures_qualify_at_500(self):
        state, low, high = cp(0, 500)
        self.assertEqual(state, "QUALIFIED")
        self.assertEqual(low, 0.0)
        self.assertLess(high, 0.05)

    def test_eleven_failures_qualify_at_500(self):
        state, _, high = cp(11, 500)
        self.assertEqual(state, "QUALIFIED")
        self.assertLessEqual(high, 0.05)

    def test_sixteen_failures_are_indeterminate_at_500(self):
        state, low, high = cp(16, 500)
        self.assertEqual(state, "INDETERMINATE")
        self.assertLess(low, 0.05)
        self.assertGreater(high, 0.05)

    def test_endpoint_has_zero_saving(self):
        fail = np.zeros(20)
        cost = np.arange(1, 21, dtype=float)
        _, _, lo, hi = bootstrap_pair(fail, cost, cost, reps=100, seed=991)
        self.assertEqual(lo, 0.0)
        self.assertEqual(hi, 0.0)

    def test_faiss_counter_fails_closed_or_positive(self):
        try:
            value = per_query_ndc()
        except RuntimeError:
            return
        self.assertGreater(value, 0)


if __name__ == "__main__":
    unittest.main()
