from pathlib import Path


def test_runtime_script_exists():
    path = Path(__file__).parents[2] / "scripts" / "sigmod_s9" / "run_s9_4_runtime.py"
    assert path.is_file()
