import json
from pathlib import Path
import pandas as pd
import pytest
R=Path("results/icba_active_observation")
@pytest.mark.parametrize("name", ["failure_counterfactuals.csv","failure_shapley.csv","fallback_tail_attribution.csv","cost_margin.csv","risk_margin.csv","uniform_estimation.csv","theory_assumption_contact.csv","label_allocation_frontier.csv","active_probe_results.csv","probe_information.csv","transcript_separation.csv","unified_gate_table.csv"])
def test_required_table(name): assert (R/name).exists() and (R/name).stat().st_size>0
@pytest.mark.parametrize("sel",[16,32,64,96,128,160,191])
def test_frontier_split(sel):
 d=pd.read_csv(R/"label_allocation_frontier.csv"); assert set(d[d.selection==sel].certification)=={250-sel}
@pytest.mark.parametrize("ds",["sift_100k","arxiv_nomic_100k"])
def test_no_oracle_joint_pass(ds):
 d=pd.read_csv(R/"label_allocation_frontier.csv"); x=d[d.dataset==ds]; assert not ((x.relative_gain>=.05)&x.p95_not_worse&(x.risk_ucb<=.05)&(x.delete_max_build_gain>0)&(x.loto_min_gain>0)).any()
def test_legacy_label(): assert "111_OF_123" in Path("docs/icba_active_observation/limitations.md").read_text()
def test_no_formal_claim(): assert "open-world claim" in Path("docs/icba_active_observation/limitations.md").read_text()
def test_decision_label(): assert json.loads(Path("manifests/icba_active_observation_decision.json").read_text())["decision"]=="FAILURE_DOMINATED_BY_CERTIFICATION_AND_FALLBACK"
