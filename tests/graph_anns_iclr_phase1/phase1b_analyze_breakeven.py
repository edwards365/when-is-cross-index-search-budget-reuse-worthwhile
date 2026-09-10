#!/usr/bin/env python3
"""Seal measured Phase-I profiling costs and conservative break-even results."""
from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

ROOT = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
OUT = ROOT / "results/graph_anns_iclr_phase1"
NS = (59, 121, 129, 256, 750)
DATASETS = ("sift_100k", "arxiv_nomic_100k")


def read_csv(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with Path(path).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def value(rows, implementation, threads, n, component, detail=None):
    found = [r for r in rows if r["implementation"] == implementation and int(r["threads"]) == threads and int(r["n"]) == n and r["component"] == component and (detail is None or r["detail"] == detail)]
    if len(found) != 1:
        raise RuntimeError((implementation, threads, n, component, detail, len(found)))
    return float(found[0]["wall_median_seconds"])


def build_context():
    rows=[]
    for dataset in DATASETS:
        values=[]; sizes=[]
        for path in Path("/home/wlk/data500/graph_anns_e4/raw").glob(f"{dataset}__*/metadata.json"):
            d=json.loads(path.read_text()); values.append(float(d["build_seconds"])); sizes.append(int(d["index_size_bytes"]))
        rows.append({"dataset":dataset,"implementation":"hnswlib","base_vectors":100000,"build_repetitions":len(values),"build_median_seconds":statistics.median(values),"index_median_bytes":int(statistics.median(sizes)),"status":"FROZEN_MEASURED_CONTEXT"})
    faiss=read_csv("/home/wlk/data500/graph_anns_faiss_external_validity/run/build_registry.csv")
    for dataset in DATASETS:
        x=[r for r in faiss if r["dataset"]==dataset]
        rows.append({"dataset":dataset,"implementation":"faiss","base_vectors":30000,"build_repetitions":len(x),"build_median_seconds":statistics.median(float(r["build_seconds"]) for r in x),"index_median_bytes":int(statistics.median(int(r["index_size_bytes"]) for r in x)),"status":"FROZEN_MEASURED_CONTEXT_30K_NOT_100K"})
    for dataset,root in (("sift_100k",Path("/home/wlk/data500/icba_vamana_stage1")),("arxiv_nomic_100k",Path("/home/wlk/data500/icba_vamana_stage1_arxiv"))):
        times=[]; sizes=[]
        for report in sorted((root/"builds").glob("V*/run_report.json")):
            d=json.loads(report.read_text())[0]["results"]["build"]
            times.append(float(d["total_time"])/1e6)
            sizes.append(sum(p.stat().st_size for p in report.parent.glob("index*")))
        rows.append({"dataset":dataset,"implementation":"vamana_style","base_vectors":100000,"build_repetitions":len(times),"build_median_seconds":statistics.median(times),"index_median_bytes":int(statistics.median(sizes)),"status":"FROZEN_MEASURED_CONTEXT; PROFILING_COST_ONLY_REPLAY_INTERFACE_NOT_AVAILABLE"})
    return rows


def hnsw_action_mix(dataset):
    decisions=read_csv(ROOT/"results/graph_anns_e4_hotfix/deployment_decision_corrected.csv")
    x=[r for r in decisions if r["dataset"]==dataset]
    actions=[]; fallbacks=0
    for r in x:
        if r["deployed_action"]:
            actions.append(int(float(r["deployed_action"])))
        else:
            actions.append(200); fallbacks += 1
    return actions, fallbacks/len(x), len(x)


def main():
    decomposition=[]; break_even=[]; cert=[]
    for dataset in DATASETS:
        rows=read_csv(OUT/f"profiling_cost_{dataset}.csv")
        for threads in (1,8):
            for n in NS:
                truth100=value(rows,"hnswlib_vamana_exact_truth",threads,n,"C_truth")
                truth30=value(rows,"faiss_exact_truth",threads,n,"C_truth")
                control=value(rows,"shared_control",threads,n,"C_cert")
                cert.append({"dataset":dataset,"threads":threads,"n":n,"candidate_M":6,"cert_median_seconds":control,"scope":"timing_only_Bonferroni_CP"})
                for implementation,truth,grid,label in (
                    ("hnswlib",truth100,(10,20,40,80,120,200),"100K"),
                    ("faiss",truth30,(16,32,64,128,256,512),"30K_FROZEN_FAISS_BASE"),
                ):
                    family=value(rows,implementation,threads,n,"C_family")
                    load=value(rows,implementation,1,0,"C_serialize_cold_load")
                    total=truth+family+control
                    decomposition.append({"dataset":dataset,"implementation":implementation,"actual_base_scope":label,"threads":threads,"n":n,"truth_seconds":truth,"candidate_family_seconds":family,"cert_and_policy_seconds":control,"cold_load_seconds":load,"profiling_total_resident_seconds":total,"truth_share":truth/total,"family_share":family/total,"control_share":control/total,"repetitions_per_component":5})

                    if implementation=="hnswlib":
                        actions,fallback_rate,target_builds=hnsw_action_mix(dataset)
                        lat={a:value(rows,implementation,threads,n,"C_search",f"ef={a}")/n for a in grid}
                        baseline=lat[max(grid)]
                        online=sum(lat[a] for a in actions)/len(actions)
                        delta=baseline-online
                        search_k=family+control
                        full_k=total
                        if delta <= 1e-15:
                            delta = 0.0
                            search_be = "NO_FINITE_BREAK_EVEN_WORKLOAD"
                            full_be = "NO_FINITE_BREAK_EVEN_WORKLOAD"
                        else:
                            search_be = search_k/delta
                            full_be = full_k/delta
                        status="ESTIMABLE_FROM_FROZEN_CERTIFIED_TARGET_DECISIONS"
                    else:
                        fallback_rate="NOT_ESTIMABLE"; target_builds=0; baseline="NOT_ESTIMABLE"; online="NOT_ESTIMABLE"; delta="NOT_ESTIMABLE"; search_be="NOT_ESTIMABLE"; full_be="NOT_ESTIMABLE"; status="TARGET_CERTIFIED_ACTION_LEDGER_ABSENT"
                    break_even.append({"dataset":dataset,"implementation":implementation,"actual_base_scope":label,"threads":threads,"n":n,"target_builds":target_builds,"fallback_rate":fallback_rate,"baseline_max_action_seconds_per_query":baseline,"p2_seconds_per_query":online,"net_saving_seconds_per_query":delta,"search_only_K0_seconds":family+control,"wall_clock_K0_seconds":total,"search_only_break_even_queries":search_be,"wall_clock_break_even_queries":full_be,"status":status})

        # Vamana cannot be rerun on the cost-only role with the frozen binary interface.
        for n in NS:
            break_even.append({"dataset":dataset,"implementation":"vamana_style","actual_base_scope":"100K","threads":"NOT_ESTIMABLE","n":n,"target_builds":0,"fallback_rate":"NOT_ESTIMABLE","baseline_max_action_seconds_per_query":"NOT_ESTIMABLE","p2_seconds_per_query":"NOT_ESTIMABLE","net_saving_seconds_per_query":"NOT_ESTIMABLE","search_only_K0_seconds":"NOT_ESTIMABLE","wall_clock_K0_seconds":"NOT_ESTIMABLE","search_only_break_even_queries":"NOT_ESTIMABLE","wall_clock_break_even_queries":"NOT_ESTIMABLE","status":"COST_ONLY_QUERY_REPLAY_INTERFACE_NOT_AVAILABLE; FROZEN_BUILD_CONTEXT_REPORTED_SEPARATELY"})

    write_csv(OUT/"profiling_cost_decomposition.csv",decomposition)
    write_csv(OUT/"certification_timing.csv",cert)
    write_csv(OUT/"break_even.csv",break_even)
    write_csv(OUT/"build_serialize_cost.csv",build_context())
    gate=[{"component":"Economics","label":"PROFILING_COST_OPERATOR_DEPENDENT","basis":"Direct cost-only measurements show sub-second to few-second profiling for hnswlib/Faiss at registered n; Faiss is actually 30K and Vamana cost-only replay is not estimable, so a universal 100K claim is not supported.","sealed_roles_accessed":False}]
    write_csv(OUT/"phase1b_gate.csv",gate)

    d59=[r for r in decomposition if r["threads"]==8 and r["n"]==59]
    lines=["# Phase 1B profiling and break-even seal","","Evidence role: `profiling_cost_only`; runtime/resource measurement only. No values in this phase select scientific thresholds or actions.","","## Findings",""]
    for r in d59:
        lines.append(f"- {r['dataset']} / {r['implementation']} ({r['actual_base_scope']}): n=59 resident profiling median {float(r['profiling_total_resident_seconds']):.6f}s (truth {float(r['truth_seconds']):.6f}s, six-action replay {float(r['candidate_family_seconds']):.6f}s, control {float(r['cert_and_policy_seconds']):.6f}s).")
    lines += ["","The registered economic label is **PROFILING_COST_OPERATOR_DEPENDENT**. On the directly measured hnswlib and Faiss cells, certification control is negligible and total profiling is seconds or less at the registered sizes. The old blanket claim that profiling is expensive is not supported at this scale. Faiss must be described as a 30K-base external-validity cell despite its historical dataset label; Vamana direct cost-only replay remains NOT_ESTIMABLE because the frozen binary/config interface couples replay to materialized evaluation query/truth files.","","Break-even is point-estimable only for hnswlib, where a frozen per-target certified action ledger exists. Faiss and Vamana are explicitly NOT_ESTIMABLE rather than assigned optimistic actions.",""]
    (ROOT/"docs/graph_anns_iclr_phase1/phase1b_profiling_report.md").write_text("\n".join(lines))


if __name__=="__main__": main()
