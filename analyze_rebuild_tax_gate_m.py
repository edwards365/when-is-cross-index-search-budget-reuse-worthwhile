#!/usr/bin/env python3
import csv,gzip,glob,json,math
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr,kendalltau
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge,LogisticRegression
from sklearn.metrics import r2_score,roc_auc_score,average_precision_score
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');OUT=ROOT/'results/rebuild_tax/derived';E=np.array([10,16,24,32,48,64,96,128,192,256,384,512]);DELTAS=[0,.001,.005,.01,.05,.10];RNG=np.random.default_rng(991)
split=json.load(open(ROOT/'manifests/hardness_portability_100k/query_split.json'))['splits'];CAL=np.array(split['train_design']);AUD=np.array(split['internal_test']);groups={'realistic':{'random','natural_source_order','cluster_block_order'},'artificial':{'lid_ascending','lid_descending'},'pooled':{'random','lid_ascending','lid_descending','natural_source_order','cluster_block_order'}}
def ci(v):return [float(np.quantile(v,.025)),float(np.quantile(v,.975))]
def load():
 G={}
 for root in ('core_raw','realistic_raw'):
  for p in glob.glob(str(ROOT/f'results/hardness_portability_100k/{root}/*.csv.gz')):
   with gzip.open(p,'rt',newline='') as f:rows=list(csv.DictReader(f))
   k=(rows[0]['dataset'],int(rows[0]['graph_seed']),rows[0]['insertion_order']);g={q:{} for q in range(1000)}
   for r in rows:g[int(r['query_id'])][int(r['ef_search'])]=(float(r['recall_at_10']),float(r['exact_ndc']))
   G[k]=g
 return G
G=load();DS=sorted({k[0] for k in G});fixed={};budget={};first={};b09={};b10={}
for k,g in G.items():
 target=.95 if any(np.mean([g[int(q)][int(e)][0] for q in CAL])>=.95 for e in E) else .90;f=next((int(e) for e in E if np.mean([g[int(q)][int(e)][0] for q in CAL])>=target),512);fixed[k]=f;budget[k]={};first[k]={};b09[k]={};b10[k]={}
 for q in AUD:
  q=int(q);t=g[q][f][0]
  first[k][q]=next((int(e) for e in E if g[q][int(e)][0]>=t),1024)
  budget[k][q]=next((int(e) for e in E if all(g[q][int(x)][0]>=t for x in E[E>=e])),1024)
  b09[k][q]=next((int(e) for e in E if all(g[q][int(x)][0]>=.9 for x in E[E>=e])),1024)
  b10[k][q]=next((int(e) for e in E if all(g[q][int(x)][0]>=1 for x in E[E>=e])),1024)
def eval_budget(k,q,b):return G[k][q][min(int(b),512)][1]
def quantile_budget(values,delta):
 values=np.sort(np.asarray(values));rank=int(np.ceil((1-delta)*len(values)))-1;return int(values[max(0,min(rank,len(values)-1))])
