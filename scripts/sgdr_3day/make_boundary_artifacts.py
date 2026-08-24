#!/usr/bin/env python3
"""Create frozen negative-result Pareto tables and figures without new experiments."""
from __future__ import annotations
import argparse, gzip, json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--d0f",type=Path,default=Path("results/post_e0/d0ef_analysis/addback_curves.csv"));p.add_argument("--stage",type=Path,default=Path("results/sgdr_3day/gate_o_stage"));p.add_argument("--stage-summary",type=Path,default=Path("results/sgdr_3day/gate_o_stage_analysis/run_mode_summary.csv"));p.add_argument("--oracle",type=Path,default=Path("results/sgdr_3day/gate_o_query_oracle/run_summary.csv"));p.add_argument("--output",type=Path,default=Path("results/sgdr_3day/boundary"));a=p.parse_args()
    if a.output.exists():raise FileExistsError(f"refusing overwrite {a.output}")
    a.output.mkdir(parents=True)
    repair=pd.read_csv(a.d0f);repair=repair.groupby(["dataset","budget_fraction"],as_index=False).agg(recall_loss_recovery=("recall_loss_recovery","mean"),retained_primary_ndc_improvement=("retained_primary_ndc_improvement","mean"))
    repair.to_csv(a.output/"repair_pareto.csv",index=False)
    fig,ax=plt.subplots(figsize=(7,5))
    for dataset,g in repair.groupby("dataset"):
        ax.plot(g.recall_loss_recovery,g.retained_primary_ndc_improvement,marker="o",label=dataset)
        for row in g.itertuples():ax.annotate(f"{100*row.budget_fraction:g}%",(row.recall_loss_recovery,row.retained_primary_ndc_improvement),fontsize=7)
    ax.axvline(.8,color="black",ls="--",lw=.8);ax.axhline(.5,color="black",ls="--",lw=.8);ax.set(xlabel="Recall-loss recovery",ylabel="Retained Primary NDC improvement",title="Sparse repair Pareto boundary (seed mean)");ax.legend();fig.tight_layout();fig.savefig(a.output/"repair_pareto.png",dpi=180);plt.close(fig)
    stage=pd.read_csv(a.stage_summary);aggregate=stage.groupby(["dataset","mode"],as_index=False).agg(minimum_fixed_ef_recall_difference=("minimum_fixed_ef_recall_difference","min"),mean_ndc_improvement=("mean_ndc_improvement","mean"),p95_ndc_improvement=("p95_ndc_improvement","mean"));aggregate.to_csv(a.output/"sgdr_stage_tradeoff.csv",index=False)
    fig,ax=plt.subplots(figsize=(8,5))
    for dataset,g in aggregate.groupby("dataset"):
        ax.scatter(g.minimum_fixed_ef_recall_difference,100*g.mean_ndc_improvement,label=dataset)
    ax.axvline(-.001,color="black",ls="--",lw=.8);ax.axhline(2,color="black",ls="--",lw=.8);ax.set(xlabel="Worst fixed-ef Recall difference",ylabel="Mean NDC improvement (%)",title="SGDR Gate-O stage tradeoff");ax.legend();fig.tight_layout();fig.savefig(a.output/"sgdr_stage_tradeoff.png",dpi=180);plt.close(fig)
    oracle=pd.read_csv(a.oracle);safe=oracle.groupby("dataset",as_index=False).r4_safe_fraction.mean();safe["harmed_fraction"]=1-safe.r4_safe_fraction;safe.to_csv(a.output/"safe_harmed.csv",index=False)
    fig,ax=plt.subplots(figsize=(7,4));ax.bar(safe.dataset,safe.r4_safe_fraction,label="R4-safe");ax.bar(safe.dataset,safe.harmed_fraction,bottom=safe.r4_safe_fraction,label="harmed");ax.set_ylim(0,1);ax.set_ylabel("Query-ef fraction");ax.set_title("Complete-policy oracle safe/harmed composition");ax.legend();fig.tight_layout();fig.savefig(a.output/"safe_harmed.png",dpi=180);plt.close(fig)
    all_rows=[]
    matrix=json.loads((a.stage/"matrix_summary.json").read_text())
    for record in matrix["records"]:
        with gzip.open(a.stage/"runs"/record["run_id"]/"diagnostic.csv.gz","rt") as f:df=pd.read_csv(f)
        original=df[df["mode"]=="Original"][["ef_search","query_id","recall","ndc"]].rename(columns={"recall":"original_recall","ndc":"original_ndc"})
        x=df[df["mode"]!="Original"].merge(original,on=["ef_search","query_id"]);x["dataset"]=record["dataset"]
        x["phase_bucket"]=pd.cut(x.first_delta_expansion,bins=[-2,-.5,3.5,7.5,15.5,31.5,float("inf")],labels=["never","0-3","4-7","8-15","16-31","32+"])
        x["recall_difference"]=x.recall-x.original_recall;x["ndc_change"]=(x.ndc-x.original_ndc)/x.original_ndc;all_rows.append(x)
    phase=pd.concat(all_rows).groupby(["dataset","phase_bucket"],observed=True,as_index=False).agg(pairs=("query_id","size"),mean_recall_difference=("recall_difference","mean"),mean_ndc_change=("ndc_change","mean"),mean_delta_expanded=("delta_expanded","mean"));phase.to_csv(a.output/"delta_phase_damage.csv",index=False)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for dataset,g in phase.groupby("dataset"):
        axes[0].plot(g.phase_bucket.astype(str),g.mean_recall_difference,marker="o",label=dataset);axes[1].plot(g.phase_bucket.astype(str),100*g.mean_ndc_change,marker="o",label=dataset)
    axes[0].axhline(0,color="black",lw=.8);axes[1].axhline(0,color="black",lw=.8);axes[0].set(ylabel="Mean Recall difference",title="Damage by first delta expansion");axes[1].set(ylabel="Mean NDC change (%)",title="Cost by first delta expansion");[x.tick_params(axis="x",rotation=30) for x in axes];axes[1].legend();fig.tight_layout();fig.savefig(a.output/"delta_phase_damage.png",dpi=180);plt.close(fig)
    manifest={"status":"BOUNDARY_ARTIFACTS_COMPLETE","source_only_existing_results":True,"new_experiments":False,"validation_dev_accessed":False,"formal_test_members_accessed":False,"files":sorted(x.name for x in a.output.iterdir())};(a.output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
if __name__=="__main__":main()
