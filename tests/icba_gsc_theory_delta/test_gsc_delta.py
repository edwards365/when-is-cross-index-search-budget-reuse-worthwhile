import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/icba_gsc_theory_delta"))
from verify_gsc_delta import counterexample_checks  # noqa: E402


class GSCDeltaTests(unittest.TestCase):
    def read(self, name):
        with (ROOT / "results/icba_gsc_theory_delta" / name).open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_counterexamples(self):
        xs = counterexample_checks()
        self.assertEqual(len(xs), 16)
        self.assertTrue(all(x["ok"] for x in xs))

    def test_schema_counts(self):
        self.assertEqual(len(self.read("conflict_ledger.csv")), 15)
        self.assertEqual(len(self.read("theory_inheritance_matrix.csv")), 8)
        self.assertEqual(len(self.read("theorem_status.csv")), 8)
        self.assertEqual(len(self.read("operator_overlap_matrix.csv")), 7)
        self.assertEqual(len(self.read("assumption_observability.csv")), 15)

    def test_status_and_claim_scan(self):
        valid = {"INHERITED_VALID", "VALID_WITH_RESTRICTED_SCOPE", "SUPERSEDED_BY_SEMANTIC_REAUDIT", "EMPIRICALLY_REFUTED", "THEORY_UNREFUTED_OPERATOR_FAILED", "ORACLE_ONLY", "CONDITIONAL_REPRODUCTION_ONLY", "NOT_ESTIMABLE"}
        self.assertTrue(all(r["current_status"] in valid for r in self.read("conflict_ledger.csv")))
        forbidden = [r for r in self.read("claim_registry.csv") if r["class"] == "D"]
        self.assertGreaterEqual(len(forbidden), 10)
        self.assertTrue(all(r["status"] == "DO_NOT_CLAIM" for r in forbidden))

    def test_commit_references_and_sealed_sets(self):
        d = json.loads((ROOT / "manifests/icba_gsc_theory_prior_delta_decision.json").read_text(encoding="utf-8"))
        self.assertEqual(d["starting_commit"], "736c3799a92bf31f503c37e8eaaf680f84398aa5")
        self.assertEqual(d["gsc_final_evaluation_access"], "NOT_ACCESSED")
        self.assertEqual(d["validation_dev"], "NOT_ACCESSED")
        self.assertEqual(d["formal_test"], "NOT_ACCESSED")
        self.assertEqual(d["future_confirm"], "NOT_ACCESSED")


if __name__ == "__main__":
    unittest.main()
