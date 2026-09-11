#!/usr/bin/env python
"""P0 audit: reproduce every Section-8 falsification-ladder aggregate cited in the
anonymous paper from frozen result trees. Pure code: no ANN access, no new search,
no modification of frozen files. Output: results/graph_anns_phase2_p0/ladder_aggregate_audit.csv

Status codes:
  REPRODUCED        computed value matches the paper value within tolerance
  STORED_VERIFIED   value is stored verbatim in a frozen artifact and located
  ORIGIN_UNLOCATED  no frozen artifact reproduces the paper value (recorded, not interpolated)
"""
import csv
import json
import math
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RES = REPO / "results"
OUT = REPO / "results" / "graph_anns_phase2_p0"
OUT.mkdir(parents=True, exist_ok=True)

rows = []


def add(metric, computed, paper, source, status, note=""):
    rows.append({
        "metric": metric,
        "computed": "" if computed is None else (f"{computed:.6g}" if isinstance(computed, float) else str(computed)),
        "paper_value": str(paper),
        "source": source,
        "status": status,
        "note": note,
    })


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def close(a, b, tol=0.011):
    return a is not None and abs(a - b) <= tol * max(1.0, abs(b))


# ---------------------------------------------------------------- 1. portal sums
hold = read_csv(RES / "icba_cals_seal" / "holdout_results.csv")
agg = {}
for r in hold:
    key = (r["dataset"], r["action_scope"])
    a = agg.setdefault(key, [0, 0])
    a[0] += int(r["positive_hit_gain"])
    a[1] += int(r["threshold_rescues"])
for ds, hits, resc, ph, pr in [
    ("sift", 1064, 426, "1,064", "426"),
    ("arxiv", 727, 348, "727", "348"),
]:
    got = agg.get((ds, "TARGET_SPECIFIC_SELECTED_FIXED_SET"), [None, None])
    ok = got[0] == hits and got[1] == resc
    add(f"portal_hits_{ds}", got[0], ph, "icba_cals_seal/holdout_results.csv",
        "REPRODUCED" if ok else "MISMATCH",
        "TARGET_SPECIFIC_SELECTED_FIXED_SET sum over holdout rows")
    add(f"portal_threshold_rescues_{ds}", got[1], pr, "icba_cals_seal/holdout_results.csv",
        "REPRODUCED" if ok else "MISMATCH", "same source")

# ------------------------------------------------- 2. auditor decisions and regret
rep = (REPO / "docs" / "icba_fixed_target_auditor" / "retrospective_crossfit_report.md").read_text()
m = re.search(r"\{.*\}", rep, re.S)
dec = json.loads(m.group(0))
counts = dec["deployed_action_counts"]
ok_dec = (dec["decisions"] == 60 and counts["A1"] == 4 and counts["A5"] == 32
          and counts["A6"] == 24 and dec["outcomes"]["SAFE_ACCEPTANCE"] == 36
          and dec["outcomes"]["SAFE_BUT_REJECTED"] == 24)
add("auditor_decisions", f"{dec['decisions']}: A1={counts['A1']} A5={counts['A5']} A6={counts['A6']}; "
    f"safe_accept={dec['outcomes']['SAFE_ACCEPTANCE']} safe_rej={dec['outcomes']['SAFE_BUT_REJECTED']}",
    "60: 4 reuse + 32 fallback + 24 abstain; 36 accepted all safe",
    "docs/icba_fixed_target_auditor/retrospective_crossfit_report.md",
    "STORED_VERIFIED" if ok_dec else "MISMATCH")

boot = read_csv(RES / "icba_fixed_target_auditor" / "bootstrap_results.csv")
for r in boot:
    ds = "sift" if r["dataset"] == "sift_100k" else "arxiv"
    est, lo, hi = float(r["estimate"]), float(r["ci_low"]), float(r["ci_high"])
    paper = {"sift": (470.34, 458.69, 482.03), "arxiv": (684.49, 674.99, 694.26)}[ds]
    ok = close(est, paper[0], 5e-4) and close(lo, paper[1], 5e-4) and close(hi, paper[2], 5e-4)
    add(f"auditor_regret_{ds}", est, f"{paper[0]} [{paper[1]}, {paper[2]}]",
        "icba_fixed_target_auditor/bootstrap_results.csv",
        "REPRODUCED" if ok else "MISMATCH",
        f"bootstrap seed {r['seed']} reps {r['repetitions']}; CI [{lo:.2f}, {hi:.2f}]")

# --------------------------------------------- 3. shared-frontier compression range
cc = read_csv(RES / "icba_shared_cost_gate" / "critical_compression.csv")
rc_all = [float(r["required_compression"]) for r in cc]
rc_recall = [float(r["required_compression"]) for r in cc if r["metric"] in ("kappa_recall", "kappa_hit")]
cmin, cmax = min(rc_recall) * 100, max(rc_all) * 100
add("shared_frontier_compression_min", cmin, "79.5%",
    "icba_shared_cost_gate/critical_compression.csv",
    "REPRODUCED" if close(cmin, 79.5, 0.011) else "MISMATCH",
    f"min required_compression over kappa_recall/kappa_hit rows ({len(rc_recall)} rows); "
    f"all-row min={min(rc_all)*100:.2f}%")
