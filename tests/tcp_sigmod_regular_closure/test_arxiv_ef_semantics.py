from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/tcp_sigmod_regular_closure/run_arxiv_fixed_ef_v2.sh"

def test_fixed_runner_uses_actual_efsearch_grid(tmp_path):
    env = os.environ.copy()
    env["TCP_DRY_RUN"] = "1"
    env["TCP_ARXIV_OUTPUT_ROOT"] = str(tmp_path)
    result = subprocess.run(["bash", str(RUNNER)], check=True, capture_output=True, text=True, env=env)
    commands = [x for x in result.stdout.splitlines() if "--mode no-early-stop" in x]
    assert len(commands) == 140
    for ef in (10, 20, 40, 80, 120, 160, 200):
        assert sum(f"--efSearch {ef} " in x for x in commands) == 20
    assert all("--fixed-amount-of-search" not in x for x in commands)

def test_old_arxiv_results_are_listed_as_invalidated():
    text = (ROOT / "manifests/tcp_sigmod_regular_closure_preregistration.json").read_text()
    assert "constant-efSearch runner" in text
