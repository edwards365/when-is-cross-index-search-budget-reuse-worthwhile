from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/graph_anns_e4_hotfix"
DOC = ROOT / "docs/graph_anns_e4_hotfix"


def read(name):
    return pd.read_csv(OUT / name)


def test_a4_partition_is_complete():
    x = read("h1a4_censoring_state_corrected.csv")
    assert (x.all_feasible_count + x.mixed_feasible_censored_count + x.all_censored_count == x.query_count).all()


def test_a4_has_750_queries_per_dataset():
    assert read("h1a4_censoring_state_corrected.csv").query_count.eq(750).all()


def test_a4_rates_match_counts():
    x = read("h1a4_censoring_state_corrected.csv")
    assert np.allclose(x.mixed_feasible_censored_rate, x.mixed_feasible_censored_count / x.query_count)


def test_a4_estimand_is_feasibility_state_only():
    assert read("h1a4_censoring_state_corrected.csv").estimand.eq("MIXED_FEASIBLE_CENSORED_STATE_RATE").all()


def test_h1_registered_denominators():
    x = read("h1_pairwise_feasible_recheck.csv")
    expected = {"H1-B": 18000, "H1-C": 63000}
    assert all(r.total_comparisons == expected[r.estimand_id] for r in x.itertuples())


def test_h1_effective_denominator_is_joint_feasible():
    x = read("h1_pairwise_feasible_recheck.csv")
    assert x.effective_denominator.equals(x.jointly_feasible_comparisons)


def test_h1_partition_joint_and_mismatch_bounded():
    x = read("h1_pairwise_feasible_recheck.csv")
    assert ((x.jointly_feasible_comparisons + x.censoring_mismatch_comparisons) <= x.total_comparisons).all()


def test_h1_finite_estimands():
    x = read("h1_pairwise_feasible_recheck.csv")
    assert np.isfinite(x[["jointly_feasible_disagreement", "jointly_feasible_absolute_difference"]]).all().all()


def test_h2_risk_identity():
    x = read("h2_robustness_corrected.csv")
    assert np.allclose(x.absolute_transport_risk - x.reference_risk, x.risk_increment)


def test_h2_all_registered_positive():
    x = read("h2_robustness_corrected.csv").query("analysis == 'all_registered'")
    assert (x.risk_increment > 0).all() and (x.safe_rom_ndc_tax > 0).all()


def test_h2_random_only_positive():
    x = read("h2_robustness_corrected.csv").query("analysis == 'random_only'")
    assert (x.risk_increment > 0).all() and (x.safe_rom_ndc_tax > 0).all()


def test_h2_two_sided_seed_deletions_present():
    x = read("h2_robustness_corrected.csv")
    for a in ["leave_one_seed", "source_only_delete", "target_only_delete"]:
        assert len(x.query("analysis == @a")) == 16


def test_h2_leave_one_order_present():
    assert len(read("h2_robustness_corrected.csv").query("analysis == 'leave_one_order'")) == 6


def test_h2_all_registered_pairs_are_552():
    assert read("h2_robustness_corrected.csv").query("analysis == 'all_registered'").pair_count.eq(552).all()


def test_h2_all_deletion_directions_positive():
    x = read("h2_robustness_corrected.csv")
    assert x.direction_positive.all()


def test_event_composition_complete():
    x = read("transport_event_composition_complete.csv")
    assert np.allclose(x.composition_sum, 1.0)


def test_event_composition_nonnegative():
    x = read("transport_event_composition_complete.csv")
    cols = ["BOTH_RIGHT_CENSORED", "SOURCE_ONLY_RIGHT_CENSORED", "TARGET_ONLY_RIGHT_CENSORED", "UNDER_BUDGET_UNSAFE", "UNDER_BUDGET_OBSERVED_SAFE", "EXACT_BUDGET_SAFE", "OVER_BUDGET_SAFE"]
    assert (x[cols] >= 0).all().all() and (x[cols] <= 1).all().all()


def test_raw_nonmonotonicity_is_separate():
    x = read("transport_event_composition_complete.csv")
    assert "raw_nonmonotone_rate" in x and np.allclose(x.raw_nonmonotone_rate, 0)


def test_deployed_candidates_are_certified():
    x = read("deployment_decision_corrected.csv")
    z = x.query("deploy_decision == 'DEPLOY_CERTIFIED_CANDIDATE'")
    assert z.candidate_certificate_pass.all() and z.deployed_action.notna().all()


def test_uncertified_candidate_never_deployed():
    x = read("deployment_decision_corrected.csv")
    assert not ((~x.candidate_certificate_pass) & x.deploy_decision.eq("DEPLOY_CERTIFIED_CANDIDATE")).any()


def test_uncertified_fallback_never_deployed():
    x = read("deployment_decision_corrected.csv")
    assert not ((~x.fallback_certificate_pass) & x.deploy_decision.eq("DEPLOY_CERTIFIED_FALLBACK")).any()


def test_abstention_has_no_action():
    x = read("deployment_decision_corrected.csv")
    assert x.loc[x.deploy_decision.eq("ABSTAIN_NO_CERTIFIED_ACTION"), "deployed_action"].isna().all()


def test_deployment_counts_match_manifest():
    x = read("deployment_decision_corrected.csv")
    m = json.loads((ROOT / "manifests/graph_anns_e4_hotfix_decision.json").read_text())
    assert (x.query("dataset == 'sift_100k'").deploy_decision == "ABSTAIN_NO_CERTIFIED_ACTION").sum() == m["sift_abstain"]
    assert (x.query("dataset == 'arxiv_nomic_100k'").deploy_decision == "ABSTAIN_NO_CERTIFIED_ACTION").sum() == m["arxiv_abstain"]


def test_clopper_pearson_is_one_sided():
    assert np.isclose(beta.ppf(0.95, 1, 250), 1 - 0.05 ** (1 / 250))


def test_manifest_freezes_no_new_experiment():
    m = json.loads((ROOT / "manifests/graph_anns_e4_hotfix_decision.json").read_text())
    assert not m["new_ann_search"] and not m["new_index_build"]


def test_manifest_forbids_sealed_access():
    m = json.loads((ROOT / "manifests/graph_anns_e4_hotfix_decision.json").read_text())
    assert not m["validation_dev_accessed"] and not m["formal_test_accessed"] and not m["future_replication_accessed"]


def test_claims_keep_grid_censoring_scope():
    text = (DOC / "paper_claim_hotfix.md").read_text()
    assert "finite registered hnswlib rebuilds" in text and "true endpoint heterogeneity" in text

