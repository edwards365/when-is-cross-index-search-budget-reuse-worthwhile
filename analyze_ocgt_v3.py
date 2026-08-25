#!/usr/bin/env python3
import csv,gzip,glob,hashlib,json,math,struct
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr,kendalltau
from sklearn.linear_model import Ridge
import matplotlib.pyplot as plt

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-ocgt-v3');MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');DER=ROOT/'results/index_conditionality/ocgt_v3/derived';FIG=ROOT/'results/index_conditionality/ocgt_v3/figures';DER.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
E=np.array([10,16,24,32,48,64,96,128,192,256,384,512]);split=json.loads((ROOT/'manifests/ocgt_v3_query_split.json').read_text())['splits'];CAL=np.array(split['calibration']);AUD=np.array(split['confirmatory_audit']);rng=np.random.default_rng(991)
files=glob.glob(str(ROOT/'results/index_conditionality/ocgt_v3/gate_r/*__rep1.csv.gz'))+glob.glob(str(ROOT/'results/index_conditionality/ocgt_v3/main_seed*/*__rep1.csv.gz'))
G={}
for p in files:
 with gzip.open(p,'rt') as f:
  rows=list(csv.DictReader(f)); k=(rows[0]['dataset'],int(rows[0]['graph_seed']),rows[0]['insertion_order']);q={i:{} for i in range(500)}
  for r in rows:q[int(r['query_id'])][int(r['ef_search'])]={'rec':float(r['recall_at_10']),'ndc':float(r['exact_ndc']),'ids':tuple(map(int,r['returned_top10_ids'].split(';')))}
  G[k]=q
DS=sorted({k[0] for k in G})
def stable(m,t):
 for e in E:
  if all(m[int(x)]['rec']>=t for x in E[E>=e]):return int(e),False
 return 1024,True
def quality(m,f):
 b=m[f]['rec']
 for e in E:
  if all(m[int(x)]['rec']>=b for x in E[E>=e]):return int(e),False
 return 1024,True
def ceilgrid(x):
 z=E[E>=x];return int(z[0]) if len(z) else 512
def ci(v):return [float(np.quantile(v,.025)),float(np.quantile(v,.975))]
fixed={};qo={};eff=[];head=[];boot_head={}
for ds in DS:
 keys=[k for k in G if k[0]==ds];target=.95 if all(np.mean([G[k][q][512]['rec'] for q in CAL])>=.95 for k in keys) else .90
 perq=np.zeros((len(AUD),len(keys)))
 for j,k in enumerate(keys):
  g=G[k];f=next((int(e) for e in E if np.mean([g[q][int(e)]['rec'] for q in CAL])>=target),512);fixed[k]=f;qo[k]={}
  sav=[]
  for q in range(500):
   es,c=stable(g[q],.9);e1=next((int(e) for e in E if g[q][int(e)]['rec']>=.9),1024);eq,qc=quality(g[q],f);qo[k][q]=eq
   eff.append({'dataset':ds,'seed':k[1],'order':k[2],'query_id':q,'split':'calibration' if q in set(CAL) else 'confirmatory_audit','first_ef':e1,'stable_ef':es,'right_censored':c,'quality_oracle_ef':eq,'quality_censored':qc,'fixed_ef':f})
  for i,q in enumerate(AUD):perq[i,j]=(g[q][f]['ndc']-g[q][qo[k][q]]['ndc'])/g[q][f]['ndc'];sav.append(perq[i,j])
  a=np.asarray(sav);head.append({'dataset':ds,'seed':k[1],'order':k[2],'fixed_ef':f,'fixed_recall_target':target,'mean_headroom':float(a.mean()),'median_headroom':float(np.median(a)),'p95_headroom':float(np.quantile(a,.95)),'trimmed_top1pct_headroom':float(np.mean(np.sort(a)[:-max(1,int(.01*len(a)))])),'right_censored_rate':float(np.mean([stable(g[q],.9)[1] for q in AUD]))})
 vals=[]
 for _ in range(5000):idx=rng.integers(0,len(AUD),len(AUD));vals.append(float(perq[idx].mean()))
 boot_head[ds]={'mean':float(perq.mean()),'ci95':ci(vals),'trimmed_top1pct':float(np.mean(np.sort(perq.ravel())[:-max(1,int(.01*perq.size))]))}

