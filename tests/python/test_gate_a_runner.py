import pytest

from scripts.gate_a.run_benchmark import resolve_ef_values

CONFIG = {
    "search": {
        "base_ef": [10, 20, 40, 80, 120, 200],
        "predeclared_midpoints": [15, 30, 60, 100, 160],
    }
}


def test_ef_values_default_to_frozen_base_grid() -> None:
    assert resolve_ef_values(CONFIG, None) == [10, 20, 40, 80, 120, 200]


def test_ef_values_accept_only_predeclared_grid_points() -> None:
    assert resolve_ef_values(CONFIG, "60,100,160") == [60, 100, 160]
    assert resolve_ef_values(CONFIG, "10,20,40,60,80,100,120,160,200") == [
        10,
        20,
        40,
        60,
        80,
        100,
        120,
        160,
        200,
    ]
    with pytest.raises(ValueError, match="predeclared"):
        resolve_ef_values(CONFIG, "50")
    with pytest.raises(ValueError, match="unique"):
        resolve_ef_values(CONFIG, "60,60")
