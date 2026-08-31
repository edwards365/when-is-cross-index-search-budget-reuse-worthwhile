"""Outcome-free integrity tests for the frozen Stage-I Phase 1 inputs."""

from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "manifests/icba_cibs_stage1_phase1_preregistration.json"
ROLES = ROOT / "manifests/icba_cibs_stage1_query_roles.json"
BUILDS = ROOT / "manifests/icba_cibs_stage1_build_candidates.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Phase1FreezeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prereg = json.loads(PREREG.read_text())
        cls.roles = json.loads(ROLES.read_text())
        cls.builds = json.loads(BUILDS.read_text())

    def test_manifest_hash_chain(self):
        self.assertEqual(self.prereg["query_role_manifest_sha256"], sha256(ROLES))
        self.assertEqual(self.prereg["build_manifest_sha256"], sha256(BUILDS))
        self.assertFalse(self.prereg["truth_or_action_outcomes_read_during_freeze"])

    def test_role_counts_hashes_and_zero_overlap(self):
        expected = {
            "cibs_design": 32,
            "cibs_sentinel": 256,
            "cibs_evaluation": 500,
            "cibs_future_confirm": 244,
        }
        for dataset in self.roles["datasets"].values():
            sets = {}
            for role, count in expected.items():
                record = dataset["roles"][role]
                ids_path = ROOT / record["source_ids_path"]
                query_path = ROOT / record["queries_path"]
                ids = np.load(ids_path, allow_pickle=False)
                queries = np.load(query_path, mmap_mode="r", allow_pickle=False)
                self.assertEqual(ids.shape, (count,))
                self.assertEqual(queries.shape[0], count)
                self.assertEqual(record["source_ids_file_sha256"], sha256(ids_path))
                self.assertEqual(record["queries_file_sha256"], sha256(query_path))
                self.assertFalse(record["truth_accessed_at_freeze"])
                self.assertFalse(record["action_outcome_accessed_at_freeze"])
                sets[role] = set(map(int, ids))
            for i, left in enumerate(expected):
                for right in tuple(expected)[i + 1 :]:
                    self.assertFalse(sets[left] & sets[right])
            self.assertEqual(dataset["selected_historical_source_id_overlap"], 0)
            self.assertEqual(dataset["selected_base_source_id_overlap"], 0)

    def test_truth_firewall_log_is_closed_at_freeze(self):
        path = ROOT / self.roles["truth_access_log"]
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["truth_accessed"] == "0" for row in rows))
        self.assertTrue(all(row["action_outcome_accessed"] == "0" for row in rows))
        future = [row for row in rows if row["role"] == "cibs_future_confirm"]
        self.assertTrue(all(row["next_permitted_access"] == "NEVER_IN_STAGE_I" for row in future))

    def test_build_orders_are_distinct_full_permutations(self):
        hashes = set()
        for candidate in self.builds["candidates"]:
            path = ROOT / candidate["insertion_order_path"]
            order = np.load(path, allow_pickle=False)
            self.assertEqual(order.shape, (100000,))
            self.assertTrue(np.array_equal(np.sort(order), np.arange(100000)))
            self.assertEqual(candidate["insertion_order_file_sha256"], sha256(path))
            hashes.add(candidate["insertion_order_le_u32_sha256"])
        self.assertEqual(len(hashes), 3)
        self.assertEqual(self.builds["fallback_build_id"], "G1")
        self.assertEqual(self.builds["random_single_build_baseline"], "G2")

    def test_exact_cp_reference_boundaries(self):
        alpha = 0.05
        for n in (256, 250):
            self.assertLessEqual(beta.ppf(1 - alpha / 36, 4, n - 3), 0.05)
            self.assertGreater(beta.ppf(1 - alpha / 36, 5, n - 4), 0.05)
        self.assertLessEqual(beta.ppf(1 - alpha / 24, 1, 128), 0.05)
        self.assertGreater(beta.ppf(1 - alpha / 24, 2, 127), 0.05)
        self.assertLessEqual(beta.ppf(1 - alpha / 12, 5, 252), 0.05)
        self.assertGreater(beta.ppf(1 - alpha / 12, 6, 251), 0.05)

    def test_resource_and_forbidden_gates(self):
        gate = self.prereg["resource_gate"]
        self.assertEqual(gate["status"], "PASS")
        self.assertGreaterEqual(gate["free_bytes"], gate["required_bytes"])
        self.assertIn("future_confirm", self.prereg["forbidden"])
        self.assertIn("GPU_method_search", self.prereg["forbidden"])


if __name__ == "__main__":
    unittest.main()
