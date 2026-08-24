#!/usr/bin/env python3
"""Apply the outcome-blind frozen Gate-O stage aggregation to exact diagnostics."""

from __future__ import annotations
import argparse, csv, gzip, json, math
from collections import defaultdict
from pathlib import Path

def pct(values:list[float],p:float)->float:
    x=sorted(values);z=(len(x)-1)*p;a=math.floor(z);b=math.ceil(z)
    return x[a] if a==b else x[a]*(b-z)+x[b]*(z-a)

def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--matrix",type=Path,default=Path("results/sgdr_3day/gate_o_stage"));p.add_argument("--query-oracle",type=Path,default=Path("results/sgdr_3day/gate_o_query_oracle/summary.json"));p.add_argument("--output",type=Path,default=Path("results/sgdr_3day/gate_o_stage_analysis"));a=p.parse_args()
    matrix=json.loads((a.matrix/"matrix_summary.json").read_text());oracle=json.loads(a.query_oracle.read_text())
    if matrix["status"]!="SGDR_GATE_O_STAGE_MATRIX_COMPLETE" or not matrix["all_native_original_checks_exact"] or not matrix["all_temporary_indexes_deleted"] or matrix["validation_dev_accessed"] or matrix["formal_test_members_accessed"]:raise ValueError("stage matrix incomplete or unsafe")
    if not oracle["query_oracle_component_passes"]:raise ValueError("query oracle prerequisite failed")
    if a.output.exists():raise FileExistsError(f"refusing overwrite {a.output}")
    a.output.mkdir(parents=True);rows=[];run_pass={};dataset_mode:dict[tuple[str,str],list[bool]]=defaultdict(list)
    for record in matrix["records"]:
        modes:dict[str,dict[tuple[int,int],tuple[float,float]]]=defaultdict(dict)
        with gzip.open(a.matrix/"runs"/record["run_id"]/"diagnostic.csv.gz","rt",newline="") as f:
            for row in csv.DictReader(f):modes[row["mode"]][(int(row["ef_search"]),int(row["query_id"]))]=(float(row["recall"]),float(row["ndc"]))
        original=modes["Original"]
        if len(original)!=3000:raise ValueError("Original row count mismatch")
        for mode,candidate in modes.items():
            if mode=="Original":continue
            per_ef=[]
            for ef in (10,20,40,80,120,200):
                keys=[k for k in original if k[0]==ef]
                rd=sum(candidate[k][0]-original[k][0] for k in keys)/len(keys)
                ndc=1-sum(candidate[k][1] for k in keys)/sum(original[k][1] for k in keys)
                per_ef.append({"ef":ef,"recall_difference":rd,"mean_ndc_improvement":ndc})
            keys=list(original);oc=[original[k][1] for k in keys];cc=[candidate[k][1] for k in keys]
            savings=[oc[i]-cc[i] for i in range(len(keys))];remove=set(sorted(range(len(keys)),key=lambda i:savings[i],reverse=True)[:math.ceil(.01*len(keys))]);keep=[i for i in range(len(keys)) if i not in remove]
            mean_gain=1-sum(cc)/sum(oc);trim_gain=1-sum(cc[i] for i in keep)/sum(oc[i] for i in keep);p95_gain=1-pct(cc,.95)/pct(oc,.95);min_recall=min(x["recall_difference"] for x in per_ef)
            stage_mode=mode.startswith("Scale-") or mode.startswith("Depth-")
            passed=stage_mode and min_recall>=-0.001 and ((mean_gain>=.02 and trim_gain>=.02) or p95_gain>=.05)
            row={"run_id":record["run_id"],"dataset":record["dataset"],"build_seed":record["build_seed"],"mode":mode,"minimum_fixed_ef_recall_difference":min_recall,"mean_ndc_improvement":mean_gain,"trim_top_1_percent_mean_ndc_improvement":trim_gain,"p95_ndc_improvement":p95_gain,"passes_run_gate":passed,"per_ef":per_ef}
            rows.append(row);run_pass[(record["run_id"],mode)]=passed;dataset_mode[(record["dataset"],mode)].append(passed)
    eligible=sorted({row["mode"] for row in rows if row["mode"].startswith("Scale-") or row["mode"].startswith("Depth-")})
    mode_decisions={}
    for mode in eligible:
        datasets={}
        for dataset in ("sift_10k","glove100_10k","arxiv_nomic_10k"):
            count=sum(dataset_mode[(dataset,mode)]);datasets[dataset]={"passing_seeds":count,"passes_two_of_three":count>=2}
        count=sum(x["passes_two_of_three"] for x in datasets.values());mode_decisions[mode]={"passing_datasets":count,"passes_two_datasets":count>=2,"datasets":datasets}
    passing_modes=[m for m,x in mode_decisions.items() if x["passes_two_datasets"]];gate_pass=bool(passing_modes)
    flat_path=a.output/"run_mode_summary.csv"
    fields=["run_id","dataset","build_seed","mode","minimum_fixed_ef_recall_difference","mean_ndc_improvement","trim_top_1_percent_mean_ndc_improvement","p95_ndc_improvement","passes_run_gate"]
    with flat_path.open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
    result={"status":"AUTHORIZE_MINIMAL_SGDR_IMPLEMENTATION" if gate_pass else "FAIL_ORACLE_UPPER_BOUND","gate_o_passes":gate_pass,"passing_common_modes":passing_modes,"mode_decisions":mode_decisions,"rule":"one common fixed scale/depth mode must pass at least two datasets, each at least two of three seeds","thresholds":{"minimum_fixed_ef_recall_difference":-0.001,"mean_ndc_improvement":.02,"p95_ndc_improvement_alternative":.05,"top_1_percent_trim_required_for_mean_route":True},"union_all_excluded_from_gate_because_not_stage_gated":True,"exact_counterfactual":True,"matrix_rows":matrix["rows"],"new_ef_points":False,"validation_dev_accessed":False,"formal_test_members_accessed":False,"rows":rows}
    (a.output/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({k:v for k,v in result.items() if k!="rows"},sort_keys=True))
if __name__=="__main__":main()
