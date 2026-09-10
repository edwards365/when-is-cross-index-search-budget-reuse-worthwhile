#!/usr/bin/env python3
from __future__ import annotations
import csv,hashlib,json,shutil
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

R=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
RES=R/'results/graph_anns_iclr_phase1'; DOC=R/'docs/graph_anns_iclr_phase1'; FIG=R/'figures/graph_anns_iclr_phase1'; MAN=R/'manifests/graph_anns_iclr_phase1_decision.json'
FIG.mkdir(parents=True,exist_ok=True)
def read(name):
 with (RES/name).open(newline='') as f:return list(csv.DictReader(f))
def write(name,rows):
 fields=[]
 for row in rows:
  for key in row:
   if key not in fields:fields.append(key)
 with (RES/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def sha(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def save(fig,name):
 fig.tight_layout();fig.savefig(FIG/f'{name}.png',dpi=180);fig.savefig(FIG/f'{name}.pdf');plt.close(fig)

# Paper tables are generated aliases with explicit source provenance.
aliases={'paper_table_P1_semantic.csv':'cross_family_semantic_table.csv','paper_table_P2_censoring.csv':'unresolved_mass.csv','paper_table_P3_workpoints.csv':'workpoint_sensitivity.csv','paper_table_P4_profiling_cost.csv':'profiling_cost_decomposition.csv','paper_table_P6_break_even.csv':'break_even.csv','paper_table_P7_deterministic.csv':'deterministic_rebuild_results.csv'}
for dst,src in aliases.items():shutil.copyfile(RES/src,RES/dst)
power=read('certification_power_table.csv');timing=read('certification_timing.csv')
write('paper_table_P5_certification.csv',[{'record_type':'power','dataset':'ALL','threads':'NA',**x} for x in power]+[{'record_type':'timing',**x} for x in timing])
claims=[
 {'claim':'phenomenon','status':'SUPPORTED_FIXED_REGISTERED_BUILDS','change':'retain with fixed-family scope'},
 {'claim':'risk','status':'SUPPORTED','change':'retain tau=.95 primary and .90/.99 sensitivity'},
 {'claim':'economic','status':'OPERATOR_DEPENDENT','change':'delete blanket expensive-profiling claim; 100K hnswlib is cheap, Faiss cell is 30K, Vamana direct timing not estimable'},
 {'claim':'mitigation','status':'SUPPORTED_TWO_DATASETS','change':'add strict deterministic rebuild contract as preferred engineering route'},
 {'claim':'environment_name','status':'PATCH','change':'use partially observed stochastic build environment'},
 {'claim':'theorem_1','status':'SCOPE_PATCH','change':'state risk semantics only; no native-ef or open-world deterministic guarantee'}]
write('paper_table_P8_claim_changes.csv',claims)

# P1 workpoint risk.
w=read('workpoint_sensitivity.csv'); labels=sorted({f"{x['implementation'].split()[0]}\n{x['dataset'].replace('_100k','')}" for x in w}); fig,ax=plt.subplots(figsize=(10,5))
for tau,mark in [('0.9','o'),('0.95','s'),('0.99','^')]:
 vals=[]
 for lab in labels:
  impl,ds=lab.split('\n'); rr=next(x for x in w if x['implementation'].startswith(impl) and x['dataset'].replace('_100k','')==ds and x['tau']==tau);vals.append(float(rr['incremental_transport_risk']))
 ax.plot(range(len(labels)),vals,marker=mark,label=f'tau={tau}')
ax.set_xticks(range(len(labels)),labels,rotation=30,ha='right');ax.set_ylabel('incremental transport risk');ax.legend();save(fig,'P1_workpoint_transport_risk')
write('figure_P1_source.csv',w)

# P2 profiling stack at n=59, 8 threads.
p=[x for x in read('profiling_cost_decomposition.csv') if x['threads']=='8' and x['n']=='59'];fig,ax=plt.subplots(figsize=(9,5));x=np.arange(len(p));bottom=np.zeros(len(p))
for col,label in [('truth_seconds','truth'),('candidate_family_seconds','candidate replay'),('cert_and_policy_seconds','cert/control')]:
 v=np.array([float(r[col]) for r in p]);ax.bar(x,v,bottom=bottom,label=label);bottom+=v
ax.set_xticks(x,[f"{r['implementation']}\n{r['dataset']}" for r in p],rotation=25,ha='right');ax.set_ylabel('seconds');ax.legend();save(fig,'P2_profiling_cost_stack');write('figure_P2_source.csv',p)

# P3 break-even curves for estimable hnswlib n=59 deployment setting.
b=[x for x in read('break_even.csv') if x['implementation']=='hnswlib' and x['threads']=='8' and x['n']=='59']; workloads=np.array([1e3,1e4,1e5,1e6,1e7]);src=[];fig,ax=plt.subplots(figsize=(7,5))
for r in b:
 k=float(r['wall_clock_K0_seconds']);d=float(r['net_saving_seconds_per_query']);cost=k-workloads*d;ax.plot(workloads,cost,marker='o',label=r['dataset']);src += [{'dataset':r['dataset'],'workload':int(n),'net_incremental_seconds':float(c)} for n,c in zip(workloads,cost)]
ax.axhline(0,color='black',lw=.8);ax.set_xscale('log');ax.set_ylabel('P2 cumulative incremental seconds');ax.set_xlabel('service queries');ax.legend();save(fig,'P3_break_even');write('figure_P3_source.csv',src)

d=read('deterministic_rebuild_results.csv');
# P4 risk and category.
src4=[{'dataset':r['dataset'],'regime':r['regime'],'category_variation':r['category_variation'],'incremental_transport_risk':r['incremental_transport_risk']} for r in d];fig,axs=plt.subplots(1,2,figsize=(10,4))
for ds in ('sift_100k','arxiv_nomic_100k'):
 z=[r for r in src4 if r['dataset']==ds];axs[0].plot([r['regime'] for r in z],[float(r['category_variation']) for r in z],marker='o',label=ds);axs[1].plot([r['regime'] for r in z],[float(r['incremental_transport_risk']) for r in z],marker='o',label=ds)
axs[0].set_ylabel('category variation');axs[1].set_ylabel('incremental transport risk');axs[1].legend();save(fig,'P4_deterministic_risk');write('figure_P4_source.csv',src4)
# P5 service tradeoff on native safe ef.
src5=[{'dataset':r['dataset'],'regime':r['regime'],'aggregate_recall_at_max':r['aggregate_recall_at_max'],'finite_budget_mean':r['finite_budget_mean'],'finite_budget_p95':r['finite_budget_p95']} for r in d];fig,axs=plt.subplots(1,3,figsize=(12,4))
for ds in ('sift_100k','arxiv_nomic_100k'):
 z=[r for r in src5 if r['dataset']==ds];xx=[r['regime'] for r in z];axs[0].plot(xx,[float(r['aggregate_recall_at_max']) for r in z],marker='o',label=ds);axs[1].plot(xx,[float(r['finite_budget_mean']) for r in z],marker='o');axs[2].plot(xx,[float(r['finite_budget_p95']) for r in z],marker='o')
axs[0].set_ylabel('Recall@10 at ef=200');axs[1].set_ylabel('mean finite safe ef');axs[2].set_ylabel('p95 finite safe ef');axs[0].legend();save(fig,'P5_deterministic_tradeoff');write('figure_P5_source.csv',src5)
# P6 decision flow.
flow=[{'order':1,'node':'Strict deterministic rebuild contract','on_pass':'Deploy D3 contract','on_fail':'Per-target certified profiling'},{'order':2,'node':'Per-target certified profiling','on_pass':'Deploy lowest certified action','on_fail':'Abstain/max-safe fallback'},{'order':3,'node':'Evidence boundary','on_pass':'Fixed registered scope','on_fail':'No open-world claim'}];write('figure_P6_source.csv',flow);fig,ax=plt.subplots(figsize=(10,3));ax.axis('off');texts=['D3 deterministic\ncontract','per-target certified\nprofiling','abstain / max-safe\nfallback'];xs=[.15,.5,.85]
for x,t in zip(xs,texts):ax.text(x,.5,t,ha='center',va='center',bbox=dict(boxstyle='round',fc='#e8f1ff'));
for a,bx in zip(xs[:-1],xs[1:]):ax.annotate('',xy=(bx-.1,.5),xytext=(a+.1,.5),arrowprops=dict(arrowstyle='->'))
save(fig,'P6_decision_flow')

impact='''# Paper impact report\n\nThe semantic core is robust on the registered fixed build families. The blanket claim that target profiling is expensive must be removed: directly measured hnswlib/Faiss profiling is seconds or less at registered sample sizes, while Vamana remains interface-limited and Faiss is a 30K-base cell. The practical recommendation is strict deterministic rebuild first; if that contract cannot be maintained, use per-target certified profiling; otherwise abstain or use the registered maximum-safe fallback. Rename hidden environment to “partially observed stochastic build environment”. D3 is an actionable fifth engineering route within identical data, toolchain, canonical order, fixed randomness and controlled concurrency only. No 1M run is authorized in Phase I; provide resource estimates separately.\n'''
(DOC/'paper_impact_report.md').write_text(impact);(DOC/'claim_registry_patch.md').write_text('# Claim registry patch\n\n'+ '\n'.join(f"- **{x['claim']}** — {x['status']}: {x['change']}" for x in claims)+'\n')
final='''# ICLR Phase-I final report\n\nSemantic: **SEMANTIC_CORE_ROBUST**. Economics: **PROFILING_COST_OPERATOR_DEPENDENT**. Mitigation: **DETERMINISTIC_REBUILD_ACTIONABLE_MITIGATION**.\n\nUnique decision: **ICLR_PHASE1_ACTIONABLE_CLOSURE_PASS**.\n\nD3 achieved byte-identical and search-identical rebuilds on SIFT-100K and Arxiv-Nomic-100K. The fixed-family transport phenomenon remains positive across all registered workpoints, while strict deterministic rebuild removes within-contract transport risk. Profiling is inexpensive on directly measurable cells at this scale, but economic evidence remains operator-dependent because Faiss used a 30K base and Vamana lacks an isolated cost-only replay interface.\n''';(DOC/'final_report.md').write_text(final)
manifest={'parent_commit':'d2ad714541d73bedcd48580347b67880d37580f8','branch':'exp/graph_anns_iclr_phase1_decisive_supplement','deadline':'2026-09-15T23:59:00+08:00','completed_before_deadline':True,'semantic':'SEMANTIC_CORE_ROBUST','economics':'PROFILING_COST_OPERATOR_DEPENDENT','mitigation':'DETERMINISTIC_REBUILD_ACTIONABLE_MITIGATION','decision':'ICLR_PHASE1_ACTIONABLE_CLOSURE_PASS','future_replication_accessed':False,'validation_dev_accessed':False,'formal_test_accessed':False,'faiss_actual_base_vectors':30000,'scope':'REGISTERED_FIXED_BUILD_FAMILIES','limitations':['Faiss external-validity cell is 30K base despite historical name','Vamana isolated cost-only replay not estimable','D3 scope excludes data updates, deletion, hardware/version changes and query shift','finite native ef budget, not tracer NDC, used for Phase1C cost gate']};MAN.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
core=[DOC/'preregistered_contract.md',RES/'frozen_config.json',RES/'cross_family_semantic_table.csv',RES/'workpoint_sensitivity.csv',RES/'profiling_cost_decomposition.csv',RES/'break_even.csv',RES/'deterministic_rebuild_results.csv',RES/'deterministic_rebuild_gate.csv',DOC/'final_report.md',DOC/'paper_impact_report.md',DOC/'claim_registry_patch.md',MAN]
with (RES/'final_core.sha256').open('w') as f:
 for p in core:f.write(f'{sha(p)}  {p.relative_to(R)}\n')
print(json.dumps(manifest,indent=2))
if __name__=='__main__':pass
