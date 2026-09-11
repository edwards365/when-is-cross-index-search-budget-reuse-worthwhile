"""P0 deterministic checks over the audit outputs. Run:
LD_LIBRARY_PATH=/home/wlk/miniconda3/lib .venv/bin/python tests/graph_anns_phase2_p0/test_p0.py
"""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "graph_anns_phase2_p0"

checks = []


def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")


rows = list(csv.DictReader(open(OUT / "ladder_aggregate_audit.csv")))
by = {r["metric"]: r for r in rows}

# every audit row has a valid status
check("audit_rows_have_status", all(r["status"] in
      ("REPRODUCED", "STORED_VERIFIED", "ORIGIN_UNLOCATED", "MISMATCH") for r in rows))
# no MISMATCH tolerated in the final P0 audit (mismatches must be resolved or downgraded)
check("no_mismatch_rows", not [r for r in rows if r["status"] == "MISMATCH"])
# portal sums exactly reproduced
for ds in ("sift", "arxiv"):
    check(f"portal_hits_{ds}_reproduced", by[f"portal_hits_{ds}"]["status"] == "REPRODUCED")
    check(f"portal_rescues_{ds}_reproduced", by[f"portal_threshold_rescues_{ds}"]["status"] == "REPRODUCED")
# compression range reproduced from the stored critical_compression table
check("compression_min_reproduced", by["shared_frontier_compression_min"]["status"] == "REPRODUCED")
check("compression_max_reproduced", by["shared_frontier_compression_max"]["status"] == "REPRODUCED")
# auditor aggregates verified
check("auditor_decisions_verified", by["auditor_decisions"]["status"] == "STORED_VERIFIED")
check("auditor_regret_sift_reproduced", by["auditor_regret_sift"]["status"] == "REPRODUCED")
check("auditor_regret_arxiv_reproduced", by["auditor_regret_arxiv"]["status"] == "REPRODUCED")
# known-unlocated rows are recorded with notes (no silent gaps)
unlocated = [r for r in rows if r["status"] == "ORIGIN_UNLOCATED"]
check("unlocated_rows_all_have_notes", all(r["note"] for r in unlocated))
check("unlocated_count_expected", len(unlocated) == 7)

# reference audit
refs = list(csv.DictReader(open(OUT / "reference_anchor_audit.csv")))
missing = [r["reference"] for r in refs if r["status"] != "ANCHORED"]
check("reference_audit_rows", len(refs) == 23)
check("reference_missing_set_known", set(missing) == {
    "Bae et al. 2026 (QBAT)", "Elliott & Clark 2024", "Garivier & Kaufmann 2016",
    "Prokhorenkova & Shekhovtsov 2020", "Yu 1997 (Le Cam Festschrift)",
    "Zhang & Miller 2026"})

# decision manifest present
man = json.loads((OUT / "decision_manifest.json").read_text())
check("manifest_label", man["final_label"] == "P0_TAKEOVER_HARDENING_PASS_WITH_PROVENANCE_GAPS")

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
