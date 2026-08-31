import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from scipy.stats import beta


ROOT = Path.cwd()
RAW_EFS = [10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]
BUILD_IDS = ["G1", "G2", "G3"]
ALPHA = 0.05


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def percentile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def cp_ucb(failures, n, family_size):
    if failures >= n:
        return 1.0
    return float(beta.ppf(1 - ALPHA / family_size, failures + 1, n - failures))


def summarize(rows, family_size):
    assert len(rows) == 256
    assert [int(row["query_row"]) for row in rows] == list(range(256))
    assert all(
        row["endpoint_status"] != "PASS"
        or (row["native_tracer_topk_equal"] == "1" and row["native_tracer_ndc_equal"] == "1")
        for row in rows
    )
    failures = sum(int(row["Z_abs"]) for row in rows)
    endpoint_failures = sum(row["endpoint_status"] != "PASS" for row in rows)
    ndc = [int(row["native_ndc"]) for row in rows]
    expansions = [int(row["actual_expansions"]) for row in rows]
    wall = [int(row["wall_clock_ns"]) for row in rows]
    recall = [float(row["raw_recall_at_10"]) for row in rows]
    ucb = cp_ucb(failures, len(rows), family_size)
    return {
        "n": len(rows),
        "failures": failures,
        "endpoint_failures": endpoint_failures,
        "mean_recall_at_10": sum(recall) / len(recall),
        "risk_cp_ucb": ucb,
        "risk_cp_family_size": family_size,
        "certified": ucb <= 0.05,
        "mean_ndc": sum(ndc) / len(ndc),
        "p50_ndc": percentile(ndc, 0.50),
        "p95_ndc": percentile(ndc, 0.95),
        "p99_ndc": percentile(ndc, 0.99),
        "mean_expansions": sum(expansions) / len(expansions),
        "p95_expansions": percentile(expansions, 0.95),
        "mean_wall_clock_ns": sum(wall) / len(wall),
        "p95_wall_clock_ns": percentile(wall, 0.95),
        "p99_wall_clock_ns": percentile(wall, 0.99),
    }


def same_number(left, right):
    return math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-9)


def assert_summary_equal(actual, recorded):
    for key, value in actual.items():
        if isinstance(value, float):
            assert same_number(value, recorded[key]), (key, value, recorded[key])
        else:
            assert value == recorded[key], (key, value, recorded[key])


def choice(actions):
    certified = [action for action in actions if action["statistics"]["certified"]]
    if not certified:
        return None
    return min(
        certified,
        key=lambda action: (
            action["statistics"]["mean_ndc"],
            action["statistics"]["p95_ndc"],
            action["requested_ef"],
            BUILD_IDS.index(action["build_id"]),
        ),
    )


def compare_csv_prefix(first, second, ignored, allow_trailing_incomplete=False):
    left = read_csv(first)
    right = read_csv(second)
    assert left
    assert len(left) <= len(right)
    fields = [key for key in left[0] if key not in ignored]
    complete_rows = left
    missing = [key for key in fields if left[-1].get(key) is None]
    if missing:
        assert allow_trailing_incomplete
        complete_rows = left[:-1]
    for index, row in enumerate(complete_rows):
        assert all(row.get(key) is not None for key in fields)
        assert {key: row[key] for key in fields} == {key: right[index][key] for key in fields}
    return len(complete_rows)


selected_path = ROOT / "manifests/icba_cibs_stage1_selected_actions.json"
gate_path = ROOT / "results/icba_cibs_stage1/sentinel_gate.json"
certificate_path = ROOT / "results/icba_cibs_stage1/sentinel/sentinel_procedure_certificate.json"
selected = json.loads(selected_path.read_text(encoding="utf-8"))
gate = json.loads(gate_path.read_text(encoding="utf-8"))
certificate = json.loads(certificate_path.read_text(encoding="utf-8"))

assert gate["status"] == "PASS_SENTINEL_SELECTION_FROZEN"
assert gate["selected_action_manifest_sha256"] == sha256(selected_path)
assert gate["sentinel_certificate_sha256"] == sha256(certificate_path)
assert gate["evaluation_access_authorized_next"] is True
assert gate["evaluation_reselection_allowed"] is False
assert gate["future_confirm_accessed"] is False
assert certificate["evaluation_accessed"] is False
assert certificate["future_confirm_accessed"] is False
assert certificate["sentinel_semantics"] == "FROZEN_FINITE_POOL_WITHOUT_REPLACEMENT"

