#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


root = Path(sys.argv[1])
contract_path = root / "query_trace_contract24.csv"
summary_path = root / "query_trace_summary.csv"

expected = [
    "query_id", "build_id", "source_target_id", "requested_ef",
    "actual_expansions", "actual_ndc", "wall_clock_ns", "upper_layer_path",
    "base_layer_expansion_order", "candidate_queue_insertion_order",
    "introduction_parent_edge", "composite_priority_key",
    "top_candidate_heap_state", "lower_bound_change", "visited_state",
    "first_safe_discovery", "endpoint_status", "checkpoint_top_k",
    "checkpoint_candidate_set", "backup_path", "edge_layer", "tie_event",
    "filter_deletion_state", "search_stop_reason",
]

with contract_path.open(newline="") as handle:
    reader = csv.DictReader(handle)
    rows = list(reader)

checks = []
checks.append(("schema_exact_24", reader.fieldnames == expected))
checks.append(("row_count_768", len(rows) == 768))
checks.append(("no_empty_cells", all(all(row[name] != "" for name in expected) for row in rows)))
checks.append(("query_ids_256", len({int(row["query_id"]) for row in rows}) == 256))
checks.append(("ef_grid_exact", {int(row["requested_ef"]) for row in rows} == {10, 20, 40}))
checks.append(("positive_expansions", all(int(row["actual_expansions"]) > 0 for row in rows)))
checks.append(("positive_ndc", all(int(row["actual_ndc"]) > 0 for row in rows)))
checks.append(("positive_wall_clock", all(int(row["wall_clock_ns"]) > 0 for row in rows)))
checks.append(("build_id_frozen", {row["build_id"] for row in rows} == {"synthetic_seed7"}))
checks.append(("source_target_recorded", all(row["source_target_id"].isdigit() for row in rows)))
checks.append(("priority_key_recorded", all(row["composite_priority_key"].startswith("(") for row in rows)))
checks.append(("stop_reason_valid", {row["search_stop_reason"] for row in rows} <= {"DISTANCE_BOUND", "CANDIDATE_QUEUE_EMPTY"}))
checks.append(("base_path_recorded", all(row["base_layer_expansion_order"] != "NONE" for row in rows)))
checks.append(("candidate_insertion_recorded", all(row["candidate_queue_insertion_order"] != "NONE" for row in rows)))
checks.append(("introduction_edge_recorded", all(row["introduction_parent_edge"] != "NONE" for row in rows)))
checks.append(("endpoint_is_nontruth_sentinel", {row["endpoint_status"] for row in rows} == {"SEARCH_COMPLETED_TRUTH_NOT_EVALUATED"}))
checks.append(("first_safe_is_nontruth_sentinel", {row["first_safe_discovery"] for row in rows} == {"TRUTH_NOT_PROVIDED"}))
checks.append(("edge_layer_recorded", all(row["edge_layer"] != "NONE" for row in rows)))

with summary_path.open(newline="") as handle:
    summary_rows = list(csv.DictReader(handle))
checks.append(("summary_row_count_768", len(summary_rows) == 768))
checks.append(("summary_recall_bounded", all(0.0 <= float(row["recall"]) <= 1.0 for row in summary_rows)))
checks.append(("summary_requested_ef_equal", {int(row["ef"]) for row in summary_rows} == {10, 20, 40}))
checks.append(("summary_ndc_recorded", all(int(row["exact_ndc"]) > 0 for row in summary_rows)))

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'},{name}")
if failed:
    raise SystemExit("failed checks: " + ", ".join(failed))
print(f"PASS_COUNT={len(checks)}")
