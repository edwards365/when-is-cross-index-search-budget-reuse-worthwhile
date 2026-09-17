#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

import numpy as np

MODULE = Path(__file__).resolve().parents[2] / "scripts" / "sigmod_ea_slack_bridge" / "analyze_s1.py"
spec = importlib.util.spec_from_file_location("s1", MODULE)
s1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s1)


class SlackSemanticsTest(unittest.TestCase):
    def test_first_and_stable_differ_on_raw_reversal(self):
        hit = np.asarray([[[10, 9, 10, 10]]])
        first, stable, nonmono = s1.label_indices(hit)
        self.assertEqual(int(first[0, 0]), 0)
        self.assertEqual(int(stable[0, 0]), 2)
        self.assertTrue(bool(nonmono[0, 0]))

    def test_unresolved_falls_back_to_endpoint(self):
        first = np.asarray([[-1]])
        stable = np.asarray([[-1]])
        for lane in s1.LANES:
            self.assertEqual(int(s1.action_indices(lane, first, stable, 5)[0, 0]), 5)

    def test_slack_caps_at_endpoint(self):
        first = np.asarray([[4, 5]])
        stable = np.asarray([[4, 5]])
        got = s1.action_indices("first_plus_2", first, stable, 5)
        np.testing.assert_array_equal(got, np.asarray([[5, 5]]))

    def test_stable_is_not_below_first(self):
        hit = np.asarray([[[8, 10, 9, 10, 10]]])
        first, stable, _ = s1.label_indices(hit)
        self.assertGreaterEqual(int(stable[0, 0]), int(first[0, 0]))

    def test_monotone_response_has_equal_labels(self):
        hit = np.asarray([[[4, 7, 10, 10]]])
        first, stable, nonmono = s1.label_indices(hit)
        self.assertEqual(int(first[0, 0]), int(stable[0, 0]))
        self.assertFalse(bool(nonmono[0, 0]))


if __name__ == "__main__":
    unittest.main()
