import json
import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "rebuild_portability_recovery"


def test_preregistered_gate_counts():
    with (RES / "m1_target_residual_calibration.csv").open(newline="") as f:
        m1 = list(csv.DictReader(f))
    with (RES / "m2_m3_looh.csv").open(newline="") as f:
        m23 = list(csv.DictReader(f))
    assert {int(r["k"]) for r in m1} == {32, 64, 128, 256}
    assert len(m1) == 576
    assert Counter(int(r["k"]) for r in m1 if r["gate_s"] == "PASS") == {
        32: 144, 64: 144, 128: 144, 256: 144
    }
    expected = {
        "M2": {32: 99, 64: 102, 128: 141, 256: 144},
        "M3": {32: 100, 64: 103, 128: 141, 256: 144},
    }
    for method, counts in expected.items():
        got = Counter(
            int(r["k"]) for r in m23
            if r["method"] == method and r["gate_s"] == "PASS"
        )
        assert got == counts


def test_decision_firewall_and_label():
    manifest = json.loads(
        (ROOT / "manifests" / "rebuild_portability_recovery_decision.json").read_text()
    )
    assert manifest["decision"] == "TARGET_ONLY_RECALIBRATION_SUFFICIENT_NO_NEW_METHOD"
    assert manifest["evidence_label"] == "EXPLORATORY_DESIGN"
    assert not manifest["validation_dev_accessed"]
    assert not manifest["formal_test_accessed"]
    assert not manifest["new_graphs_built"]
    assert not manifest["confirmatory_claim"]


if __name__ == "__main__":
    test_preregistered_gate_counts()
    test_decision_firewall_and_label()
    print("RECOVERY_GATE_TEST_PASS")
