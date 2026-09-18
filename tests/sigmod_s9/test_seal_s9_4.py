from pathlib import Path


def test_seal_script_exists():
    assert (Path(__file__).parents[2] / "scripts" / "sigmod_s9" / "seal_s9_4.py").is_file()
