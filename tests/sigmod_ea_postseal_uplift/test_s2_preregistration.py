import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class S2PreregistrationTest(unittest.TestCase):
    def setUp(self):
        self.e4 = json.loads((ROOT / "manifests/graph_anns_e4_role_manifest.json").read_text())
        self.s4 = json.loads((ROOT / "results/sigmod_ea_slack_bridge/s4_fresh_preregistration.json").read_text())
        self.s3 = json.loads((ROOT / "results/sigmod_ea_slack_bridge/s3_query_role_manifest.json").read_text())
        self.decision = json.loads((ROOT / "manifests/sigmod_ea_postseal_uplift_s2_preregistration.json").read_text())

    def test_parent_and_no_access(self):
        self.assertEqual(self.decision["parent_commit"], "49bd2910b122293f43c1a9063364a038fa4417b8")
        for key in ("new_query_vector_reads", "new_truth_reads", "new_ann_searches", "new_index_builds"):
            self.assertEqual(self.decision[key], 0)

    def test_s4_exhausts_future_pool(self):
        for dataset in ("sift_100k", "arxiv_nomic_100k"):
            future = set(self.e4["roles"][dataset]["future_replication_ids"])
            cert = set(self.s4["roles"][dataset]["fresh_source_certification_ids"])
            evaluation = set(self.s4["roles"][dataset]["fresh_target_evaluation_ids"])
            self.assertEqual(len(future), 1000)
            self.assertEqual(len(cert), 500)
            self.assertEqual(len(evaluation), 500)
            self.assertFalse(cert & evaluation)
            self.assertEqual(future, cert | evaluation)

    def test_confirmatory_partition(self):
        for dataset in ("sift_100k", "arxiv_nomic_100k"):
            confirmatory = set(self.e4["roles"][dataset]["confirmatory_ids"])
            sentinel = set(self.e4["roles"][dataset]["target_sentinel_ids"])
            evaluation = set(self.e4["roles"][dataset]["confirmatory_evaluation_ids"])
            self.assertFalse(sentinel & evaluation)
            self.assertEqual(confirmatory, sentinel | evaluation)

    def test_s3_is_not_prospective(self):
        self.assertEqual(self.s3["evidence_level"], "POST_HOC_ROLE_LIMITED")
        self.assertIn("PREVIOUSLY_INSPECTED", self.s3["historical_truth_status"])

    def test_inventory_hashes(self):
        inventory = ROOT / "results/sigmod_ea_postseal_uplift/s2_input_inventory.csv"
        with inventory.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            digest = hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest()
            self.assertEqual(digest, row["sha256"])


if __name__ == "__main__":
    unittest.main()
