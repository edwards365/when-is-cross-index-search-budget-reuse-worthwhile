import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "sigmod_s9" / "run_s9_2_faiss_runtime.py"
SPEC = importlib.util.spec_from_file_location("s9_runtime", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def test_action_schedule_is_deterministic_and_complete():
    first = MOD.action_order("build", 501, 2)
    second = MOD.action_order("build", 501, 2)
    assert first == second
    assert sorted(first) == list(MOD.GRID)


def test_action_schedule_changes_across_repetition():
    assert MOD.action_order("build", 501, 1) != MOD.action_order("build", 501, 2)


def test_role_ids_are_disjoint():
    cert = set(MOD.selected_query_ids("target_certification", 500))
    evaluation = set(MOD.selected_query_ids("target_evaluation", 500))
    assert len(cert) == len(evaluation) == 500
    assert not cert & evaluation


def test_warmup_count_does_not_shrink_with_smoke_query_count():
    assert len(MOD.warmup_query_ids("target_evaluation", 50)) == 50
    assert MOD.warmup_query_ids("target_evaluation", 50)[0] == 500


def test_cv_is_zero_for_constant_measurements():
    assert MOD.coefficient_of_variation([10, 10, 10]) == 0.0


def test_cv_tracks_block_variation():
    assert 0.09 < MOD.coefficient_of_variation([90, 100, 110]) < 0.11
