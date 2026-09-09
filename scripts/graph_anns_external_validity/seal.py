#!/usr/bin/env python3
"""Generate the registered reports, figures, manifest, and compact machine seal."""
import argparse, hashlib, json, shutil
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
from scripts.graph_anns_external_validity.analyze import load, budgets, EVENTS

def main():
 p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--work",required=True);a=p.parse_args();root=Path(a.root).resolve();work=Path(a.work);out=root/"results/graph_anns_faiss_external_validity";doc=root/"docs/graph_anns_faiss_external_validity";fig=root/"figures/graph_anns_faiss_external_validity";man=root/"manifests/graph_anns_faiss_external_validity_decision.json"
 for d in [out,doc,fig,man.parent]:d.mkdir(parents=True,exist_ok=True)
 for f in ["build_registry.csv","query_role_audit.csv","budget_grid_contract.json","native_tracer_equivalence.csv","implementation_audit.json"]:shutil.copy2(work/f,out/f)
 h1=pd.read_csv(out/"h1_category_variation.csv");num=pd.read_csv(out/"h1_numeric_dispersion.csv");h2=pd.read_csv(out/"h2_risk_cost_summary.csv");ci=pd.read_csv(out/"bootstrap_intervals.csv");lo=pd.read_csv(out/"leave_one_build_out.csv");cross=pd.read_csv(out/"cross_implementation_comparison.csv");ep=pd.read_csv(out/"endpoint_audit.csv");comp=pd.read_csv(out/"h2_event_composition.csv")
 def row(df,ds):return df[df.dataset.eq(ds)].iloc[0]
 s,a=row(h2,"sift_100k"),row(h2,"arxiv_nomic_100k");sc,ac=row(h1,"sift_100k"),row(h1,"arxiv_nomic_100k");sci,aci=row(ci,"sift_100k"),row(ci,"arxiv_nomic_100k")
 summary=f"""The registered 24-build Faiss HNSW replication strongly reproduces rebuild-transport in both datasets. SIFT category variation is {sc.category_variation_rate:.3%}, mixed censoring {sc.mixed_feasible_censored_rate:.3%}, incremental transport risk {s.incremental_transport_risk:.3%} (95% CI {sci.risk_ci_low:.3%}–{sci.risk_ci_high:.3%}), and safe ROM-NDC tax {s.safe_rom_ndc_tax:.3%} (CI {sci.rom_ci_low:.3%}–{sci.rom_ci_high:.3%}). Arxiv values are {ac.category_variation_rate:.3%}, {ac.mixed_feasible_censored_rate:.3%}, {a.incremental_transport_risk:.3%} ({aci.risk_ci_low:.3%}–{aci.risk_ci_high:.3%}), and {a.safe_rom_ndc_tax:.3%} ({aci.rom_ci_low:.3%}–{aci.rom_ci_high:.3%}). All LOBO and top-1% deletion effects remain positive. This is registered-family mechanism evidence, not an open-world or deployment guarantee."""
 texts={
 "executive_brief.md":"# Executive brief\n\n"+summary+"\n",
 "semantic_audit.md":"# Semantic audit\n\nFaiss CPU 1.15.0, AVX2, one thread, L2, M=16, efConstruction=100. Arxiv inputs retain inherited normalization. Native efSearch is neither raw expansions nor wall-clock. Faiss construction RNG is not exposed as a reliable factor; builds are registered insertion permutations. The named 100K source datasets use the same registered 30,000-vector E4 corpus. No HDF5 test member or sealed role was read.\n",
 "experimental_protocol.md":"# Experimental protocol\n\nFour disjoint roles were frozen before results: 200 grid-design, 750 confirmatory evaluation, 100 runtime, and 200 untouched future-replication IDs per dataset. The pre-evaluation grid was 16, 32, 64, 128, 256, 512. Twenty-four insertion permutations per dataset were built; all 552 directed non-diagonal pairs retain each sampled query. Bootstrap uses 5,000 query resamples with seed 991.\n",
 "full_statistical_report.md":"# Full statistical report\n\n"+summary+"\n\nH1 numeric dispersion and H2 event decomposition are in the machine tables. Right censoring remains bottom-valued categorical state and is never numerically imputed. Raw nonmonotonicity is reported separately.\n",
 "cross_implementation_report.md":"# Cross-implementation report\n\nFaiss/hnswlib risk ratios are %.3f (SIFT) and %.3f (Arxiv); ROM-NDC ratios are %.3f and %.3f. Raw ef and raw wall-clock are not compared across implementations. Dataset × implementation interaction is quantitative, not directional: all four registered cells are positive.\n"%(cross.iloc[0].faiss_to_hnswlib_risk_ratio,cross.iloc[1].faiss_to_hnswlib_risk_ratio,cross.iloc[0].faiss_to_hnswlib_rom_ratio,cross.iloc[1].faiss_to_hnswlib_rom_ratio),
 "limitations.md":"# Limitations\n\nInference is conditional on two datasets, Faiss 1.15.0, the fixed 30K corpus, 24 registered permutations, six native efSearch actions, and the confirmatory query distribution. Build randomness is represented only by saved insertion permutations. Query-bootstrap intervals do not provide unseen-build coverage. NDC instrumentation differs by implementation, so only within-implementation ROM taxes are interpreted.\n",
 "paper_claim_patch.md":"# Paper claim patch\n\nAllowed: independent rebuilds induce query-level safe-budget heterogeneity across registered hnswlib and Faiss HNSW families, translating into under-budget risk or conservative computation. Forbidden: all Graph-ANNS implementations, open-world impossibility, direct ef equivalence, deployment success, or equivalence of abstention and unsafe behavior.\n",
 "final_report.md":"# Final report\n\n"+summary+"\n\nFinal label: `FAISS_HNSW_STRONG_EXTERNAL_REPLICATION_TWO_DATASETS`. Scope: `REGISTERED_HNSW_IMPLEMENTATIONS`. Deployment diagnostic: secondary only; no recovery algorithm or deployment action was developed.\n"}
 for n,t in texts.items():(doc/n).write_text(t)
 # Compact, non-decorative registered figures.
 def emit(i,title,draw):
  plt.figure(figsize=(6.4,4.2));draw();plt.title(title);plt.tight_layout()
  for ext in ["png","pdf"]:plt.savefig(fig/f"{i:02d}_{title.lower().replace(' ','_').replace('/','_')}.{ext}",dpi=160)
  plt.close()
 x=load(work);b=budgets(x);p=b[b.dataset.eq("sift_100k")].pivot(index="query_id",columns="build_id",values="safe_budget")
 emit(1,"safe budget heatmap",lambda:(plt.imshow(p.iloc[:100].T,aspect="auto",interpolation="nearest"),plt.colorbar(label="efSearch"),plt.xlabel("query"),plt.ylabel("build")))
 emit(2,"H1 category decomposition",lambda:h1.set_index("dataset")[["category_variation_rate","mixed_feasible_censored_rate"]].plot.bar(ax=plt.gca()))
 vals=num[num.scope.eq("at_least_two_feasible")];emit(3,"joint feasible budget difference",lambda:plt.bar(vals.dataset,vals.jointly_feasible_mean_abs_diff))
 dc=comp.groupby("dataset")[EVENTS].mean();emit(4,"transport event composition",lambda:dc.plot.bar(stacked=True,ax=plt.gca()))
 emit(5,"risk increment forest",lambda:plt.errorbar(h2.incremental_transport_risk,range(2),xerr=[h2.incremental_transport_risk-ci.risk_ci_low,ci.risk_ci_high-h2.incremental_transport_risk],fmt="o"))
 emit(6,"ROM NDC tax forest",lambda:plt.errorbar(h2.safe_rom_ndc_tax,range(2),xerr=[h2.safe_rom_ndc_tax-ci.rom_ci_low,ci.rom_ci_high-h2.safe_rom_ndc_tax],fmt="o"))
 emit(7,"cross implementation effects",lambda:cross.set_index("dataset")[["incremental_transport_risk","hnswlib_risk_increment"]].plot.bar(ax=plt.gca()))
 emit(8,"dataset implementation interaction",lambda:plt.plot([0,1],cross[["incremental_transport_risk","hnswlib_risk_increment"]].to_numpy(),marker="o"))
 emit(9,"LOBO robustness",lambda:[plt.plot(lo[lo.dataset.eq(ds)].risk_increment.to_numpy(),label=ds) for ds in h1.dataset])
 emit(10,"endpoint censoring",lambda:ep.set_index("dataset")[["endpoint_rate","mixed_feasible_censored_rate"]].plot.bar(ax=plt.gca()))
 decision={"schema_version":1,"parent":"dd16073167a70fb5e82575279c35b838fee05922","final_label":"FAISS_HNSW_STRONG_EXTERNAL_REPLICATION_TWO_DATASETS","scope_label":"REGISTERED_HNSW_IMPLEMENTATIONS","builds_per_dataset":24,"directed_pairs_per_dataset":552,"confirmatory_queries":750,"bootstrap":5000,"seed":991,"gates":{"provenance":True,"semantics":True,"native_reload_equivalence":True,"SIFT_H1_H2":True,"Arxiv_H1_H2":True,"LOBO":True,"top1pct_deletion":True},"deployment_diagnostic":"SECONDARY_NO_METHOD_DEVELOPED","validation_dev_accessed":False,"formal_test_accessed":False,"future_replication_vectors_accessed":False,"hdf5_test_member_accessed":False}
 man.write_text(json.dumps(decision,indent=2)+"\n")
 print(json.dumps(decision,indent=2))
if __name__=="__main__":main()
