import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[2] / "scripts/graph_anns_phase3_ea85/run_phase4_deep1m.py"
SPEC = importlib.util.spec_from_file_location("deep1m", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_normalize_unit_length():
    x = np.array([[3.0, 4.0], [1.0, 0.0]], dtype=np.float32)
    y = MOD.normalize(x)
    assert np.allclose(np.linalg.norm(y, axis=1), 1.0)


def test_registered_query_sampler_excludes_prior_p10():
    prior = set(np.sort(np.random.RandomState(991).choice(10000, 500, replace=False)).tolist())
    remaining = np.asarray([i for i in range(10000) if i not in prior], dtype=int)
    ids = np.sort(np.random.default_rng(2991).choice(remaining, 1000, replace=False))
    assert len(ids) == len(set(ids.tolist())) == 1000
    assert not (prior & set(ids.tolist()))
