import unittest
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "tcp_sigmod_regular_closure"
sys.path.insert(0, str(SCRIPT_DIR))

from phase6_lifecycle import break_even


class Phase6LifecycleTest(unittest.TestCase):
    def test_immediate_break_even_when_overhead_and_marginal_cost_are_lower(self):
        self.assertEqual(break_even(10, 2, 20, 4), 0)

    def test_positive_break_even(self):
        self.assertEqual(break_even(30, 2, 10, 4), 10)

    def test_no_break_even_without_marginal_saving(self):
        self.assertIsNone(break_even(10, 4, 10, 4))


if __name__ == "__main__":
    unittest.main()
