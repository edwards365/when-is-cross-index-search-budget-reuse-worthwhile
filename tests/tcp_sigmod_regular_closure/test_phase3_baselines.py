import importlib.util
from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/tcp_sigmod_regular_closure"))
SPEC = importlib.util.spec_from_file_location(
    "phase3_baselines", ROOT / "scripts/tcp_sigmod_regular_closure/phase3_baselines.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Phase3BaselineTests(unittest.TestCase):
    def test_rows_are_disjoint_and_reset(self):
        frame = pd.DataFrame({"qid": range(500), "r": [1.0] * 500})
        selection = MODULE.rows(frame, 0, 250)
        certification = MODULE.rows(frame, 250, 500)
        self.assertEqual(len(selection), 250)
        self.assertEqual(len(certification), 250)
        self.assertFalse(set(selection.qid) & set(certification.qid))

    def test_target_action_is_selected_only_from_selection_slice(self):
        grids = {}
        for ef in MODULE.GRID:
            recall = [0.95] * 250 + [0.1] * 250
            grids[int(ef)] = pd.DataFrame({"qid": range(500), "r": recall, "dists": ef})
        self.assertEqual(MODULE.first_passing_action(grids, 0, 250), 10)


if __name__ == "__main__":
    unittest.main()
