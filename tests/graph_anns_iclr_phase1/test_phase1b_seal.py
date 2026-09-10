#!/usr/bin/env python3
import csv
import json
from pathlib import Path

ROOT=Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
OUT=ROOT/"results/graph_anns_iclr_phase1"

def rows(name):
    return list(csv.DictReader((OUT/name).open()))

manifest=json.loads((OUT/"profiling_cost_only_role_manifest.json").read_text())
assert manifest["role"]=="profiling_cost_only"
assert manifest["sealed_future_vectors_or_truth_accessed"] is False
assert all(x["count"]==750 and x["source_identity_overlap_all_zero"] for x in manifest["datasets"])

for dataset in ("sift_100k","arxiv_nomic_100k"):
    measured=rows(f"profiling_cost_{dataset}.csv")
    assert {int(x["n"]) for x in measured if x["component"]=="C_truth"}=={59,121,129,256,750}
    assert {x["implementation"] for x in measured if x["component"]=="C_truth"}=={"hnswlib_vamana_exact_truth","faiss_exact_truth"}
    assert all(int(x["repetitions"])==5 for x in measured)
    assert len({x["detail"] for x in measured if x["implementation"]=="hnswlib" and x["component"]=="C_search"})==6
    assert len({x["detail"] for x in measured if x["implementation"]=="faiss" and x["component"]=="C_search"})==6

decomp=rows("profiling_cost_decomposition.csv")
assert len(decomp)==40
assert all(x["actual_base_scope"]=="30K_FROZEN_FAISS_BASE" for x in decomp if x["implementation"]=="faiss")
be=rows("break_even.csv")
assert len(be)==50
assert all(x["wall_clock_break_even_queries"]=="NO_FINITE_BREAK_EVEN_WORKLOAD" for x in be if x["dataset"]=="sift_100k" and x["implementation"]=="hnswlib")
assert all(x["wall_clock_break_even_queries"]=="NOT_ESTIMABLE" for x in be if x["implementation"] in {"faiss","vamana_style"})
gate=rows("phase1b_gate.csv")
assert gate[0]["label"]=="PROFILING_COST_OPERATOR_DEPENDENT"
print("PHASE1B_ASSERTIONS_PASSED")
