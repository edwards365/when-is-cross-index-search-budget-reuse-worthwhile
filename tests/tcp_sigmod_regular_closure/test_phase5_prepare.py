import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "tcp_sigmod_regular_closure"))

from phase5_prepare import exact_truth, permutation  # noqa: E402


class Phase5PrepareTest(unittest.TestCase):
    def test_permutation_inverse(self):
        order, inverse = permutation(2381, 100)
        np.testing.assert_array_equal(inverse[order], np.arange(100))

    def test_truth_ids_remap_to_same_vectors(self):
        base = np.arange(80, dtype=np.float32).reshape(20, 4)
        queries = base[[2, 11]] + 0.01
        ids, _ = exact_truth(base, queries, "l2", top=3, block=1)
        order, inverse = permutation(2503, len(base))
        mapped = inverse[ids]
        np.testing.assert_array_equal(base[ids], base[order][mapped])

    def test_angular_nearest(self):
        base = np.eye(4, dtype=np.float32)
        ids, distances = exact_truth(base, base[[2]], "angular", top=2)
        self.assertEqual(int(ids[0, 0]), 2)
        self.assertAlmostEqual(float(distances[0, 0]), 0.0)


if __name__ == "__main__":
    unittest.main()
