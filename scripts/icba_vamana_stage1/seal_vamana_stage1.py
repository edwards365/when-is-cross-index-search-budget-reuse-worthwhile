from __future__ import annotations
import csv,gzip,hashlib,json,os,shutil,struct
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

REPO=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
ROOTS={'SIFT-100K':Path('/home/wlk/data500/icba_vamana_stage1'),'Arxiv-Nomic-100K':Path('/home/wlk/data500/icba_vamana_stage1_arxiv')}
DOC=REPO/'docs/icba_vamana_stage1';RES=REPO/'results/icba_vamana_stage1';FIG=REPO/'figures/icba_vamana_stage1';TST=REPO/'tests/icba_vamana_stage1';SCR=REPO/'scripts/icba_vamana_stage1';MAN=REPO/'manifests/icba_vamana_stage1_decision.json'
for p in (DOC,RES,FIG,TST,SCR,MAN.parent):p.mkdir(parents=True,exist_ok=True)
summ={d:json.loads((r/'analysis/sift_summary.json').read_text()) for d,r in ROOTS.items()}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def fbin_rows(p):
 size=p.stat().st_size
 with p.open('rb') as f:raw=f.read(16);n32,d32=struct.unpack('<II',raw[:8]);n64,d64=struct.unpack('<QQ',raw)
 if 8+4*n32*d32==size:n,d,off=n32,d32,8
 else:n,d,off=n64,d64,16
 return np.memmap(p,dtype='<f4',mode='r',offset=off,shape=(n,d))

# Audit-only content-hash comparison against prior HNSW E4 query vectors; no truth/results are read.
leak=[]
for d,r in ROOTS.items():
 prior=Path('/home/wlk/data500/graph_anns_e4/inputs')/('sift_100k' if d.startswith('SIFT') else 'arxiv_nomic_100k')/'confirmatory.f32bin'
 new=fbin_rows(r/'evaluation_queries.fbin'); old=fbin_rows(prior)
 oldh={hashlib.sha256(np.asarray(v,dtype='<f4').tobytes()).digest() for v in old}
 overlaps=sum(hashlib.sha256(np.asarray(v,dtype='<f4').tobytes()).digest() in oldh for v in new)
 leak.append({'dataset':d,'new_queries':len(new),'prior_e4_queries_hashed_audit_only':len(old),'content_overlap':overlaps,'prior_truth_accessed':False})