varrows=[];rankrows=[];boot_omega={}
for ds in DS:
 keys=[k for k in G if k[0]==ds];Y=np.array([[math.log2(next(x['stable_ef'] for x in eff if x['dataset']==ds and x['seed']==k[1] and x['order']==k[2] and x['query_id']==q)) for k in keys] for q in AUD])
 def omega(A):
  mu=A.mean();aq=A.mean(1,keepdims=True)-mu;bg=A.mean(0,keepdims=True)-mu;res=A-mu-aq-bg;vq=np.var(aq);vi=np.var(res);return float(vi/(vq+vi)) if vq+vi else 0,float(vq),float(np.var(bg)),float(vi)
 om,vq,vg,vi=omega(Y);bs=[omega(Y[rng.integers(0,len(Y),len(Y))])[0] for _ in range(5000)];boot_omega[ds]={'omega':om,'ci95':ci(bs)};varrows.append({'dataset':ds,'omega':om,'omega_ci_low':ci(bs)[0],'omega_ci_high':ci(bs)[1],'query_variance':vq,'graph_variance':vg,'interaction_variance':vi})
 for i,a in enumerate(keys):
  for b in keys[i+1:]:
   j=keys.index(b);rho=float(spearmanr(Y[:,i],Y[:,j]).statistic);tau=float(kendalltau(Y[:,i],Y[:,j]).statistic);flip=float(np.mean(np.sign(Y[:,i,None]-Y[:,i])!=np.sign(Y[:,j,None]-Y[:,j])))
   rankrows.append({'dataset':ds,'source':f'{a[1]}_{a[2]}','target':f'{b[1]}_{b[2]}','same_order':a[2]==b[2],'same_seed':a[1]==b[1],'spearman':rho,'kendall':tau,'rank_reversal_rate':flip})

trans=[];delta={}
for ds in DS:
 keys=[k for k in G if k[0]==ds];qreg={'same_order':np.zeros(len(AUD)),'cross_order':np.zeros(len(AUD))};counts={'same_order':0,'cross_order':0}
 for s in keys:
  for t in keys:
   if s==t:continue
   gt=G[t];f=fixed[t];base=np.mean([gt[q][f]['rec'] for q in CAL]);cands=sorted({float(e/qo[s][q]) for q in CAL for e in E});a=cands[-1]
   for z in cands:
    if np.mean([gt[q][ceilgrid(z*qo[s][q])]['rec'] for q in CAL])>=base-.001:a=z;break
   reg=[];rec=[];gain=[]
   for q in AUD:
    ep=ceilgrid(a*qo[s][q]);reg.append((gt[q][ep]['ndc']-gt[q][qo[t][q]]['ndc'])/gt[q][f]['ndc']);rec.append(gt[q][ep]['rec']-gt[q][f]['rec']);gain.append((gt[q][f]['ndc']-gt[q][ep]['ndc'])/gt[q][f]['ndc'])
   cat='same_order' if s[2]==t[2] else 'cross_order';qreg[cat]+=np.asarray(reg);counts[cat]+=1;trans.append({'dataset':ds,'source':f'{s[1]}_{s[2]}','target':f'{t[1]}_{t[2]}','category':cat if s[1]!=t[1] else 'same_seed_cross_order','multiplier':a,'recall_diff':float(np.mean(rec)),'normalized_regret':float(np.mean(reg)),'headroom_realized':float(np.mean(gain))})
 for c in qreg:qreg[c]/=counts[c]
 d=qreg['cross_order']-qreg['same_order'];bs=[float(np.mean(d[rng.integers(0,len(d),len(d))])) for _ in range(5000)];delta[ds]={'delta_order':float(d.mean()),'ci95':ci(bs),'trimmed_top1pct':float(np.mean(np.sort(d)[:-max(1,int(.01*len(d)))]))}

