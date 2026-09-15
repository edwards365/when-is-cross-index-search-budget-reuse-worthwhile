import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "tcp_sigmod_regular_closure"))

from phase3_simultaneous_fallback import (  # noqa: E402
    CONFIDENCE, choose_policy, simultaneous_pass,
)


class SimultaneousFallbackTest(unittest.TestCase):
    def test_order_is_frozen(self):
        self.assertEqual(choose_policy(True, True, True), "TCP_HM9_TC")
        self.assertEqual(choose_policy(False, True, True), "SOURCE_GLOBAL_FIXED")
        self.assertEqual(choose_policy(False, False, True), "FIXED_ENDPOINT")
        self.assertEqual(choose_policy(False, False, False), "INVALID_NO_CERTIFIED_ACTION")

    def test_bonferroni_confidence(self):
        self.assertAlmostEqual(CONFIDENCE, 1 - .05 / 3)

    def test_known_threshold_at_n500(self):
        safe = pd.DataFrame({"r": [0.0] * 14 + [1.0] * 486})
        unsafe = pd.DataFrame({"r": [0.0] * 15 + [1.0] * 485})
        self.assertTrue(simultaneous_pass(safe)[0])
        self.assertFalse(simultaneous_pass(unsafe)[0])


if __name__ == "__main__":
    unittest.main()