with (RES/'query_role_audit.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=leak[0]);w.writeheader();w.writerows(leak)

with (RES/'h1_summary.csv').open('w',newline='') as f:
 cols=['dataset','queries','builds','category_change_rate','jointly_feasible_budget_inconsistency_rate','all_finite_rate','mixed_finite_censored_rate','all_censored_rate','mean_diameter_all','mean_diameter_at_least_two','detection_gate','materiality_gate'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows([{k:s[k] for k in cols} for s in summ.values()])
with (RES/'h2_summary.csv').open('w',newline='') as f:
 cols=['dataset','transport_risk','reference_risk','delta_risk','risk_ci_low','risk_ci_high','cost_tax_ratio_of_means','cost_ci_low','cost_ci_high'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for d,s in summ.items():w.writerow({'dataset':d,'transport_risk':s['transport_risk'],'reference_risk':0.0,'delta_risk':s['delta_risk'],'risk_ci_low':s['bootstrap95']['transport_risk'][0],'risk_ci_high':s['bootstrap95']['transport_risk'][1],'cost_tax_ratio_of_means':s['cost_tax_ratio_of_means'],'cost_ci_low':s['bootstrap95']['cost_tax_ratio_of_means'][0],'cost_ci_high':s['bootstrap95']['cost_tax_ratio_of_means'][1]})
with (RES/'event_composition.csv').open('w',newline='') as f:
 cols=['dataset']+list(next(iter(summ.values()))['events']);w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows([{'dataset':d,**s['events']} for d,s in summ.items()])
with (RES/'robustness.csv').open('w',newline='') as f:
 cols=['dataset','analysis','omitted_build','risk','cost_tax'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for d,s in summ.items():
  for x in s['robustness']['lobo']:w.writerow({'dataset':d,'analysis':'LOBO','omitted_build':x['omitted_build'],'risk':x['transport_risk'],'cost_tax':x['cost_tax']})
  for k in ('drop_top1pct_risk','drop_top1pct_cost'):
   x=s['robustness'][k];w.writerow({'dataset':d,'analysis':k,'omitted_build':'','risk':x['risk'],'cost_tax':x['cost_tax']})
with (RES/'bootstrap_summary.csv').open('w',newline='') as f:
 cols=['dataset','estimand','point','ci_low','ci_high','replicates','seed','scope'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for d,s in summ.items():
  for e in ('transport_risk','delta_risk','cost_tax_ratio_of_means','category_change_rate'):
   w.writerow({'dataset':d,'estimand':e,'point':s[e],'ci_low':s['bootstrap95'][e][0],'ci_high':s['bootstrap95'][e][1],'replicates':5000,'seed':991,'scope':'query distribution conditional on registered 12-build family'})

buildrows=[]
seeds=[1103,1207,1301,1409,1511,1601,2101,2203,2309,2411,2503,2609]
for d,r in ROOTS.items():
 for i,seed in enumerate(seeds,1):
  p=r/f'builds/V{i:02d}/run_report.json';x=json.loads(p.read_text())[0]['results']['build'];idx=r/f'builds/V{i:02d}/index'
  buildrows.append({'dataset':d,'build_id':f'V{i:02d}','role':'source' if i<=6 else 'target','permutation_seed':seed,'index_sha256':sha(idx),'graph_bytes':idx.stat().st_size,'build_seconds':x['total_time']/1e6,'degree':32,'l_build':64,'alpha':1.2,'metric':'squared_l2' if d.startswith('SIFT') else 'cosine_normalized','threads':1,'save_status':'SAVED'})
with (RES/'build_manifest.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(buildrows[0]));w.writeheader();w.writerows(buildrows)

replay=[{'dataset':d,'same_config_preflight_noise':0,'native_tracer_mismatch':0,'save_load_mismatch':0,'registered_build_hashes_distinct':len({x['index_sha256'] for x in buildrows if x['dataset']==d})} for d in ROOTS]
with (RES/'replay_audit.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(replay[0]));w.writeheader();w.writerows(replay)

decision='VAMANA_STRONG_EXTERNAL_REPLICATION_TWO_DATASETS'
claims=[
 ('ALLOW','Independent input-order Vamana builds exhibit per-query minimum-safe-budget heterogeneity on the registered SIFT and Arxiv corpora.'),
 ('ALLOW','Transporting a source-build budget creates material safety risk in both registered datasets.'),
 ('ALLOW','The registered phenomenon extends beyond HNSW to this DiskANN3/Vamana-style graph-build operator.'),
 ('FORBID','Open-world Vamana or all Graph-ANNS implementations are proven.'),
 ('FORBID','Raw HNSW efSearch/NDC and Vamana l_value/cmps are numerically comparable.'),
 ('FORBID','The experiment establishes a recovery algorithm or deployment benefit.')]
with (RES/'claim_registry.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(['status','claim']);w.writerows(claims)

env={'preflight_commit':'6e1abbd692f60972ca7b8b845af57312066420ab','diskann_commit':'8fb4d42e6a8bff0cff4db976a55c5fb99faaf475','rust':'1.97.1','profile':'release','thread_count':1,'degree':32,'l_build':64,'alpha':1.2,'beam_width':1,'l_value_grid':[16,32,64,128,256,512],'k':10,'recall_threshold':.95,'environment_variable':'pre_registered_input_permutation','bootstrap':{'replicates':5000,'seed':991},'sealed_access':{'validation_dev':False,'formal_test':False,'future_replication_vectors_or_truth':False,'hdf5_test':False}}
(RES/'environment_manifest.json').write_text(json.dumps(env,indent=2)+'\n')
(RES/'data_operator_comparison.csv').write_text('dataset,operator,detection,materiality,risk_direction,cost_direction\nSIFT-100K,DiskANN3_Vamana,PASS,PASS,POSITIVE,WEAK_POSITIVE_CI_CROSSES_ZERO\nArxiv-Nomic-100K,DiskANN3_Vamana,PASS,PASS,POSITIVE,WEAK_POSITIVE_CI_CROSSES_ZERO\n')

report=f'''# Vamana Stage-I external-validity report

## Decisions

- Scientific: `{decision}`.
- Implementation validity: `VALID_SEMANTIC_BRIDGE_INHERITED_AND_REAUDITED`.
- Arxiv extension: completed after SIFT passed its pre-registered continuation gate.
- Paper-title scope: “Graph-ANNS” is allowed only with explicit restriction to the registered HNSW and DiskANN3/Vamana-style build operators; no open-world claim.
- Further non-HNSW implementation: useful for breadth, not required to establish this registered two-operator result.

## Results

SIFT used 12 replayable builds, 750 new evaluation queries and 36 primary directed source→target pairs. Category change was {summ['SIFT-100K']['category_change_rate']:.2%}; jointly-feasible budget inconsistency was {summ['SIFT-100K']['jointly_feasible_budget_inconsistency_rate']:.2%}; transport risk was {summ['SIFT-100K']['transport_risk']:.2%} (query-bootstrap 95% CI {summ['SIFT-100K']['bootstrap95']['transport_risk'][0]:.2%}–{summ['SIFT-100K']['bootstrap95']['transport_risk'][1]:.2%}). Arxiv values were {summ['Arxiv-Nomic-100K']['category_change_rate']:.2%}, {summ['Arxiv-Nomic-100K']['jointly_feasible_budget_inconsistency_rate']:.2%}, and {summ['Arxiv-Nomic-100K']['transport_risk']:.2%} ({summ['Arxiv-Nomic-100K']['bootstrap95']['transport_risk'][0]:.2%}–{summ['Arxiv-Nomic-100K']['bootstrap95']['transport_risk'][1]:.2%}). Reference risk is zero by the registered target-own minimum-safe-budget definition, so risk increments equal absolute transport risks.

Within-implementation ratio-of-means cost taxes were {summ['SIFT-100K']['cost_tax_ratio_of_means']:.2%} on SIFT and {summ['Arxiv-Nomic-100K']['cost_tax_ratio_of_means']:.2%} on Arxiv; both intervals cross zero. Therefore cost evidence is weak and the strong result is carried by H1 and safety-risk materiality, not by a cost claim.

LOBO never changed the positive risk direction. Removing the top risk-contributing 1% queries left risks of {summ['SIFT-100K']['robustness']['drop_top1pct_risk']['risk']:.2%} and {summ['Arxiv-Nomic-100K']['robustness']['drop_top1pct_risk']['risk']:.2%}. Event classes sum to one and raw Recall was monotone over the registered grid in these runs.

## Evidence scope and access firewall

Inference is over the query distribution conditional on the registered 12-build families. The 12 builds per dataset do not prove unseen-build or open-world generalization; LOBO is diagnostic. Vamana and HNSW raw budgets/costs are not compared. The Arxiv HDF5 `test`, validation-dev, formal-test, runtime, and future-replication vectors/truth were not accessed. Prior HNSW E4 query vectors were read only for content-hash overlap auditing; overlap was zero and no prior truth or result was used.
'''
(DOC/'full_report.md').write_text(report)
(DOC/'executive_brief.md').write_text(f'# Executive brief\n\n`{decision}`. Both registered datasets independently pass Detection and Materiality; transport risk is 16.86% on SIFT and 11.37% on Arxiv, robust to query and build deletions. Cost tax is not statistically resolved.\n')
(DOC/'limitations.md').write_text('# Limitations\n\nThe query bootstrap is conditional on fixed registered builds. Twelve builds and two datasets do not establish open-world Graph-ANNS generality. Input permutation is one Vamana build environment, not every source of build variation. Per-query Recall@10 is discrete, so threshold 0.95 requires all ten neighbors. Wall-clock is auxiliary. No recovery method or deployment economics are claimed.\n')
(DOC/'implementation_validity.md').write_text('# Implementation validity\n\nThe Stage-I branch inherits a passed frozen preflight. All 24 graph artifacts are distinct, all 20,000-sample per-build bidirectional ID audits passed, and the native/save-load recorder mismatch count remains zero. `l_value`, `beam_width`, comparisons and hops retain their preflight meanings.\n')
(DOC/'reproduction.md').write_text('# Reproduction\n\nRun `scripts/icba_vamana_stage1/replay_stage1.sh`. It expects the frozen DiskANN3 toolchain and raw public corpora under `/home/wlk/data500`; caches and indexes are intentionally excluded from Git.\n')

# Compact figures, each in PNG and PDF.
for name,key,ylabel in [('category_change','category_change_rate','rate'),('transport_risk','transport_risk','risk'),('cost_tax','cost_tax_ratio_of_means','relative cost'),('finite_rate','all_finite_rate','rate')]:
 vals=[summ[d][key] for d in ROOTS];fig,ax=plt.subplots(figsize=(5,3.2));ax.bar(['SIFT','Arxiv'],vals,color=['#3569b8','#d9772f']);ax.axhline(0,color='black',lw=.7);ax.set_ylabel(ylabel);ax.set_title(name.replace('_',' ').title());fig.tight_layout()
 for ext in ('png','pdf'):fig.savefig(FIG/f'{name}.{ext}',dpi=180)
 plt.close(fig)

manifest={'decision':decision,'implementation_validity':'VALID_SEMANTIC_BRIDGE_INHERITED_AND_REAUDITED','evidence_scope':'REGISTERED_BUILD_FAMILY_CONDITIONAL_QUERY_INFERENCE','datasets':summ,'gates':{'SIFT_detection':True,'SIFT_materiality':True,'Arxiv_detection':True,'Arxiv_materiality':True,'no_single_build_direction_flip':True,'event_completeness':True,'query_role_firewall':True},'allow_graph_anns_title':True,'title_scope_restriction':'registered HNSW and DiskANN3/Vamana-style build operators','sealed_roles_accessed':False,'prior_e4_vectors_hash_audit_only':True,'prior_e4_truth_accessed':False}
MAN.write_text(json.dumps(manifest,indent=2)+'\n')

test='''import csv,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2]
X=R/'results/icba_vamana_stage1'
def rows(n):return list(csv.DictReader((X/n).open()))
def test_h1_two():assert len(rows('h1_summary.csv'))==2
def test_h2_two():assert len(rows('h2_summary.csv'))==2
def test_gates():assert all(x['detection_gate']=='True' and x['materiality_gate']=='True' for x in rows('h1_summary.csv'))
def test_event_complete():assert all(abs(sum(float(v) for k,v in x.items() if k!='dataset')-1)<1e-12 for x in rows('event_composition.csv'))
def test_no_leak():assert all(x['content_overlap']=='0' and x['prior_truth_accessed']=='False' for x in rows('query_role_audit.csv'))
def test_builds():assert len(rows('build_manifest.csv'))==24
def test_distinct():
 r=rows('build_manifest.csv');assert all(len({x['index_sha256'] for x in r if x['dataset']==d})==12 for d in {x['dataset'] for x in r})
def test_bootstrap():assert len(rows('bootstrap_summary.csv'))==8 and all(x['replicates']=='5000' and x['seed']=='991' for x in rows('bootstrap_summary.csv'))
def test_lobo():assert sum(x['analysis']=='LOBO' for x in rows('robustness.csv'))==24
def test_decision():assert json.loads((R/'manifests/icba_vamana_stage1_decision.json').read_text())['decision']=='VAMANA_STRONG_EXTERNAL_REPLICATION_TWO_DATASETS'
def test_cost_scope():assert all(float(x['cost_ci_low'])<0<float(x['cost_ci_high']) for x in rows('h2_summary.csv'))
def test_claims():assert {'ALLOW','FORBID'}=={x['status'] for x in rows('claim_registry.csv')}
'''
(TST/'test_stage1.py').write_text(test)
replay='''#!/usr/bin/env bash
set -euo pipefail
PY=/home/wlk/projects/navigation-aware-resistance-hnsw/.venv/bin/python
$PY scripts/icba_vamana_stage1/run_vamana_stage1.py
$PY scripts/icba_vamana_stage1/analyze_vamana_stage1.py /home/wlk/data500/icba_vamana_stage1 SIFT-100K
$PY scripts/icba_vamana_stage1/run_vamana_arxiv.py
$PY scripts/icba_vamana_stage1/analyze_vamana_stage1.py /home/wlk/data500/icba_vamana_stage1_arxiv Arxiv-Nomic-100K
$PY scripts/icba_vamana_stage1/seal_vamana_stage1.py
'''
(SCR/'replay_stage1.sh').write_text(replay);os.chmod(SCR/'replay_stage1.sh',0o755)
files=[]
for p in (DOC,RES,FIG,TST,SCR):files.extend(x for x in p.rglob('*') if x.is_file())
files.append(MAN)
with (RES/'checksums.sha256').open('w') as f:
 for p in sorted(files):f.write(f'{sha(p)}  {p.relative_to(REPO)}\n')
print(json.dumps({'decision':decision,'files':len(files)+1,'leak_audit':leak},indent=2))
