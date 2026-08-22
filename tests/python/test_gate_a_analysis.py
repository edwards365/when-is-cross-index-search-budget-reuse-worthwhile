import numpy as np
import pandas as pd
from narhnsw.gate_a_analysis import (
    collapse_latency_rounds,
    curve_summary,
    matched_recall_cost,
    paired_query_bootstrap,
    realized_treatment,
    validate_method_pairing,
)


def query_fixture() -> pd.DataFrame:
    rows = []
    for method, offset in [("geometry", 0), ("ggr_0", -2)]:
        for ef, recall in [(10, 0.9), (20, 0.96)]:
            for query_id in range(4):
                for latency_round in range(2):
                    rows.append(
                        {
                            "dataset": "fixture",
                            "method": method,
                            "build_seed": 7,
                            "control_seed": np.nan,
                            "ef_search": ef,
                            "query_id": query_id,
                            "latency_round": latency_round,
                            "recall_at_10": recall,
                            "full_recall": recall == 1,
                            "ndc": 100 + ef + offset + query_id,
                            "visited_nodes": 80 + query_id,
                            "candidate_queue_pushes": 50,
                            "candidate_queue_pops": 40,
                            "latency_ns": 1000 + 10 * latency_round + offset,
                        }
                    )
    return pd.DataFrame(rows)


def test_query_schema_pairing_and_matched_recall() -> None:
    collapsed = collapse_latency_rounds(query_fixture())
    validate_method_pairing(collapsed, {"geometry", "ggr_0"}, 4)
    curve = curve_summary(collapsed)
    geometry = curve[curve["method"] == "geometry"]
    cost = matched_recall_cost(geometry, target_recall=0.95, quantile=0.95)
    assert cost.ef_search == 20
    assert cost.observed_recall == 0.96
    assert cost.ndc_cost is not None


def test_bootstrap_is_paired_and_reproducible() -> None:
    left = np.array([10, 20, 30, 40], dtype=float)
    right = left + 2
    first = paired_query_bootstrap(
        left, right, statistic="q0.95", replicates=500, seed=91
    )
    second = paired_query_bootstrap(
        left, right, statistic="q0.95", replicates=500, seed=91
    )
    assert first == second
    assert first["estimate"] == -2


def test_realized_treatment_reports_directed_and_support_changes() -> None:
    geometry = {(0, 1), (1, 0), (1, 2)}
    method = {(0, 1), (1, 0), (1, 3)}
    result = realized_treatment(geometry, method)
    assert result["added_directed_edges"] == 1
    assert result["removed_directed_edges"] == 1
    assert result["changed_sources"] == 1
    assert result["directed_jaccard"] == 0.5
    assert result["support_jaccard"] == 1 / 3


def test_incomplete_method_pairing_is_rejected() -> None:
    collapsed = collapse_latency_rounds(query_fixture())
    incomplete = collapsed.drop(collapsed.index[0])
    try:
        validate_method_pairing(incomplete, {"geometry", "ggr_0"}, 4)
    except ValueError as error:
        assert "pairing" in str(error) or "incomplete" in str(error)
    else:
        raise AssertionError("incomplete pairing was accepted")
