import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "sigmod_s9" / "prepare_s9_3_inputs.py"
SPEC = importlib.util.spec_from_file_location("s9_3_inputs", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_exact_top10_l2():
    base = np.arange(20, dtype=np.float32).reshape(-1, 1)
    queries = np.asarray([[0.1], [18.9]], dtype=np.float32)
    got = MOD.exact_top10(base, queries, "l2", block=1)
    assert list(got[0, :3]) == [0, 1, 2]
    assert list(got[1, :3]) == [19, 18, 17]


def test_exact_top10_inner_product():
    base = np.eye(12, dtype=np.float32)
    queries = np.asarray([np.arange(12, dtype=np.float32)], dtype=np.float32)
    got = MOD.exact_top10(base, queries, "ip")
    assert list(got[0, :3]) == [11, 10, 9]