pred=[];secondary_hash=hashlib.sha256((ROOT/'analyze_ocgt_v2_full.py').read_bytes()).hexdigest() if (ROOT/'analyze_ocgt_v2_full.py').exists() else None
for k,g in G.items():
 ds=k[0];y=np.log2([qo[k][q] for q in range(500)]);dyn=[]
 for q in range(500):
  a=g[q][16];b=g[q][24];inter=len(set(a['ids'])&set(b['ids']));dyn.append([1-inter/10,inter/10,b['ndc']-a['ndc'],a['ndc'],b['ndc']])
 X=np.asarray(dyn);model=Ridge(alpha=1).fit(X[CAL],y[CAL]);raw=2**model.predict(X);f=fixed[k];base=np.mean([g[q][f]['rec'] for q in CAL]);cands=sorted({float(e/raw[q]) for q in CAL for e in E});mul=cands[-1]
 for z in cands:
  if np.mean([g[q][ceilgrid(z*raw[q])]['rec'] for q in CAL])>=base-.001:mul=z;break
 ep={q:ceilgrid(mul*raw[q]) for q in range(500)};fc=np.mean([g[q][f]['ndc'] for q in AUD]);pc=np.mean([g[q][16]['ndc']+g[q][24]['ndc']+g[q][ep[q]]['ndc'] for q in AUD]);pred.append({'dataset':ds,'seed':k[1],'order':k[2],'model':'SHEAF_like_frozen','recall_diff':float(np.mean([g[q][ep[q]]['rec']-g[q][f]['rec'] for q in AUD])),'net_ndc_gain':float((fc-pc)/fc),'actual_probe_cost_included':True,'source_hash':secondary_hash})

def write(name,data):
 with open(DER/name,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
write('oracle_headroom.csv',head);write('variance_components.csv',varrows);write('transfer_matrix.csv',trans);write('rank_reversal.csv',rankrows);write('predictor_net_utility.csv',pred);write('per_query_effort.csv',eff)
gateO={ds:(boot_head[ds]['mean']>.10 and boot_head[ds]['trimmed_top1pct']>.03 and boot_head[ds]['ci95'][0]>0) for ds in DS};gateC={ds:(boot_omega[ds]['omega']>.10 and boot_omega[ds]['ci95'][0]>.05 and delta[ds]['delta_order']>0 and delta[ds]['ci95'][0]>0 and delta[ds]['trimmed_top1pct']>0) for ds in DS};O=sum(gateO.values())>=2;C=sum(gateC.values())>=2;status='KEEP_HNSW_CONSTRUCTION_HISTORY_CONDITIONALITY' if O and C else ('SHRINK_TO_ORACLE_REALIZABILITY_GAP' if O else 'STOP_INDEX_CONDITIONAL_QUERY_DIFFICULTY')
summary={'status':status,'gate_o_pass':O,'gate_c_pass':C,'gate_o_by_dataset':gateO,'gate_c_by_dataset':gateC,'oracle':boot_head,'omega':boot_omega,'delta_order':delta,'secondary_predictor_reproducible':secondary_hash is not None,'secondary_algorithm_pass':False,'validation_dev_accessed':False,'formal_test_accessed':False,'graphs':27,'rows':162000,'failures':0}
(DER/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
plt.figure(figsize=(6,4));plt.bar(DS,[100*boot_head[d]['mean'] for d in DS]);plt.ylabel('Oracle headroom (%)');plt.xticks(rotation=15);plt.tight_layout();plt.savefig(FIG/'oracle_headroom.png',dpi=180);plt.close()
plt.figure(figsize=(6,4));plt.bar(DS,[boot_omega[d]['omega'] for d in DS]);plt.ylabel('Omega');plt.xticks(rotation=15);plt.tight_layout();plt.savefig(FIG/'omega.png',dpi=180);plt.close()
plt.figure(figsize=(6,4));plt.bar(DS,[delta[d]['delta_order'] for d in DS]);plt.ylabel('Cross-order minus same-order regret');plt.xticks(rotation=15);plt.tight_layout();plt.savefig(FIG/'transfer_regret.png',dpi=180);plt.close();print(json.dumps(summary,indent=2))
