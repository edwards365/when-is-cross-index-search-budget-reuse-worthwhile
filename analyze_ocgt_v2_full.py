import csv, glob, hashlib, json, math, struct
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr, kendalltau
from sklearn.linear_model import Ridge

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-ocgt')
MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
RAW=ROOT/'results/index_conditionality/ocgt_v2/raw'; DER=ROOT/'results/index_conditionality/ocgt_v2/derived'; DER.mkdir(parents=True,exist_ok=True)
EFS=np.array([10,16,24,32,48,64,96,128,192,256,384,512]); MULT=[.75,1,1.25,1.5,2,3,4]
rng=np.random.default_rng(20260825); perm=rng.permutation(500)
splits={'train_design':sorted(map(int,perm[:250])),'calibration':sorted(map(int,perm[250:375])),'internal_audit':sorted(map(int,perm[375:]))}
(ROOT/'manifests/index_conditionality/ocgt_v2/query_split_materialization.json').write_text(json.dumps({'schema_version':1,'protocol':'OCGT-v2','seed':20260825,'rng':'numpy.random.Generator(PCG64)','permutation_sha256':hashlib.sha256(np.asarray(perm,dtype='<u4').tobytes()).hexdigest(),'splits':splits,'outcome_independent_materialization':True},indent=2)+'\n')
split_of={q:s for s,ids in splits.items() for q in ids}

def read_queries(path):
 out={}
 with open(path) as f:
  for r in csv.DictReader(f):
   q=int(r['query_id']); e=int(r['ef_search']); out.setdefault(q,{})[e]={'recall':float(r['recall_at_10']),'ndc':float(r['ndc']),'ids':tuple(map(int,r['returned_top10'].split(';'))),'visited':float(r['visited_nodes'])}
 return out
def ceil_grid(x):
 for e in EFS:
  if e>=x:return int(e)
 return 512
def stable(m,target):
 for e in EFS:
  if all(m[int(x)]['recall']>=target for x in EFS[EFS>=e]):return int(e),False
 return 1024,True
graphs={}
for p in sorted(RAW.glob('*/queries.csv')):
 run=p.parent.name; ds,seed,order=run.split('__'); graphs[(ds,int(seed.replace('seed','')),order)]=read_queries(p)

effort=[]; head=[]
quality_oracle={}; fixed_map={}
for key,g in graphs.items():
 ds,seed,order=key; cal=splits['calibration']; audit=splits['internal_audit']
 target=.95 if np.mean([g[q][512]['recall'] for q in cal])>=.95 else .9
 fixed=next((int(e) for e in EFS if np.mean([g[q][int(e)]['recall'] for q in cal])>=target),512); fixed_map[key]=fixed
 qo={}
 for q,m in g.items():
  es,cen=stable(m,.9); base=m[fixed]['recall']; eq=next((int(e) for e in EFS if e<=fixed and all(m[int(x)]['recall']>=base for x in EFS[(EFS>=e)&(EFS<=fixed)])),fixed); qo[q]=eq
  effort.append({'dataset':ds,'seed':seed,'order':order,'query_id':q,'query_split':split_of[q],'stable_ef':es,'right_censored':cen,'quality_oracle_ef':eq,'fixed_ef':fixed})
 quality_oracle[key]=qo
 f=np.mean([g[q][fixed]['ndc'] for q in audit]); o=np.mean([g[q][qo[q]]['ndc'] for q in audit]); h=(f-o)/f
 head.append({'dataset':ds,'seed':seed,'order':order,'fixed_ef':fixed,'recall_target':target,'fixed_recall':np.mean([g[q][fixed]['recall'] for q in audit]),'oracle_recall':np.mean([g[q][qo[q]]['recall'] for q in audit]),'fixed_mean_ndc':f,'oracle_mean_ndc':o,'oracle_headroom':h})

cond={}
for ds in sorted({k[0] for k in graphs}):
 keys=[k for k in graphs if k[0]==ds]; Y=np.array([[math.log2(next(x['stable_ef'] for x in effort if x['dataset']==ds and x['seed']==k[1] and x['order']==k[2] and x['query_id']==q)) for k in keys] for q in range(500)])
 centered=Y-np.median(Y,axis=0); rhos=[]; taus=[]; jacs=[]
 for i in range(len(keys)):
  for j in range(i+1,len(keys)):
   rhos.append(float(spearmanr(centered[:,i],centered[:,j]).statistic)); taus.append(float(kendalltau(centered[:,i],centered[:,j]).statistic))
   a=set(np.argsort(Y[:,i])[-50:]); b=set(np.argsort(Y[:,j])[-50:]); jacs.append(len(a&b)/len(a|b))
 alpha=Y.mean(1,keepdims=True)-Y.mean(); beta=Y.mean(0,keepdims=True)-Y.mean(); residual=Y-Y.mean()-alpha-beta
 va=float(np.var(alpha)); vg=float(np.var(beta)); vi=float(np.var(residual)); omega=vi/(va+vi) if va+vi else 0
 cond[ds]={'omega':omega,'query_variance':va,'graph_variance':vg,'interaction_variance':vi,'centered_spearman_median':float(np.nanmedian(rhos)),'kendall_median':float(np.nanmedian(taus)),'hard_top10_jaccard_median':float(np.median(jacs))}