dataset_rows=[];history_rows=[];retention_rows=[];sensitivity_rows=[];query_contrib={};details={}
for ds in DS:
 details[ds]={}
 for name,orders in groups.items():
  keys=sorted(k for k in G if k[0]==ds and k[2] in orders);aware_q=[];fixed_q=[];blind_q={d:[] for d in DELTAS};under={d:[] for d in DELTAS};censored=[]
  for q in AUD:
   q=int(q);bs=[budget[k][q] for k in keys];aware=np.mean([eval_budget(k,q,budget[k][q]) for k in keys]);fix=np.mean([eval_budget(k,q,fixed[k]) for k in keys]);aware_q.append(aware);fixed_q.append(fix);censored.append(any(x>512 for x in bs))
   for d in DELTAS:
    b=quantile_budget(bs,d);blind_q[d].append(np.mean([eval_budget(k,q,b) for k in keys]));under[d].append(np.mean([b<budget[k][q] for k in keys]))
  aware_q=np.asarray(aware_q);fixed_q=np.asarray(fixed_q);query_contrib[(ds,name)]=(np.asarray(blind_q[0])-aware_q)/aware_q
  for d in DELTAS:
   blind=np.asarray(blind_q[d]);pib=float(blind.mean()/aware_q.mean()-1);den=fixed_q.mean()-aware_q.mean();ret=float((fixed_q.mean()-blind.mean())/den) if den!=0 else float('nan');vals=[]
   for _ in range(5000):idx=RNG.integers(0,len(AUD),len(AUD));vals.append(float(blind[idx].mean()/aware_q[idx].mean()-1))
   row={'dataset':ds,'history_group':name,'delta':d,'pib':pib,'pib_ci_low':ci(vals)[0],'pib_ci_high':ci(vals)[1],'oracle_retention':ret,'oracle_loss':1-ret,'under_budget_rate':float(np.mean(under[d])),'aware_mean_ndc':float(aware_q.mean()),'blind_mean_ndc':float(blind.mean()),'fixed_mean_ndc':float(fixed_q.mean()),'right_censored_query_rate':float(np.mean(censored)),'query_p50_pib':float(np.quantile((blind-aware_q)/aware_q,.5)),'query_p95_pib':float(np.quantile((blind-aware_q)/aware_q,.95)),'query_p99_pib':float(np.quantile((blind-aware_q)/aware_q,.99))}
   dataset_rows.append(row);retention_rows.append({k:row[k] for k in ('dataset','history_group','delta','oracle_retention','oracle_loss')})
  strict=query_contrib[(ds,name)];keep=np.argsort(strict)[:int(.99*len(strict))];details[ds][name]={'strict_pib':next(r['pib'] for r in dataset_rows if r['dataset']==ds and r['history_group']==name and r['delta']==0),'strict_ci_low':next(r['pib_ci_low'] for r in dataset_rows if r['dataset']==ds and r['history_group']==name and r['delta']==0),'trimmed_top1pct_mean_contribution':float(strict[keep].mean())}
  for order in sorted(orders):
   ks=[k for k in keys if k[2]==order];a=np.mean([[eval_budget(k,int(q),budget[k][int(q)]) for k in ks] for q in AUD]);b=np.mean([[eval_budget(k,int(q),max(budget[x][int(q)] for x in keys)) for k in ks] for q in AUD]);history_rows.append({'dataset':ds,'history_group':name,'history':order,'strict_pib_using_group_blind_budget':float(b/a-1),'aware_mean_ndc':float(a),'blind_mean_ndc':float(b)})

  for target_name,target_map in [('first_quality_preserving',first),('stable_recall_0.9',b09),('stable_recall_1.0',b10)]:
   aware=np.asarray([np.mean([eval_budget(k,int(q),target_map[k][int(q)]) for k in keys]) for q in AUD]);fix=np.asarray([np.mean([eval_budget(k,int(q),fixed[k]) for k in keys]) for q in AUD])
   for d in DELTAS:
    blind=np.asarray([np.mean([eval_budget(k,int(q),quantile_budget([target_map[x][int(q)] for x in keys],d)) for k in keys]) for q in AUD]);vals=[]
    for _ in range(5000):idx=RNG.integers(0,len(AUD),len(AUD));vals.append(float(blind[idx].mean()/aware[idx].mean()-1))
    denom=fix.mean()-aware.mean();sensitivity_rows.append({'dataset':ds,'history_group':name,'target':target_name,'delta':d,'pib':float(blind.mean()/aware.mean()-1),'pib_ci_low':ci(vals)[0],'pib_ci_high':ci(vals)[1],'oracle_retention':float((fix.mean()-blind.mean())/denom) if denom else float('nan'),'right_censored_query_rate':float(np.mean([any(target_map[k][int(q)]>512 for k in keys) for q in AUD]))})

rank_rows=[];rank_summary={}
for ds in DS:
 rank_summary[ds]={}
 for name,orders in groups.items():
  keys=sorted(k for k in G if k[0]==ds and k[2] in orders);pairs=[];displacements=[]
  for i,a in enumerate(keys):
   x=np.array([math.log2(budget[a][int(q)]) for q in AUD]);rx=np.argsort(np.argsort(x))/(len(x)-1)
   for b in keys[i+1:]:
    y=np.array([math.log2(budget[b][int(q)]) for q in AUD]);ry=np.argsort(np.argsort(y))/(len(y)-1);rho=float(spearmanr(x,y).statistic);tau=float(kendalltau(x,y).statistic);disp=np.abs(rx-ry);pairs.append((rho,tau));displacements.append(disp);rank_rows.append({'dataset':ds,'history_group':name,'source':f'{a[1]}_{a[2]}','target':f'{b[1]}_{b[2]}','spearman':rho,'kendall':tau,'rank_inversion_rate':float((1-tau)/2),'mean_percentile_displacement':float(disp.mean())})
  d=np.mean(displacements,axis=0);boot=[float(d[RNG.integers(0,len(d),len(d))].mean()) for _ in range(5000)];rank_summary[ds][name]={'mean_spearman':float(np.mean([p[0] for p in pairs])),'mean_kendall':float(np.mean([p[1] for p in pairs])),'mean_percentile_displacement':float(d.mean()),'displacement_ci95':ci(boot)}

