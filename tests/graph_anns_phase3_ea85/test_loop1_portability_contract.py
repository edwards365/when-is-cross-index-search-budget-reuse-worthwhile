from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = ROOT / "scripts/graph_anns_phase3_ea85"


def text(relative: str) -> str:
    return (SCRIPT_ROOT / relative).read_text(encoding="utf-8")


def test_shell_launchers_expose_root_overrides():
    for relative in (
        "run_darth95_bridge.sh",
        "run_phase2_refresh95_replay.sh",
        "adaef_bridge/run_adaef_extension.sh",
    ):
        source = text(relative)
        assert "ICBA_REPO_ROOT" in source
        assert "ICBA_EA85_ROOT" in source


def test_analysis_scripts_expose_data_root_cli():
    assert '"--data-root"' in text("analyze_darth95_bridge.py")
    assert '"--data500-root"' in text("analyze_phase3_vamana_unified.py")
    assert '"--data-root"' in text("analyze_phase4_deep1m.py")
    assert '"--data-root"' in text("run_phase4_deep1m.py")


def test_refresh_role_builder_exposes_raw_and_build_roots():
    source = text("prepare_refresh95_roles.py")
    assert '"--sift-hdf5"' in source
    assert '"--arxiv-hdf5"' in source
    assert '"--score8-root"' in source


def test_artifact_entrypoint_has_no_private_host_path():
    artifact = ROOT / "artifacts/graph_anns_phase3_ea85"
    for path in artifact.iterdir():
        if path.is_file() and path.suffix in {".md", ".csv", ".txt", ".sh"}:
            source = path.read_text(encoding="utf-8")
            assert "/home/wlk" not in source
            assert "101.6.160.66" not in source
