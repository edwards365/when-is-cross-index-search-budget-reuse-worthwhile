#!/usr/bin/env python3
"""Frozen OCGT-v2 LID/static secondary predictor, isolated from primary gates."""
import csv,gzip,glob,json,struct,hashlib
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-ocgt-v3');MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');DER=ROOT/'results/index_conditionality/ocgt_v3/derived';E=np.array([10,16,24,32,48,64,96,128,192,256,384,512]);sp=json.loads((ROOT/'manifests/ocgt_v3_query_split.json').read_text())['splits'];CAL=sp['calibration'];AUD=sp['confirmatory_audit'];eff=list(csv.DictReader(open(DER/'per_query_effort.csv')))
def ceilg(x):z=E[E>=x];return int(z[0]) if len(z) else 512
files=glob.glob(str(ROOT/'results/index_conditionality/ocgt_v3/gate_r/*__rep1.csv.gz'))+glob.glob(str(ROOT/'results/index_conditionality/ocgt_v3/main_seed*/*__rep1.csv.gz'));G={}
for p in files:
 with gzip.open(p,'rt') as f:
  rs=list(csv.DictReader(f));k=(rs[0]['dataset'],int(rs[0]['graph_seed']),rs[0]['insertion_order']);q={i:{} for i in range(500)}
  for r in rs:q[int(r['query_id'])][int(r['ef_search'])]={'rec':float(r['recall_at_10']),'ndc':float(r['exact_ndc'])}
  G[k]=q
def features(ds):
 m=json.loads((ROOT/'manifests/ocgt_v3_query_membership.json').read_text());r=next(x for x in m['datasets'] if x['dataset']==ds);q=np.load(ROOT/r['queries_path']);brec=next(x for x in json.loads((MAIN/'results/gb_mpcc/r0_inputs/manifest.json').read_text())['inputs'] if x['dataset']==ds);base=np.memmap(MAIN/brec['path'],dtype=np.float32,mode='r',shape=(10000,brec['dimensions']));d=np.empty((500,100));bn=(base*base).sum(1)
 for s in range(0,500,50):z=(q[s:s+50]*q[s:s+50]).sum(1)[:,None]+bn[None,:]-2*q[s:s+50]@base.T;d[s:s+50]=np.sqrt(np.maximum(np.partition(z,99,axis=1)[:,:100],0))
 d.sort(1);rk=d[:,-1];lid=-100/np.log(np.clip(d/(rk[:,None]+1e-30),1e-30,1)).sum(1);return np.column_stack([lid,d[:,0],d[:,9],d[:,9]/(d[:,0]+1e-9),d.mean(1),d.var(1)])
cache={};out=[];source_hash=hashlib.sha256((ROOT/'analyze_ocgt_v2_full.py').read_bytes()).hexdigest()
for k,g in G.items():
 ds=k[0];
 if ds not in cache:cache[ds]=features(ds)
 X=cache[ds];fixed=int(next(r['fixed_ef'] for r in eff if r['dataset']==ds and int(r['seed'])==k[1] and r['order']==k[2]));oracle={int(r['query_id']):int(r['quality_oracle_ef']) for r in eff if r['dataset']==ds and int(r['seed'])==k[1] and r['order']==k[2]};y=np.log2([oracle[q] for q in range(500)]);model=Ridge(alpha=1).fit(X[CAL],y[CAL]);raw=2**model.predict(X);base=np.mean([g[q][fixed]['rec'] for q in CAL]);cands=sorted({float(e/raw[q]) for q in CAL for e in E});mul=cands[-1]
 for z in cands:
  if np.mean([g[q][ceilg(z*raw[q])]['rec'] for q in CAL])>=base-.001:mul=z;break
 ep={q:ceilg(mul*raw[q]) for q in range(500)};fc=np.mean([g[q][fixed]['ndc'] for q in AUD]);pc=np.mean([g[q][ep[q]]['ndc'] for q in AUD]);out.append({'dataset':ds,'seed':k[1],'order':k[2],'model':'LID_STATIC_frozen','recall_diff':float(np.mean([g[q][ep[q]]['rec']-g[q][fixed]['rec'] for q in AUD])),'net_ndc_gain':float((fc-pc)/fc),'actual_probe_cost_included':True,'source_hash':source_hash})
with open(DER/'lid_predictor_net_utility.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=out[0].keys());w.writeheader();w.writerows(out)
print(json.dumps({d:{'mean_recall_diff':float(np.mean([x['recall_diff'] for x in out if x['dataset']==d])),'mean_net_ndc_gain':float(np.mean([x['net_ndc_gain'] for x in out if x['dataset']==d]))} for d in sorted({x['dataset'] for x in out})},indent=2))
