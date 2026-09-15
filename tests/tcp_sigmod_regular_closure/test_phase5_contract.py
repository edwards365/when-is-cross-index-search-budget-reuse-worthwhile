import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Phase5ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / "scripts/tcp_sigmod_regular_closure/phase5_run.sh").read_text()

    def test_actual_ef_search_is_varied(self):
        self.assertIn('--efSearch "$ef"', self.text)
        self.assertNotIn("--fixed-amount-of-search", self.text)

    def test_frozen_seeds_and_grid(self):
        self.assertIn("source_seeds=(1103 1229 1361 1499 1621 1747 1877 1999 2131)", self.text)
        self.assertIn('${TCP_TARGET_SEEDS:-2381 2503 2633}', self.text)
        self.assertIn("grid=(10 20 40 80 120 160 200)", self.text)

    def test_refuses_overwrite(self):
        self.assertGreaterEqual(len(re.findall("refusing to overwrite", self.text)), 2)

    def test_darth_comparator_is_first_source_and_frozen(self):
        self.assertIn("seed_1103/model_11feat.txt", self.text)
        self.assertIn("--mode early-stop-testing", self.text)
        self.assertIn("--initial-prediction-interval 20", self.text)
        self.assertIn("--min-prediction-interval 5", self.text)


if __name__ == "__main__":
    unittest.main()
