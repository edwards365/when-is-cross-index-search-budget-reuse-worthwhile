from pathlib import Path

from scripts.gate_a.compare_plan_prefix import compare_audit, prefix_sha256


def test_prefix_hash_matches_concatenated_plan(tmp_path: Path) -> None:
    (tmp_path / "000000_000002_geometry.csv").write_bytes(b"0,1\n1,2\n")
    (tmp_path / "000002_000003_geometry.csv").write_bytes(b"2,3\n")
    combined = tmp_path / "combined.csv"
    combined.write_bytes(b"0,1\n1,2\n2,3\n")
    import hashlib

    assert prefix_sha256(tmp_path, "geometry", 3, 2) == hashlib.sha256(
        combined.read_bytes()
    ).hexdigest()


def test_audit_comparison_allows_only_tiny_float_roundoff() -> None:
    old = [
        {
            "center": "7",
            "method": "ggr_0",
            "swap_steps": "2",
            "terminal_changed_edges": "2",
            "geometry_base": "1.0",
            "geometry_final": "0.9",
            "true_frozen_leverage_total": "4.0",
        }
    ]
    new = [{**old[0], "true_frozen_leverage_total": "4.00000000001"}]
    comparison = compare_audit(old, new, tolerance=1e-10)
    assert comparison["rows_match"]
    assert comparison["discrete_mismatches"] == 0
    assert comparison["floating_mismatches"] == 0
