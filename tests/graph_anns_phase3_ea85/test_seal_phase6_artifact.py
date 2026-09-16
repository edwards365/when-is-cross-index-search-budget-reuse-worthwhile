import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/graph_anns_phase3_ea85/seal_phase6_artifact.py"
SPEC = importlib.util.spec_from_file_location("seal_artifact", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)


def test_seal_has_identity_guard():
    text = SCRIPT.read_text(encoding="utf-8")
    assert '"wlk", "101.6.160.66", "/home/"' in text
    assert "raw_truth_accessed\": False" in text


def test_full_replay_boundary_is_explicit():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "REQUIRES_EXTERNAL_DATA_AND_PATH_MAPPING" in text
