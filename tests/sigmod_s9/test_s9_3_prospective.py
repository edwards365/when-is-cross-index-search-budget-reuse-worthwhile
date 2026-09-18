import importlib.util
from pathlib import Path

import numpy as np


MODULE_PATH = Path(__file__).parents[2] / "scripts" / "sigmod_s9" / "run_s9_3_prospective.py"
SPEC = importlib.util.spec_from_file_location("s9p3", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_registered_grid_and_seed_cardinality():
    assert MODULE.GRID == [16, 32, 64, 128, 256, 512]
    assert len(MODULE.SEEDS) == 8
    assert len(set(MODULE.SEEDS)) == 8


def test_build_index_preserves_external_ids():
    rng = np.random.default_rng(7)
    base = rng.normal(size=(64, 8)).astype(np.float32)
    permutation = rng.permutation(len(base)).astype(np.int64)
    index = MODULE.build_index(base, permutation)
    MODULE.core(index).hnsw.efSearch = 64
    faiss = MODULE.faiss
    faiss.cvar.hnsw_stats.reset()
    _, found = index.search(base[:8], 1)
    assert np.array_equal(found[:, 0], np.arange(8))
    assert faiss.cvar.hnsw_stats.n3 > 0
    assert faiss.cvar.hnsw_stats.ndis == 0


def test_role_offsets_are_disjoint_and_complete():
    members = []
    for start, stop in MODULE.ROLE_OFFSETS.values():
        members.extend(range(start, stop))
    assert members == list(range(1500))
