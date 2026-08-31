"""Outcome-free tests for the frozen Stage-I sentinel implementation."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/icba_cibs_stage1/run_sentinel_and_select.py"
CPP = ROOT / "cpp/src/icba_cibs_stage1_runner.cpp"


def load_protocol_module():
    spec = importlib.util.spec_from_file_location("sentinel_protocol", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SentinelProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = load_protocol_module()

    def test_exact_cp_main_boundaries(self):
        self.assertLessEqual(self.protocol.cp_ucb(3, 256, 36), 0.05)
        self.assertGreater(self.protocol.cp_ucb(4, 256, 36), 0.05)
        self.assertLessEqual(self.protocol.cp_ucb(3, 250, 36), 0.05)
        self.assertGreater(self.protocol.cp_ucb(4, 250, 36), 0.05)

    def test_exact_cp_b1_boundaries(self):
        self.assertLessEqual(self.protocol.cp_ucb(4, 256, 12), 0.05)
        self.assertGreater(self.protocol.cp_ucb(5, 256, 12), 0.05)

    def test_selection_tie_break_is_frozen(self):
        actions = [
            {"build_id": "G2", "requested_ef": 32,
             "statistics": {"certified": True, "mean_ndc": 100.0, "p95_ndc": 120.0}},
            {"build_id": "G1", "requested_ef": 32,
             "statistics": {"certified": True, "mean_ndc": 100.0, "p95_ndc": 120.0}},
            {"build_id": "G3", "requested_ef": 24,
             "statistics": {"certified": True, "mean_ndc": 100.0, "p95_ndc": 120.0}},
            {"build_id": "G1", "requested_ef": 16,
             "statistics": {"certified": False, "mean_ndc": 1.0, "p95_ndc": 1.0}},
        ]
        selected = self.protocol.select_action(actions)
        self.assertEqual((selected["build_id"], selected["requested_ef"]), ("G3", 24))

    def test_action_grid_is_exact_and_non_enveloped(self):
        self.assertEqual(
            self.protocol.RAW_EFS,
            [10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512],
        )
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('["cibs_evaluation"]', source)
        self.assertNotIn('["cibs_future_confirm"]', source)
        self.assertNotIn("raw_recall_envelope", source)

    def test_native_runner_separates_ef_ndc_expansions_and_wall_clock(self):
        source = CPP.read_text(encoding="utf-8")
        self.assertIn('if (command == "truth")', source)
        self.assertIn('if (command == "sentinel")', source)
        self.assertIn("requested_ef,raw_recall_at_10,Z_abs,native_ndc,tracer_ndc", source)
        self.assertIn("actual_expansions,visited_count,wall_clock_ns,endpoint_status", source)


if __name__ == "__main__":
    unittest.main()
