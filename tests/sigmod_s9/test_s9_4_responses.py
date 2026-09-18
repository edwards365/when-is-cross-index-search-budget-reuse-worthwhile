import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "scripts" / "sigmod_s9" / "run_s9_4_responses.py"
SPEC = importlib.util.spec_from_file_location("s9p4_responses", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_roles_are_complete_and_disjoint():
    members = []
    for start, stop in MODULE.ROLE_OFFSETS.values():
        members.extend(range(start, stop))
    assert members == list(range(1500))


def test_grid_matches_protocol():
    assert MODULE.GRID == [16, 32, 64, 128, 256, 512]
