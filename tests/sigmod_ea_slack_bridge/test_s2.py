import importlib.util
import pathlib
import sys
import unittest

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sigmod_ea_slack_bridge" / "analyze_s2.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("s2", SCRIPT)
s2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s2)


class S2SemanticTests(unittest.TestCase):
    def test_zero_failures_59_qualifies_at_alpha_005(self):
        state, _, upper = s2.three_state(0, 59, 0.05)
        self.assertEqual(state, "QUALIFIED")
        self.assertLessEqual(upper, 0.05)

    def test_zero_failures_58_does_not_qualify(self):
        state, _, upper = s2.three_state(0, 58, 0.05)
        self.assertEqual(state, "INDETERMINATE")
        self.assertGreater(upper, 0.05)

    def test_nonqualification_is_not_above_delta(self):
        state, lower, upper = s2.three_state(1, 59, 0.05)
        self.assertEqual(state, "INDETERMINATE")
        self.assertLessEqual(lower, 0.05)
        self.assertGreater(upper, 0.05)

    def test_confidently_above_delta_requires_lower_bound(self):
        state, lower, _ = s2.three_state(60, 750, 0.05)
        self.assertEqual(state, "CONFIDENTLY_ABOVE_DELTA")
        self.assertGreater(lower, 0.05)

    def test_first_passing_can_differ_from_stable_tail(self):
        hit = np.asarray([[[10, 9, 10]]], dtype=np.int16)
        first, stable, nonmono = s2.label_indices(hit)
        self.assertEqual(int(first[0, 0]), 0)
        self.assertEqual(int(stable[0, 0]), 2)
        self.assertTrue(bool(nonmono[0, 0]))

    def test_stable_tail_implication_on_counterexample(self):
        hit = np.asarray([[[10, 9, 10]]], dtype=np.int16)
        _, stable, _ = s2.label_indices(hit)
        action = int(stable[0, 0])
        self.assertGreaterEqual(action, int(stable[0, 0]))
        self.assertGreaterEqual(int(hit[0, 0, action]), 10)

    def test_cp_bounds_ordered(self):
        lower, upper = s2.cp_bounds(20, 750, 0.025)
        self.assertLessEqual(lower, 20 / 750)
        self.assertGreaterEqual(upper, 20 / 750)


if __name__ == "__main__":
    unittest.main()
