#!/usr/bin/env python3
"""Frozen Graph-ANNS labeled-sentinel/source-Oracle ECSE replay."""
from __future__ import annotations

import argparse, csv, gzip, json, math
from collections import defaultdict
from pathlib import Path

GRID=(10,16,24,32,48,64,96,128,192,256,384,512)
TAU=0.9
WORKLOADS=(1_000,10_000,100_000,1_000_000,10_000_000)

def load_graph(path):
    curves=defaultdict(dict); first=None
    with gzip.open(path,"rt",newline="") as h:
        for r in csv.DictReader(h):
            first=first or r; q=int(r["query_id"]); b=int(r.get("ef_search") or r["budget"])
            curves[q][b]=(float(r["recall_at_10"]),int(r["exact_ndc"]))
    stable={}
    for q,c in curves.items(): stable[q]=next((b for i,b in enumerate(GRID) if all(c[x][0]>=TAU for x in GRID[i:])),None)
    return {"path":str(path),"dataset":first["dataset"],"implementation":path.parent.name,
            "history":first.get("insertion_order") or first["history"],
            "seed":str(first.get("graph_seed") or first["seed"]),"hash":first["graph_hash"],
            "curves":curves,"stable":stable}

def distance(a,b,ids): return sum(a[q]!=b[q] for q in ids)

def evaluate(target,candidates,eval_ids,endpoint):
    observed=under=recall=ndc=oracle_ndc=fixed_ndc=censored=0.0; n=len(eval_ids); per=[]
    for q in eval_ids:
        truth=target["stable"][q]
        vals=[x["stable"][q] for x in candidates]
        chosen=GRID[-1] if any(x is None for x in vals) else max(vals)
        if truth is None:
            censored+=1; under+=1
        else:
            observed+=1; under += chosen<truth
            oracle_ndc += target["curves"][q][truth][1]
        recall += target["curves"][q][chosen][0]
        chosen_ndc=target["curves"][q][chosen][1]; endpoint_ndc=target["curves"][q][endpoint][1]
        ndc += chosen_ndc; fixed_ndc += endpoint_ndc
        per.append((endpoint_ndc-chosen_ndc, chosen_ndc, bool(truth is None or chosen<truth)))
    ordered=sorted(per,key=lambda x:x[0],reverse=True); trimmed=ordered[max(1,math.ceil(0.01*n)):]
    p95=sorted(x[1] for x in per)[math.ceil(0.95*n)-1]
    return {"queries":n,"observed_queries":int(observed),"right_censored_queries":int(censored),
            "under_rate_conservative":under/n,"under_rate_observed":(under-censored)/observed if observed else math.nan,
            "mean_recall":recall/n,"mean_ndc":ndc/n,"oracle_mean_ndc_observed":oracle_ndc/observed if observed else math.nan,
            "p95_ndc":p95,"fixed_mean_ndc":fixed_ndc/n,"ndc_saving_vs_fixed":1-ndc/fixed_ndc if fixed_ndc else math.nan,
            "top1pct_deleted_ndc_saving":sum(x[0] for x in trimmed)/sum(x[0]+x[1] for x in trimmed),
            "top1pct_deleted_under_rate":sum(x[2] for x in trimmed)/len(trimmed)}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,required=True); p.add_argument("--split",type=Path,required=True); p.add_argument("--endpoint",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args()
    split=json.loads(a.split.read_text()); endpoints={}
    for r in csv.DictReader(a.endpoint.open()): endpoints[(r["implementation"],r["dataset"],r["history"],r["seed"])]=int(r["certified_safe_budget"]) if r["certified_safe_budget"] else 512
    graphs=[load_graph(x) for x in sorted(a.root.glob("*/*.csv.gz"))]
    rows=[]; sets=[]
    for target in graphs:
        sent=split["datasets"][target["dataset"]]["sentinel_query_ids"]; ev=split["datasets"][target["dataset"]]["evaluation_query_ids"]
        library=[x for x in graphs if x["dataset"]==target["dataset"] and x["implementation"]==target["implementation"]]
        sentinel_search_ndc=sum(target["curves"][q][b][1] for q in sent for b in GRID)
        for lane,pool in (("CLOSED_WORLD_DESIGN_REPLAY",library),("OPEN_WORLD_DESIGN_SIMULATION",[x for x in library if x["hash"]!=target["hash"]])):
            distances={x["hash"]:distance(target["stable"],x["stable"],sent) for x in pool}
            best=min(distances.values()); chosen=[x for x in pool if distances[x["hash"]]==best]
            endpoint=endpoints[(target["implementation"],target["dataset"],target["history"],target["seed"])]
            result=evaluate(target,chosen,ev,endpoint)
            result.update({"dataset":target["dataset"],"implementation":target["implementation"],"history":target["history"],"seed":target["seed"],"target_graph_hash":target["hash"],"lane":lane,
                           "information_lane":"LABELED_TARGET_SENTINEL_PLUS_NON_DEPLOYABLE_SOURCE_ORACLE",
                           "endpoint":endpoint,"endpoint_certified":endpoints[(target["implementation"],target["dataset"],target["history"],target["seed"])]!=512 or target["dataset"]!="glove100_100k",
                           "sentinel_k":len(sent),"sentinel_min_distance":best,"ambiguity_size":len(chosen),"target_in_set":any(x["hash"]==target["hash"] for x in chosen),
                           "sentinel_search_ndc":sentinel_search_ndc,"truth_acquisition_cost":"NOT_ESTIMABLE"})
            for n in WORKLOADS: result[f"total_ndc_N{n}"]=result["mean_ndc"]+sentinel_search_ndc/n
            rows.append(result); sets.append({"target_graph_hash":target["hash"],"lane":lane,"candidate_hashes":";".join(x["hash"] for x in chosen),"min_distance":best,"ambiguity_size":len(chosen)})
    a.output_dir.mkdir(parents=True,exist_ok=True)
    def write(name,data):
        path=a.output_dir/name; tmp=path.with_suffix(path.suffix+".tmp")
        with tmp.open("w",newline="") as h: w=csv.DictWriter(h,fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
        tmp.replace(path)
    write("graph_replay.csv",rows); write("environment_sets.csv",sets)
    write("open_world_leave_build_out.csv",[r for r in rows if r["lane"]=="OPEN_WORLD_DESIGN_SIMULATION"])

if __name__=="__main__": main()
