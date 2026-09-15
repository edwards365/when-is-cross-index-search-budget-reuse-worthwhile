import importlib.util
from pathlib import Path
import unittest

import numpy as np
import pandas as pd


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts/tcp_sigmod_regular_closure/tcp_hm9_tc.py"
SPEC = importlib.util.spec_from_file_location("tcp_hm9_tc", MODULE_PATH)
TCP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TCP)


def grid_from_safe(patterns):
    result = {}
    for index, ef in enumerate(TCP.GRID):
        safe = [pattern[index] for pattern in patterns]
        result[int(ef)] = pd.DataFrame({
            "qid": range(len(safe)),
            "r": [0.95 if value else 0.80 for value in safe],
            "dists": [float(ef)] * len(safe),
        })
    return result


class CanonicalTcpTests(unittest.TestCase):
    def test_stable_tail_handles_nonmonotonic_recall_and_bot(self):
        grid = grid_from_safe([
            [True, True, True, True, True, True, True],
            [False, True, False, True, True, True, True],
            [False, False, False, False, False, True, False],
        ])
        np.testing.assert_array_equal(TCP.raw_first_safe(grid), [10, 20, 160])
        tail = TCP.stable_tail_actions(grid)
        self.assertEqual(tail[0], 10)
        self.assertEqual(tail[1], 80)
        self.assertTrue(np.isinf(tail[2]))

    def test_history_max_preserves_bot(self):
        pooled = TCP.history_max([np.array([10.0, np.inf]), np.array([20.0, 80.0])])
        self.assertEqual(pooled[0], 20)
        self.assertTrue(np.isinf(pooled[1]))

    def test_execute_routes_bot_to_endpoint_without_dropping_query(self):
        grid = grid_from_safe([[True] * 7, [True] * 7])
        result = TCP.execute(grid, np.array([20.0, np.inf]))
        self.assertEqual(result.selected_ef.tolist(), [20, 200])
        self.assertEqual(result.abstain.tolist(), [False, True])
        self.assertEqual(len(result), 2)

    def test_cp_bound_validates_counts(self):
        with self.assertRaises(ValueError):
            TCP.cp_ucb(2, 1)


if __name__ == "__main__":
    unittest.main()
