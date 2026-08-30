import json
from pathlib import Path
import pandas as pd, pytest
R=Path("results/icba_certification_fallback_autopsy")
@pytest.mark.parametrize("n",["rejection_quadrants.csv","sample_size_curves.csv","safety_margin.csv","ordered_policy_violations.csv","fallback_frontier.csv","tail_attribution.csv","cost_break_even.csv","theory_contact_matrix.csv","unified_gate_table.csv","mechanism_contributions.csv"])
def test_table(n): assert (R/n).exists() and (R/n).stat().st_size>0
@pytest.mark.parametrize("ds",["sift_100k","arxiv_nomic_100k"])
def test_quadrants(ds): assert set(pd.read_csv(R/"rejection_quadrants.csv").query("dataset==@ds").quadrant)=={"SAFE_ACCEPTED","SAFE_BUT_REJECTED","UNSAFE_REJECTED","UNSAFE_ACCEPTED"}
@pytest.mark.parametrize("m",[59,64,90,96,122,128,154,186,218,234,250])
def test_requested_m(m): assert m in set(pd.read_csv(R/"sample_size_curves.csv").certification_m)
def test_cp_consistency(): assert pd.read_csv(R/"rejection_quadrants.csv").event_consistent.all()
def test_unsafe_acceptance_present(): assert (pd.read_csv(R/"rejection_quadrants.csv").quadrant=="UNSAFE_ACCEPTED").any()
def test_order_failed(): assert pd.read_csv(R/"ordered_policy_violations.csv").failure_violations.sum()>0
def test_gate_not_authorized(): assert not pd.read_csv(R/"unified_gate_table.csv")["pass"].all()
def test_manifest(): assert json.loads(Path("manifests/icba_certification_fallback_autopsy_decision.json").read_text())["decision"]=="MIXED_CERTIFICATION_AND_FALLBACK_BOTTLENECK"
def test_no_sealed_access():
 x=json.loads(Path("manifests/icba_certification_fallback_autopsy_decision.json").read_text()); assert not x["validation_dev_accessed"] and not x["formal_test_accessed"]