summary = {"rows": {}, "selected": {}, "certified": {}, "replay_rows": {}}
for dataset in ("sift_100k", "arxiv_nomic_100k"):
    recorded = {action["action_id"]: action for action in certificate["actions"][dataset]}
    assert len(recorded) == 36
    raw_files = {entry["build_id"]: entry for entry in certificate["raw_action_files"][dataset]}
    recomputed = []
    rows_by_build = {}
    for build_id in BUILD_IDS:
        entry = raw_files[build_id]
        path = ROOT / entry["path"]
        assert sha256(path) == entry["sha256"]
        rows = read_csv(path)
        rows_by_build[build_id] = rows
        assert len(rows) == 256 * len(RAW_EFS)
        groups = defaultdict(list)
        for row in rows:
            groups[int(row["requested_ef"])].append(row)
        assert sorted(groups) == RAW_EFS
        for ef in RAW_EFS:
            action_id = f"{build_id}:ef={ef}"
            stats = summarize(groups[ef], 36)
            assert_summary_equal(stats, recorded[action_id]["statistics"])
            recomputed.append({"action_id": action_id, "build_id": build_id, "requested_ef": ef, "statistics": stats})
    primary = choice(recomputed)
    frozen_primary = selected["datasets"][dataset]["B4_CIBS_FIXED"]
    if primary is None:
        assert frozen_primary["kind"] == "fixed_safe_fallback"
    else:
        assert frozen_primary["action_id"] == primary["action_id"]
    g1_alpha12 = []
    g1_groups = defaultdict(list)
    for row in rows_by_build["G1"]:
        g1_groups[int(row["requested_ef"])].append(row)
    for ef in RAW_EFS:
        g1_alpha12.append({
            "action_id": f"G1:ef={ef}",
            "build_id": "G1",
            "requested_ef": ef,
            "statistics": summarize(g1_groups[ef], 12),
        })
    b1 = choice(g1_alpha12)
    frozen_b1 = selected["datasets"][dataset]["B1"]
    if b1 is None:
        assert frozen_b1["kind"] == "fixed_safe_fallback"
    else:
        assert frozen_b1["action_id"] == b1["action_id"]
    assert selected["datasets"][dataset]["B2"]["action_id"] == "G1:ef=512"
    assert selected["datasets"][dataset]["B3"]["action_id"] == "G2:ef=512"
    summary["rows"][dataset] = sum(len(rows) for rows in rows_by_build.values())
    summary["selected"][dataset] = frozen_primary.get("action_id", "G1:ef=100000:fallback")
    summary["certified"][dataset] = sum(action["statistics"]["certified"] for action in recomputed)

attempt1 = ROOT / "results/icba_cibs_stage1/sentinel_interrupted_attempt1"
attempt2 = ROOT / "results/icba_cibs_stage1/sentinel"
summary["replay_rows"]["sift_truth"] = compare_csv_prefix(
    attempt1 / "sift_100k__sentinel_truth.csv",
    attempt2 / "sift_100k__sentinel_truth.csv",
    {"truth_acquisition_wall_clock_ns"},
)
for build_id in BUILD_IDS:
    summary["replay_rows"][f"sift_{build_id}"] = compare_csv_prefix(
        attempt1 / f"sift_100k__{build_id}__sentinel_actions.csv",
        attempt2 / f"sift_100k__{build_id}__sentinel_actions.csv",
        {"wall_clock_ns"},
    )
summary["replay_rows"]["arxiv_truth"] = compare_csv_prefix(
    attempt1 / "arxiv_nomic_100k__sentinel_truth.csv",
    attempt2 / "arxiv_nomic_100k__sentinel_truth.csv",
    {"truth_acquisition_wall_clock_ns"},
)
summary["replay_rows"]["arxiv_G1_partial"] = compare_csv_prefix(
    attempt1 / "arxiv_nomic_100k__G1__sentinel_actions.csv",
    attempt2 / "arxiv_nomic_100k__G1__sentinel_actions.csv",
    {"wall_clock_ns"},
    allow_trailing_incomplete=True,
)

with (ROOT / "results/icba_cibs_stage1/phase1/query_roles/truth_access_log.csv").open(newline="") as handle:
    access = list(csv.DictReader(handle))
assert len(access) == 8
for row in access:
    if row["role"] in {"cibs_design", "cibs_sentinel"}:
        assert row["truth_accessed"] == "1" and row["action_outcome_accessed"] == "1"
    else:
        assert row["truth_accessed"] == "0" and row["action_outcome_accessed"] == "0"

summary.update({
    "status": "PASS_INDEPENDENT_SENTINEL_SELECTION_AND_REPLAY_VALIDATION",
    "selected_manifest_sha256": sha256(selected_path),
    "sentinel_certificate_sha256": sha256(certificate_path),
    "truth_access_log_sha256": sha256(ROOT / "results/icba_cibs_stage1/phase1/query_roles/truth_access_log.csv"),
    "evaluation_accessed": False,
    "future_confirm_accessed": False,
})
print(json.dumps(summary, indent=2, sort_keys=True))
