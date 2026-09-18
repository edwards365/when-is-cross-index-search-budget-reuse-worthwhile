import importlib.util
from pathlib import Path

import numpy as np


MODULE_PATH = Path(__file__).parents[2] / "scripts" / "sigmod_s9" / "prepare_s9_4_inputs.py"
SPEC = importlib.util.spec_from_file_location("s9p4_inputs", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_exact_top10_l2():
    base = np.asarray([[0.0], [1.0], [2.0], [3.0], [4.0], [5.0], [6.0], [7.0], [8.0], [9.0], [10.0]], np.float32)
    query = np.asarray([[0.1]], np.float32)
    assert MODULE.exact_top10(base, query, "l2").shape == (1, 10)
    assert MODULE.exact_top10(base, query, "l2")[0, 0] == 0


def test_exact_top10_inner_product():
    base = np.eye(11, dtype=np.float32)
    query = np.zeros((1, 11), np.float32)
    query[0, 7] = 1.0
    assert MODULE.exact_top10(base, query, "ip")[0, 0] == 7
