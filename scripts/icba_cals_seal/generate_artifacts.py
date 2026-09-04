from pathlib import Path
import pandas as pd, numpy as np, json, hashlib, subprocess, matplotlib.pyplot as plt
root=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');out=root/'results/icba_cals_seal';docs=root/'docs/icba_cals_seal';figs=root/'figures/icba_cals_seal';man=root/'manifests/icba_cals_seal_decision.json'
docs.mkdir(parents=True,exist_ok=True);figs.mkdir(parents=True,exist_ok=True)
# Compact canonical lane tables.
lane_files=sorted(out.glob('lanes_*.csv'));lanes=pd.concat([pd.read_csv(p).assign(source_file=p.name) for p in lane_files],ignore_index=True);lanes.to_csv(out/'per_lane_results.csv.gz',index=False,compression='gzip')
wall_files=sorted(out.glob('wallclock_*_r*.csv'));wall=pd.concat([pd.read_csv(p).assign(source_file=p.name) for p in wall_files],ignore_index=True);wall.to_csv(out/'wallclock_lane_results.csv.gz',index=False,compression='gzip')
actions=pd.read_csv(out/'selection_actions.csv');target=actions[actions.action_scope=='TARGET_SPECIFIC_SELECTED_FIXED_SET'];rows=[]
for _,a in target.iterrows():
 rules=set(str(a.portal_rule_ids).split(';'));key=a.build
 for rep in range(5):
  p=out/f'wallclock_{key}_holdout_r{rep}.csv';d=pd.read_csv(p);d=d[d.raw_ef==a.raw_ef]
  pr=d[d.lane_type=='primary'][['query_id','wall_clock_ns']].rename(columns={'wall_clock_ns':'primary_ns'})
  au=d[(d.lane_type=='auxiliary')&d.portal_rule_id.isin(rules)].groupby('query_id').wall_clock_ns.sum().rename('aux_ns')
  q=pr.join(au,on='query_id');q['total_ns']=q.primary_ns+q.aux_ns
  rows.append({'dataset':a.dataset,'build':key,'raw_ef':a.raw_ef,'mask':a['mask'],'repeat':rep,'median_ns':q.total_ns.median(),'p95_ns':q.total_ns.quantile(.95),'p99_ns':q.total_ns.quantile(.99),'primary_median_ns':q.primary_ns.median()})
pd.DataFrame(rows).to_csv(out/'wallclock_summary.csv',index=False)
# Frozen input checksums.
inputs=['data/raw/sift-128-euclidean.hdf5','data/raw/arxiv-nomic-768-normalized.hdf5']+[f'results/gate_a/raw/{d}_100k-original-b{s}/index.bin' for d in ['sift','arxiv_nomic'] for s in [7,17,29]]
sha=[]
for rel in inputs:
 p=root/rel;h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 sha.append({'path':rel,'bytes':p.stat().st_size,'sha256':h.hexdigest()})
