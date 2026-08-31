"""Outcome-free checks for immutable Stage-I evaluation execution."""

from __future__ import annotations

import csv
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/icba_cibs_stage1/run_evaluation.py"
INTENT = ROOT / "manifests/icba_cibs_stage1_evaluation_access_intent.json"
ACCESS = ROOT / "results/icba_cibs_stage1/phase1/query_roles/truth_access_log.csv"
SELECTED = ROOT / "manifests/icba_cibs_stage1_selected_actions.json"


def load_module():
    spec = importlib.util.spec_from_file_location("evaluation_protocol", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EvaluationProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = load_module()

    def test_access_intent_binds_selected_manifest(self):
        intent = json.loads(INTENT.read_text(encoding="utf-8"))
        selected = json.loads(SELECTED.read_text(encoding="utf-8"))
        self.assertEqual(intent["selected_action_manifest_sha256"], self.protocol.sha256(SELECTED))
        self.assertFalse(intent["evaluation_reselection_allowed"])
        self.assertFalse(intent["future_confirm_accessed"])
        self.assertEqual(selected["status"], "FROZEN_AFTER_SENTINEL_BEFORE_EVALUATION")

    def test_access_log_is_conservatively_armed(self):
        with ACCESS.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 8)
        for row in rows:
            if row["role"] == "cibs_future_confirm":
                self.assertEqual((row["truth_accessed"], row["action_outcome_accessed"]), ("0", "0"))
            else:
                self.assertEqual((row["truth_accessed"], row["action_outcome_accessed"]), ("1", "1"))

    def test_no_future_query_artifact_is_opened(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('["cibs_future_confirm"]', source)
        self.assertIn('["cibs_evaluation"]', source)

    def test_selected_actions_are_lookup_only(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('fixed_action_rows(all_rows, dataset, frozen["B1"])', source)
        self.assertIn('fixed_action_rows(all_rows, dataset, frozen["B4_CIBS_FIXED"])', source)
        self.assertNotIn("select_action(", source)

    def test_oracle_is_diagnostic_and_target_feasible(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('float(row["raw_recall_at_10"]) >= 0.90', source)
        self.assertIn('"B5_deployable": False', source)

    def test_statistics_are_exactly_frozen(self):
        self.assertEqual(self.protocol.BOOTSTRAP_SEED, 991)
        self.assertEqual(self.protocol.BOOTSTRAP_REPLICATES, 5000)
        self.assertLess(self.protocol.cp_ucb(0, 500), 0.05)
        self.assertGreater(self.protocol.cp_ucb(30, 500), 0.05)


if __name__ == "__main__":
    unittest.main()
