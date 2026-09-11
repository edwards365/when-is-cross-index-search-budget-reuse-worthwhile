"""P1 deterministic checks. Run:
LD_LIBRARY_PATH=/home/wlk/miniconda3/lib .venv/bin/python tests/graph_anns_phase2_p1/test_p1.py
"""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "graph_anns_phase2_p1"
checks = []
def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")

f = list(csv.DictReader(open(OUT / "vamana_overlap_forensics.csv")))
check("two_datasets", len(f) == 2)
for r in f:
    ds = r["dataset"]
    check(f"{ds}_raw_overlap_zero", int(r["query_base_raw_overlap"]) == 0)
    check(f"{ds}_normalized_overlap_zero", int(r["query_base_normalized_overlap"]) == 0)
    check(f"{ds}_role_id_overlap_zero", int(r["historical_role_id_overlap"]) == 0)
    check(f"{ds}_internal_raw_dup_zero", int(r["evaluation_internal_raw_duplicates"]) == 0)
    check(f"{ds}_internal_norm_dup_zero", int(r["evaluation_internal_normalized_duplicates"]) == 0)
    check(f"{ds}_crossstage_zero", int(r["crossstage_query_e4base_raw_overlap"]) == 0
          and int(r["crossstage_query_e4base_normalized_overlap"]) == 0)
    check(f"{ds}_gate_pass", r["gate_a"] == "PASS")

b = list(csv.DictReader(open(OUT / "vamana_base_identity.csv")))
check("base_rows_24", len(b) == 24)
check("all_builds_same_base_multiset", all(r["same_content_multiset_as_V01"] == "True" for r in b))
check("vamana_base_differs_from_e4_base", all(r["same_content_multiset_as_e4_input"] == "False" for r in b))

c = list(csv.DictReader(open(OUT / "estimand_crosswalk.csv")))
check("crosswalk_rows_10", len(c) == 10)
paper_rows = [r for r in c if r["paper_adoption"].startswith("YES")]
check("six_adopted_rows", len(paper_rows) == 6)
# adopted hnswlib numbers match the repair registry exactly
hr = [r for r in paper_rows if "Repaired h=10" in r["estimand"]]
check("hnswlib_adopted_values", {(r["dataset"], r["incremental_risk"]) for r in hr} ==
      {("sift_100k", "0.215478"), ("arxiv_nomic_100k", "0.171737")})

dp = (REPO / "docs" / "graph_anns_phase2_p1" / "definitions_patch.md").read_text()
check("definitions_cover_distcomp", "DistComp" in dp and "ROM-NDC" in dp)
check("definitions_cover_59_derivation", "ceil(log(alpha_l)/log(1-delta))" in dp)

man = json.loads((OUT / "decision_manifest.json").read_text())
check("manifest_label", man["final_label"] == "P1_SEMANTICS_HYGIENE_SEALED_VAMANA_OVERLAP_PASS")

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
