import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/graph_anns_phase3_ea85/artifact_smoke.py"
SPEC = importlib.util.spec_from_file_location("artifact_smoke", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_sha256_known_value(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"abc")
    assert MOD.sha256(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_smoke_is_read_only():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "write_text" not in text
    assert "raw_truth_accessed\": False" in text
