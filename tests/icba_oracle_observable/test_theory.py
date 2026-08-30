#!/usr/bin/env python3
"""Regression tests for generated finite-state theory artifacts."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "results" / "icba_oracle_observable"


class TheoryClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(HERE / "exhaustive_verify.py")], check=True)

    def test_all_validation_rows_pass(self) -> None:
        with (OUT / "exhaustive_validation.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertGreaterEqual(len(rows), 9)
        self.assertEqual({row["status"] for row in rows}, {"PASS"})

    def test_all_twelve_counterexamples_present(self) -> None:
        with (OUT / "counterexample_registry.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["counterexample_id"] for row in rows}, {f"C{i}" for i in range(1, 13)})
        self.assertTrue(all(row["status"] == "VERIFIED_EXACT_ENUMERATION" for row in rows))

    def test_manifest_is_consistent_when_present(self) -> None:
        path = ROOT / "manifests" / "icba_oracle_observable_theory_decision.json"
        if not path.exists():
            self.skipTest("manifest is generated after proof audit")
        decision = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(decision["sealed_splits"]["validation_dev_accessed"])
        self.assertFalse(decision["sealed_splits"]["formal_test_accessed"])
        self.assertEqual(decision["racs_status"], "THEORETICAL_METHOD_TEMPLATE")

    def test_no_sealed_split_names_are_used_as_inputs(self) -> None:
        source = (HERE / "exhaustive_verify.py").read_text(encoding="utf-8")
        self.assertNotIn("validation-dev/", source)
        self.assertNotIn("formal-test/", source)


if __name__ == "__main__":
    unittest.main()