mechanism=[]
for ds in DS:
 keys=sorted(k for k in G if k[0]==ds);Y=np.array([[math.log2(budget[k][int(q)]) for k in keys] for q in AUD]);mu=Y.mean();aq=Y.mean(1,keepdims=True)-mu;bg=Y.mean(0,keepdims=True)-mu;res=Y-mu-aq-bg;omega=float(np.var(res)/(np.var(aq)+np.var(res)))
 rec=next(r for r in json.load(open(ROOT/'manifests/hardness_portability_100k/data_query_truth_manifest.json'))['datasets'] if r['dataset']==ds);qv=np.load(ROOT/rec['queries_path'])[AUD];td=np.load(ROOT/rec['truth_distances_path'])[AUD];X=np.column_stack([np.linalg.norm(qv,axis=1),td.mean(1),td.std(1),td[:,-1]/np.maximum(td[:,0],1e-30),td[:,1]-td[:,0],(td[:,-1]-td[:,0])/np.maximum(td[:,0],1e-30)]);S=Y.var(1);kf=KFold(5,shuffle=True,random_state=991);pred=np.empty(len(S));iso=np.empty(len(S));prob=np.empty(len(S));cls=S>=np.quantile(S,.8)
 for tr,te in kf.split(X):
  m=make_pipeline(StandardScaler(),Ridge(alpha=1)).fit(X[tr],S[tr]);pred[te]=m.predict(X[te]);im=IsotonicRegression(out_of_bounds='clip').fit(X[tr,3],S[tr]);iso[te]=im.predict(X[te,3]);lm=make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=2000,random_state=991)).fit(X[tr],cls[tr]);prob[te]=lm.predict_proba(X[te])[:,1]
 metas=[json.load(open(ROOT/f'results/hardness_portability_100k/{"core_raw" if k[2] in {"random","lid_ascending","lid_descending"} else "realistic_raw"}/{ds}__seed{k[1]}__{k[2]}.metadata.json')) for k in keys];GX=np.array([[m['max_level'],m['build_seconds'],m['peak_rss_bytes']] for m in metas]);gy=Y.mean(0);gpred=np.empty(len(gy));gkf=KFold(5,shuffle=True,random_state=991)
 for tr,te in gkf.split(GX):gpred[te]=make_pipeline(StandardScaler(),Ridge(alpha=1)).fit(GX[tr],gy[tr]).predict(GX[te])
 mechanism.append({'dataset':ds,'omega':omega,'geometry_ridge_oof_r2':float(r2_score(S,pred)),'geometry_ridge_spearman':float(spearmanr(S,pred).statistic),'geometry_isotonic_d10d1_oof_r2':float(r2_score(S,iso)),'sensitive_query_auroc':float(roc_auc_score(cls,prob)),'sensitive_query_auprc':float(average_precision_score(cls,prob)),'graph_global_n':len(keys),'graph_global_mean_budget_oof_r2':float(r2_score(gy,gpred)),'trace_incremental_r2':None,'trace_status':'UNAVAILABLE_NO_FROZEN_QUERY_TRACE'})

real_prev=json.load(open(ROOT/'results/hardness_portability_100k/realistic_derived/realistic_history_decision.json'));gate={};leave={}
for ds in DS:
 strict=next(r for r in dataset_rows if r['dataset']==ds and r['history_group']=='realistic' and r['delta']==0);effect=(strict['pib']>.05 or strict['oracle_loss']>.25);rank=rank_summary[ds]['realistic'];global_residual=bool(real_prev['gate_by_dataset'][ds]);trim=details[ds]['realistic']['trimmed_top1pct_mean_contribution']>0;ciok=strict['pib_ci_low']>0
 keys=sorted(k for k in G if k[0]==ds and k[2] in groups['realistic']);loo=[]
 for seed in (43,59,71):
  kk=[k for k in keys if k[1]!=seed];a=np.mean([[eval_budget(k,int(q),budget[k][int(q)]) for k in kk] for q in AUD]);b=np.mean([[eval_budget(k,int(q),max(budget[x][int(q)] for x in kk)) for k in kk] for q in AUD]);loo.append(b/a-1)
 for order in groups['realistic']:
  kk=[k for k in keys if k[2]!=order];a=np.mean([[eval_budget(k,int(q),budget[k][int(q)]) for k in kk] for q in AUD]);b=np.mean([[eval_budget(k,int(q),max(budget[x][int(q)] for x in kk)) for k in kk] for q in AUD]);loo.append(b/a-1)
 leave[ds]=min(loo);gate[ds]=bool(effect and rank['displacement_ci95'][0]>0 and global_residual and trim and ciok and min(loo)>0)
passed=sum(gate.values())>=2;status='KEEP_REBUILD_TAX_MECHANISM' if passed else ('SHRINK_TO_HARDNESS_NONPORTABILITY_MEASUREMENT' if any(details[d]['realistic']['strict_pib']>0 for d in DS) else 'STOP_REBUILD_TAX_EXTENSION')
summary={'status':status,'gate_m_pass':passed,'gate_by_dataset':gate,'leave_one_min_pib':leave,'details':details,'rank':rank_summary,'mechanism':mechanism,'source_graphs':45,'source_rows':540000,'new_hnsw_queries':0,'validation_dev_accessed':False,'formal_test_accessed':False}
def write(name,rows):
 with open(OUT/name,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
write('pib_by_dataset.csv',dataset_rows);write('pib_by_history.csv',history_rows);write('oracle_retention.csv',retention_rows);write('pib_sensitivity.csv',sensitivity_rows);write('rank_inversions.csv',rank_rows);write('mechanism_decomposition.csv',mechanism);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