transfer=[]
for ds in sorted({k[0] for k in graphs}):
 keys=[k for k in graphs if k[0]==ds]
 for src in keys:
  for dst in keys:
   if src==dst:continue
   gd=graphs[dst]; fixed=fixed_map[dst]; cal=splits['calibration']; audit=splits['internal_audit']; base_cal=np.mean([gd[q][fixed]['recall'] for q in cal]); chosen=4
   for a in MULT:
    rec=np.mean([gd[q][ceil_grid(a*quality_oracle[src][q])]['recall'] for q in cal])
    if rec>=base_cal-1e-12:chosen=a;break
   cost=np.mean([gd[q][ceil_grid(chosen*quality_oracle[src][q])]['ndc'] for q in audit]); fc=np.mean([gd[q][fixed]['ndc'] for q in audit]); oc=np.mean([gd[q][quality_oracle[dst][q]]['ndc'] for q in audit]); h=(fc-oc)/fc; gain=(fc-cost)/fc
   transfer.append({'dataset':ds,'source':str(src[1])+'_'+src[2],'target':str(dst[1])+'_'+dst[2],'multiplier':chosen,'recall_diff':np.mean([gd[q][ceil_grid(chosen*quality_oracle[src][q])]['recall']-gd[q][fixed]['recall'] for q in audit]),'ndc_gain':gain,'eta':gain/h if h>0 else 0,'oracle_regret':(cost-oc)/oc})

feature_cache={}
def query_features(ds):
 if ds in feature_cache:return feature_cache[ds]
 base_rec=next(x for x in json.loads((MAIN/'results/gb_mpcc/r0_inputs/manifest.json').read_text())['inputs'] if x['dataset']==ds); x=np.memmap(MAIN/base_rec['path'],dtype=np.float32,mode='r',shape=(10000,base_rec['dimensions']))
 qpath=MAIN/'results/gb_mpcc/e0/search_inputs'/f'{ds}_queries.f32bin'
 with open(qpath,'rb') as f:n,d=struct.unpack('<QQ',f.read(16));q=np.fromfile(f,np.float32,n*d).reshape(n,d)
 d100=np.empty((500,100)); xn=(x*x).sum(1)
 for s in range(0,500,50):
  z=((q[s:s+50]**2).sum(1)[:,None]+xn[None,:]-2*q[s:s+50]@x.T); d100[s:s+50]=np.sqrt(np.maximum(np.partition(z,99,axis=1)[:,:100],0))
 d100.sort(1); rk=d100[:,-1]; lid=-100/np.log(np.clip(d100/(rk[:,None]+1e-30),1e-30,1)).sum(1)
 feature_cache[ds]=np.column_stack([lid,d100[:,0],d100[:,9],d100[:,9]/(d100[:,0]+1e-9),d100.mean(1),d100.var(1)])
 return feature_cache[ds]

pred=[]
for key,g in graphs.items():
 ds,seed,order=key; y=np.log2([quality_oracle[key][q] for q in range(500)]); static=query_features(ds)
 dyn=[]
 for q in range(500):
  a=g[q][16];b=g[q][24]; inter=len(set(a['ids'])&set(b['ids'])); dyn.append([1-inter/10,inter/10,b['ndc']-a['ndc'],a['ndc'],b['ndc'],a['visited'],b['visited']])
 for name,X in [('LID_STATIC',static),('SHEAF',np.asarray(dyn))]:
  tr=splits['train_design'];ca=splits['calibration'];au=splits['internal_audit']; model=Ridge(alpha=1).fit(X[tr],y[tr]); rawp=2**model.predict(X); fixed=fixed_map[key]; basecal=np.mean([g[q][fixed]['recall'] for q in ca]); chosen=4
  for a in MULT:
   if np.mean([g[q][ceil_grid(a*rawp[q])]['recall'] for q in ca])>=basecal-1e-12:chosen=a;break
  final=[ceil_grid(chosen*rawp[q]) for q in range(500)]; fc=np.mean([g[q][fixed]['ndc'] for q in au]); pc=np.mean([(g[q][final[q]]['ndc'] if name=='LID_STATIC' else g[q][16]['ndc']+g[q][24]['ndc']+g[q][final[q]]['ndc']) for q in au]); oc=np.mean([g[q][quality_oracle[key][q]]['ndc'] for q in au]); h=(fc-oc)/fc
  pred.append({'dataset':ds,'seed':seed,'order':order,'model':name,'correlation':float(spearmanr(y[au],np.log2(np.array(final)[au])).statistic),'mae_log2':float(np.mean(np.abs(y[au]-np.log2(np.array(final)[au])))),'multiplier':chosen,'recall_diff':float(np.mean([g[q][final[q]]['recall']-g[q][fixed]['recall'] for q in au])),'ndc_gain':(fc-pc)/fc,'eta':((fc-pc)/fc)/h if h>0 else 0,'actual_probe_cost_included':name=='SHEAF'})

for name,data in [('per_query_effort.csv',effort),('oracle_headroom.csv',head),('cross_graph_transfer.csv',transfer),('predictor_summary.csv',pred)]:
 with open(DER/name,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
(DER/'variance_components.json').write_text(json.dumps(cond,indent=2)+'\n')
summary={'oracle_headroom_by_dataset':{ds:float(np.mean([x['oracle_headroom'] for x in head if x['dataset']==ds])) for ds in cond},'conditionality':cond,'transfer_eta_by_dataset':{ds:float(np.median([x['eta'] for x in transfer if x['dataset']==ds])) for ds in cond},'predictors':{ds:{m:{'corr':float(np.nanmedian([x['correlation'] for x in pred if x['dataset']==ds and x['model']==m])),'ndc_gain':float(np.mean([x['ndc_gain'] for x in pred if x['dataset']==ds and x['model']==m])),'recall_diff':float(np.mean([x['recall_diff'] for x in pred if x['dataset']==ds and x['model']==m]))} for m in ['LID_STATIC','SHEAF']} for ds in cond}}
(DER/'full_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
