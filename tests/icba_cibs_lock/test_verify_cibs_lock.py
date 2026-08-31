import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/icba_cibs_lock"))

from verify_cibs_lock import counterexamples, cp_row, cp_upper  # noqa: E402


class CIBSLockTests(unittest.TestCase):
    def test_exact_cp_main(self):
        row = cp_row(3, 12, 256, 0.05, 0.05)
        self.assertEqual(row["max_certifiable_failures"], 3)
        self.assertLessEqual(row["ucb_at_max"], 0.05)
        self.assertGreater(row["ucb_at_next"], 0.05)
        self.assertEqual(row["zero_failure_min_n"], 129)

    def test_exact_cp_low_cost(self):
        row = cp_row(2, 12, 128, 0.05, 0.05)
        self.assertEqual(row["max_certifiable_failures"], 0)
        self.assertLessEqual(row["ucb_at_max"], 0.05)
        self.assertGreater(row["ucb_at_next"], 0.05)
        self.assertEqual(row["zero_failure_min_n"], 121)

    def test_cp_boundary(self):
        self.assertEqual(cp_upper(10, 10, 0.01), 1.0)

    def test_all_counterexamples(self):
        rows = counterexamples()
        self.assertEqual(len(rows), 14)
        self.assertTrue(all(r["pass"] for r in rows))
        self.assertTrue(math.isinf(rows[11]["quantity"]))


if __name__ == "__main__":
    unittest.main()
