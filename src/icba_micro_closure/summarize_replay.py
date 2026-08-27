#!/usr/bin/env python3
import csv, math
from pathlib import Path

ROOT=Path("results/icba_micro_closure")
rows=list(csv.DictReader((ROOT/"graph_replay.csv").open()))
cost=[]
for r in rows:
    saving=float(r["fixed_mean_ndc"])-float(r["mean_ndc"])
    sentinel=float(r["sentinel_search_ndc"])
    cost.append({"dataset":r["dataset"],"implementation":r["implementation"],"history":r["history"],"seed":r["seed"],"lane":r["lane"],
                 "break_even_N_search_only":sentinel/saving if saving>0 else "INF",
                 "truth_acquisition_cost":"NOT_ESTIMABLE","latency":"LATENCY_NOT_ESTIMABLE_FROM_TRACE",
                 **{f"net_ndc_saving_N{n}":1-float(r[f"total_ndc_N{n}"])/float(r["fixed_mean_ndc"]) for n in (1000,10000,100000,1000000,10000000)}})
with (ROOT/"cost_break_even.csv.tmp").open("w",newline="") as h:
    w=csv.DictWriter(h,fieldnames=list(cost[0]));w.writeheader();w.writerows(cost)
(ROOT/"cost_break_even.csv.tmp").replace(ROOT/"cost_break_even.csv")
gates=[
 {"gate":"G0_ENDPOINT","status":"PASS_WITH_DATASET_BOUNDARY","evidence":"hnswlib safe on SIFT and Arxiv 18/18 graphs; GloVe 0/9"},
 {"gate":"G1_LOWER_BOUND","status":"PASS_RESTRICTED_ALIGNED_RESPONSE_CLASS","evidence":"positive overlap-separation bound; finite edge tests pass"},
 {"gate":"G2_CONSTRUCTIVE_UPPER","status":"PASS_FINITE_CLOSED_WORLD_CLASS","evidence":"K=2 singular-sentinel class reaches Oracle at k=8"},
 {"gate":"G3_GRAPH_MECHANISM","status":"CLOSED_WORLD_PASS_OPEN_WORLD_FAIL","evidence":"closed exact identification; all open-world implementation/dataset cells exceed delta_q=0.05"},
 {"gate":"G4_DEPLOYMENT","status":"FAIL","evidence":"only labeled-sentinel plus source-Oracle lane estimable; open-world unsafe"},
]
with (ROOT/"unified_gate_table.csv.tmp").open("w",newline="") as h:
    w=csv.DictWriter(h,fieldnames=list(gates[0]));w.writeheader();w.writerows(gates)
(ROOT/"unified_gate_table.csv.tmp").replace(ROOT/"unified_gate_table.csv")