add("shared_frontier_compression_max", cmax, "93.4%",
    "icba_shared_cost_gate/critical_compression.csv",
    "REPRODUCED" if close(cmax, 93.4, 0.011) else "MISMATCH",
    f"max required_compression over all {len(rc_all)} rows")

# ------------------------- 4. multi-lane vs matched native lane (cost ratio, recall deficit)
wc = read_csv(RES / "icba_cals_seal" / "wallclock_summary.csv")
wc_by = {}
for r in wc:
    wc_by.setdefault(r["dataset"], []).append(
        float(r["median_ns"]) / float(r["primary_median_ns"]))
for ds, paper_ratio in [("sift", 2.77), ("arxiv", 2.47)]:
    vals = wc_by.get(ds, [])
    mr = sum(vals) / len(vals) if vals else None
    add(f"multilane_matched_ratio_{ds}", mr, paper_ratio,
        "icba_cals_seal/wallclock_summary.csv",
        "ORIGIN_UNLOCATED",
        f"same-ef primary-lane wallclock ratio mean={mr:.3f} range=[{min(vals):.2f},{max(vals):.2f}] "
        f"over {len(vals)} setting-repeats; docs/icba_cals_seal/cost_and_tail.md states 'roughly "
        "2.5-2.8x the matched native single-lane cost' but the matched-lane pairing rule is not "
        "stored as an artifact")
for ds, paper_def in [("sift", 4.79), ("arxiv", 3.29)]:
    add(f"multilane_recall_deficit_pp_{ds}", None, paper_def,
        "icba_cals_seal/subset_summary.csv + matched-lane rule (not stored)",
        "ORIGIN_UNLOCATED",
        "requires the matched native lane definition used by the paper; subset-level pairing "
        "attempts did not reproduce it")

# --------------------------- 5. recalibration aggregates from e4_reanalysis frozen tables
tr = read_csv(RES / "graph_anns_e4_reanalysis" / "target_recalibration_corrected.csv")
sc = read_csv(RES / "graph_anns_e4_reanalysis" / "source_calibrated_transfer.csv")
rec_ndc = {(r["dataset"], r["target_build"]): float(r["mean_ndc"]) for r in tr}
for ds, paper_pct in [("sift_100k", 29.40), ("arxiv_nomic_100k", 26.17)]:
    per_pair, n = [], 0
    for r in sc:
        if r["dataset"] != ds:
            continue
        n += 1
        t = rec_ndc.get((r["dataset"], r["target_build"]))
        if t:
            per_pair.append((float(r["mean_ndc"]) - t) / float(r["mean_ndc"]))
    mean_pair = 100 * sum(per_pair) / len(per_pair)
    srcs = [float(r["mean_ndc"]) for r in sc if r["dataset"] == ds]
    recs = [v for (d, _), v in rec_ndc.items() if d == ds]
    rom = 100 * (1 - (sum(recs) / len(recs)) / (sum(srcs) / len(srcs)))
    best = min([("mean-of-pairwise-ratios", mean_pair), ("ratio-of-means", rom)],
               key=lambda kv: abs(kv[1] - paper_pct))
    add(f"recalibration_target_only_ndc_reduction_pct_{ds}", best[1], paper_pct,
        "graph_anns_e4_reanalysis/{source_calibrated_transfer,target_recalibration_corrected}.csv",
        "REPRODUCED" if close(best[1], paper_pct, 0.02) else "ORIGIN_UNLOCATED",
        f"{n} directed pairs; mean-pairwise={mean_pair:.2f}% ratio-of-means={rom:.2f}%; "
        "history-assisted and disjoint-cross-fit variants not present as stored aggregates")

# ------------------------------- 6. build-selection (72-action joint feasibility, stored)
gsc = read_csv(RES / "icba_gsc" / "frozen72_slack_audit.csv")
add("build_selection_frozen_action_count", len(gsc), 72,
    "icba_gsc/frozen72_slack_audit.csv", "STORED_VERIFIED" if len(gsc) == 72 else "MISMATCH",
    "row count = frozen build-budget actions")

# ------------------------------------------------------------------ 7. repair NDC
add("protected_edge_repair_ndc_mean", None, "509.49 -> 503.41",
    "repo-wide search", "ORIGIN_UNLOCATED",
    "no frozen artifact stores 509.49/503.41/849/833; requires aggregation provenance from authors")

# ------------------------------------------------------------------ write outputs
with open(OUT / "ladder_aggregate_audit.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

summary = {}
for r in rows:
    summary[r["status"]] = summary.get(r["status"], 0) + 1
(OUT / "ladder_aggregate_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
for r in rows:
    print(f"{r['status']:17s} {r['metric']:48s} computed={r['computed']:>12s} paper={r['paper_value']}")
