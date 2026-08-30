import json
from pathlib import Path
import pandas as pd,pytest
R=Path("results/icba_ordered_rung_semantic_reaudit")
@pytest.mark.parametrize("n",["rung_actions.csv","budget_action_monotonicity.csv","ndc_cost_monotonicity_diagnostic.csv","stable_budget_labels.csv","event_nesting_audit.csv","rejection_quadrants_corrected.csv","certificate_error_diagnostic.csv","sample_size_curves.csv","safety_margin.csv","fallback_cost_attribution.csv","tail_metrics.csv","fallback_frontier.csv","theory_contact_matrix_corrected.csv","unified_gate_table.csv"])
def test_outputs(n): assert (R/n).exists()
@pytest.mark.parametrize("ds",["sift_100k","arxiv_nomic_100k"])
def test_dataset(ds): assert ds in set(pd.read_csv(R/"rejection_quadrants_corrected.csv").dataset)
def test_no_ndc_budget(): assert "NDC is not budget action" in Path("docs/icba_ordered_rung_semantic_reaudit/semantic_correction_note.md").read_text()
def test_not_estimable_budget(): assert pd.read_csv(R/"budget_action_monotonicity.csv").budget_action_monotone.eq("NOT_ESTIMABLE").all()
def test_cp_event(): assert pd.read_csv(R/"rejection_quadrants_corrected.csv").eval_state.notna().all()
def test_no_oracle(): assert not json.loads(Path("manifests/icba_ordered_rung_semantic_reaudit_decision.json").read_text())["method_implementation_authorized"]
def test_legacy(): assert "111_OF_123" in Path("docs/icba_ordered_rung_semantic_reaudit/limitations.md").read_text()
def test_no_sealed():
 x=json.loads(Path("manifests/icba_ordered_rung_semantic_reaudit_decision.json").read_text()); assert not x["validation_dev_accessed"] and not x["formal_test_accessed"] and not x["gloVe_accessed"]
def test_decision(): assert json.loads(Path("manifests/icba_ordered_rung_semantic_reaudit_decision.json").read_text())["decision"].startswith("EXISTING_STAGE_FAMILY")