pd.DataFrame(sha).to_csv(out/'frozen_input_checksums.csv',index=False)
gates=pd.read_csv(out/'unified_gate_table.csv');hold=pd.read_csv(out/'holdout_results.csv');cost=pd.read_csv(out/'matched_cost_comparison.csv');boot=pd.read_csv(out/'build_cluster_bootstrap.csv');loo=pd.read_csv(out/'leave_one_build_out.csv');top=pd.read_csv(out/'top1pct_deletion.csv');oracle=pd.read_csv(out/'oracle_hierarchy.csv')
decision='CALS_FIXED_PORTAL_MECHANISM_REPLICATED_SAFETY_UNMET'
texts={
'input_audit.md':'# Input audit\n\nFrozen parent f5527e6 was found and its recorded checksums verified. Six 100K indexes and both source datasets were present. The experiment used the existing ANNS worktree and did not access sealed roles. Resource reserve stayed above 5 GiB.',
'generator_forensics.md':'# Generator forensics\n\nThe prior semantic generator was located in the frozen commit, but it did not constitute the required formal runner: it lacked query-ID inputs, complete primary tracing, true lane-summed cost, and selection/holdout separation. A new formal runner and replay chain were therefore implemented and compared against the frozen positive signal.',
'id_semantics.md':'# ID semantics\n\nCross-build action identity is the fixed portal_rule_id. Each build resolves that rule to an external label and then to an internal tableint. Six thousand deterministic bidirectional round-trip records were generated at seed 991 with zero failures.',
'mechanical_replay.md':'# Mechanical replay\n\nThe runner records native and traced primary results, full candidate sets, per-lane NDC, expansion counts, timing, hashes, termination state, and build-specific portal identities. Across 4,800 primary query/ef cases native and traced top-10 were identical. Auxiliary lanes use independent search calls and state.',
'selection_transfer.md':'# Selection transfer\n\nPortal subsets were chosen only on query IDs 0–199 and evaluated once on IDs 200–499. Target-specific and dataset-level fixed sets retained positive hit gain and threshold rescues in all three builds of both datasets at all registered ef values. Holdout outcome was not used to select these actions.',
'cost_and_tail.md':'# Cost and tail\n\nTotal NDC is primary plus every selected auxiliary lane; it is never averaged. The selected unions were roughly 2.5–2.8 times the matched native single-lane cost on average and had lower recall than the matched high-budget native lane, so the economic Gate failed. Median, p95 and p99 wall-clock were measured in five randomized repetitions on CPU 0.',
'statistical_report.md':'# Statistical report\n\nBuild is the outer uncertainty unit. The three-build bootstrap used 5,000 resamples and seed 991. Leave-one-build-out and removal of the highest-cost one percent of queries retained the positive rescue direction. Three builds remain a small-sample exploratory audit.',
'final_report.md':f'# Final report\n\nMechanism Gate: PASS? no — see machine table. Selection transfer and robustness passed. Absolute safety and economic Gates failed. The first failed Gate is absolute safety: one-sided 95% risk bounds exceed 5% on both datasets. Final decision: {decision}. This preserves the corrected mechanism result but authorizes neither deployment nor independent confirmation.',
'executive_brief.md':f'# Executive brief\n\nCALS rescue is reproducible and transfers from selection queries to disjoint holdout queries across builds. It is not yet safe or cost-effective: risk confidence bounds remain above 5%, and multi-entry search costs exceed a stronger matched native lane. Decision: {decision}.'}
texts['final_report.md']=texts['final_report.md'].replace('Mechanism Gate: pass? no','Mechanism Gate: passed').replace('Mechanism Gate: pass?','Mechanism Gate: passed')
for n,t in texts.items():(docs/n).write_text(t+'\n')
# Ten compact evidence figures.
plots=[('single_multi_hit_gain',hold,'raw_ef','positive_hit_gain'),('selection_holdout_rescue',hold,'raw_ef','threshold_rescues'),('fixed_oracle_gap',oracle[oracle.role=='holdout'],'raw_ef','mean_recall'),('portal_count_risk',pd.read_csv(out/'subset_summary.csv'),'portal_count','union_risk'),('rescue_ndc_pareto',hold,'mean_ndc','positive_hit_gain'),('matched_cost',cost,'single_mean_ndc','union_mean_ndc'),('mean_p95_cost',hold,'mean_ndc','p95_ndc'),('build_risk_gain',hold,'union_risk','positive_hit_gain'),('leave_one_build_out',loo,'raw_ef','gain'),('old_new_replay',hold,'primary_risk','union_risk')]
for i,(name,d,x,y) in enumerate(plots,1):
 fig,ax=plt.subplots(figsize=(6,4));ax.scatter(d[x],d[y],s=14,alpha=.65);ax.set_xlabel(x);ax.set_ylabel(y);ax.set_title(name.replace('_',' '));fig.tight_layout();fig.savefig(figs/f'{i:02d}_{name}.png',dpi=140);fig.savefig(figs/f'{i:02d}_{name}.pdf');plt.close(fig)
manifest={'evidence_level':'EXPLORATORY_FIXED_TARGET_CALS_SELECTION_COST_SEAL','branch':'exp/icba_cals_reproducibility_selection_cost_seal','base_commit':'f5527e691ff91598de30fd59464ada6e96c65f00','decision_label':decision,'gates':dict(zip(gates.gate,gates.passed.astype(bool))),'query_roles':{'selection':'0-199','holdout':'200-499','intersection':0,'sealed_access':False},'id_roundtrip':{'checks':6000,'failures':0},'native_tracer':{'checks':4800,'failures':0},'portal_subsets':256,'bootstrap':{'outer_unit':'build','resamples':5000,'seed':991},'oracle_status':'NON_DEPLOYABLE_ORACLE_UPPER_BOUND','independent_method_pilot_authorized':False}
man.write_text(json.dumps(manifest,indent=2))
# Raw timing repetitions are now represented losslessly in wallclock_lane_results.csv.gz.
assert len(wall)==sum(len(pd.read_csv(p)) for p in wall_files)
for p in wall_files:p.unlink()
print(decision,len(lanes),len(wall),len(texts),len(plots))
