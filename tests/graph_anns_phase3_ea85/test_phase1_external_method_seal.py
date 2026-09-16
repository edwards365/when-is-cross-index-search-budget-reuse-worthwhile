import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGG = ROOT / "results/graph_anns_phase3_ea85/adaef_bridge/arxiv_10build/aggregate.json"
ROWS = ROOT / "results/graph_anns_phase3_ea85/adaef_bridge/arxiv_10build/build_metrics.csv"
DECISION = ROOT / "manifests/graph_anns_phase3_ea85/p1_external_method_decision.json"


def test_adaef_ten_build_seal():
    aggregate = json.loads(AGG.read_text())
    rows = list(csv.DictReader(ROWS.open()))
    assert aggregate["status"] == "TEN_BUILD_EXTENSION_COMPLETE"
    assert aggregate["builds"] == 10
    assert len(rows) == 10
    assert aggregate["all_raw_failed_certificate"] is True
    assert aggregate["all_fixed_safe_passed_certificate"] is True
    assert aggregate["all_deployments"] == ["FIXED_SAFE_EF200"]
    assert aggregate["intervals"]["raw_eval_risk"]["ci95_low"] > 0.05
    assert aggregate["intervals"]["audited_gain_vs_fixed"]["mean"] == 0.0


def test_phase1_claim_boundary():
    decision = json.loads(DECISION.read_text())
    assert decision["status"] == "PHASE1_COMPLETE"
    assert decision["methods"]["DARTH"]["raw_certified_builds"] == 0
    assert decision["methods"]["Ada-ef"]["raw_certified_builds"] == 0
    assert decision["methods"]["Ada-ef"]["fixed_safe_certified_builds"] == 10
    assert "TCP positive value is not established" in decision["claim_boundary"]
