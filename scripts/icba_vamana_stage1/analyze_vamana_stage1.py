from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/home/wlk/data500/icba_vamana_stage1'); DATASET=sys.argv[2] if len(sys.argv)>2 else 'SIFT-100K'; GRID=np.array([16,32,64,128,256,512]); NQ=750
builds=[]
for i in range(1,13):
    p=ROOT/f'builds/V{i:02d}/run_report.json'; x=json.loads(p.read_text())[0]
    rs=x['results']['search']['Topk']; assert len(rs)==6
    recalls=np.array([r['query_recalls'] for r in rs]).T
    cmps=np.array([r['query_cmps'] for r in rs]).T
    hops=np.array([r['query_hops'] for r in rs]).T
    assert recalls.shape==(NQ,6)
    finite=recalls>=.95; first=np.argmax(finite,axis=1); ok=finite.any(1)
    b=np.where(ok,GRID[first],-1)
    builds.append({'id':f'V{i:02d}','recall':recalls,'cmps':cmps,'hops':hops,'B':b,'index_sha256':hashlib.sha256((ROOT/f'builds/V{i:02d}/index').read_bytes()).hexdigest(),
                   'build_seconds':x['results']['build']['total_time']/1e6})

B=np.stack([x['B'] for x in builds],axis=1)
all_finite=(B>0).all(1); any2=(B>0).sum(1)>=2
cat_change=np.array([len(set(row.tolist()))>1 for row in B])
diam_all=np.array([row.max()-row.min() if ok else np.nan for row,ok in zip(B,all_finite)])
diam_two=np.array([(row[row>0].max()-row[row>0].min()) if ok else np.nan for row,ok in zip(B,any2)])
mixed=((B>0).any(1)&~(B>0).all(1)); all_cens=(B<0).all(1)

rows=[]
for si in range(6):
  for ti in range(6,12):
    s,t=builds[si],builds[ti]
    raw_nonmono=(np.diff(t['recall'],axis=1)<0).any(1)
    for q in range(NQ):
      bs,bt=int(s['B'][q]),int(t['B'][q]); sf=bs>0; tf=bt>0
      if not sf and not tf: event='BOTH_RIGHT_CENSORED'; transport_safe=False; ctrans=np.nan; cref=np.nan
      elif not sf: event='SOURCE_ONLY_RIGHT_CENSORED'; transport_safe=False; ctrans=np.nan; cref=float(t['cmps'][q,np.where(GRID==bt)[0][0]])
      elif not tf:
        j=np.where(GRID==bs)[0][0]; transport_safe=t['recall'][q,j]>=.95; event='TARGET_ONLY_RIGHT_CENSORED'; ctrans=float(t['cmps'][q,j]); cref=np.nan
      else:
        j=np.where(GRID==bs)[0][0]; k=np.where(GRID==bt)[0][0]; transport_safe=t['recall'][q,j]>=.95
        if bs<bt: event='UNDER_BUDGET_UNSAFE' if not transport_safe else 'EXACT_BUDGET_SAFE'
        elif bs==bt: event='EXACT_BUDGET_SAFE' if transport_safe else 'OVER_BUDGET_UNSAFE'
        else: event='OVER_BUDGET_SAFE' if transport_safe else 'OVER_BUDGET_UNSAFE'
        ctrans=float(t['cmps'][q,j]); cref=float(t['cmps'][q,k])
      rows.append((q,s['id'],t['id'],bs,bt,event,int(not transport_safe),int(raw_nonmono[q]),ctrans,cref))

dtype=[('q','i4'),('source','U3'),('target','U3'),('bs','i4'),('bt','i4'),('event','U28'),('risk','i1'),('raw_nonmono','i1'),('ctrans','f8'),('cref','f8')]
A=np.array(rows,dtype=dtype)
def est(idx=None,mask=None):
  z=A if idx is None else A[np.isin(A['q'],idx)]
  if mask is not None: z=z[mask(z)]
  valid=np.isfinite(z['ctrans'])&np.isfinite(z['cref'])
  ratio=z['ctrans'][valid].mean()/z['cref'][valid].mean()-1 if valid.any() else np.nan
  return {'transport_risk':float(z['risk'].mean()),'delta_risk':float(z['risk'].mean()),'cost_tax_ratio_of_means':float(ratio),
          'category_change_rate':float(cat_change[np.unique(z['q'])].mean())}
point=est()
rng=np.random.default_rng(991); boot=np.empty((5000,4))
for b in range(5000):
  ids=rng.integers(0,NQ,NQ); counts=np.bincount(ids,minlength=NQ); w=counts[A['q']]
  valid=np.isfinite(A['ctrans'])&np.isfinite(A['cref'])
  risk=np.average(A['risk'],weights=w)
  tax=np.average(A['ctrans'][valid],weights=w[valid])/np.average(A['cref'][valid],weights=w[valid])-1
  cc=np.average(cat_change,weights=counts)
  da=np.average(np.nan_to_num(diam_all,nan=0),weights=counts)
  boot[b]=risk,risk,tax,cc
ci={k:[float(np.quantile(boot[:,j],.025)),float(np.quantile(boot[:,j],.975))] for j,k in enumerate(('transport_risk','delta_risk','cost_tax_ratio_of_means','category_change_rate'))}

events={e:float((A['event']==e).mean()) for e in ('BOTH_RIGHT_CENSORED','SOURCE_ONLY_RIGHT_CENSORED','TARGET_ONLY_RIGHT_CENSORED','UNDER_BUDGET_UNSAFE','EXACT_BUDGET_SAFE','OVER_BUDGET_SAFE','OVER_BUDGET_UNSAFE')}
lobo=[]
for bid in [f'V{i:02d}' for i in range(1,13)]:
  z=A[(A['source']!=bid)&(A['target']!=bid)]; valid=np.isfinite(z['ctrans'])&np.isfinite(z['cref'])
  lobo.append({'omitted_build':bid,'transport_risk':float(z['risk'].mean()),'cost_tax':float(z['ctrans'][valid].mean()/z['cref'][valid].mean()-1)})
# Query contribution deletion diagnostics.
qrisk=np.array([A['risk'][A['q']==q].mean() for q in range(NQ)])
qcost=np.array([np.nanmean(A['ctrans'][A['q']==q]-A['cref'][A['q']==q]) for q in range(NQ)])
drop_risk=set(np.argsort(qrisk)[-max(1,int(.01*NQ)):]); drop_cost=set(np.argsort(np.nan_to_num(qcost,nan=-np.inf))[-max(1,int(.01*NQ)):])
keep_r=np.array([q not in drop_risk for q in A['q']]); keep_c=np.array([q not in drop_cost for q in A['q']])
def zpoint(z):
 v=np.isfinite(z['ctrans'])&np.isfinite(z['cref']); return {'risk':float(z['risk'].mean()),'cost_tax':float(z['ctrans'][v].mean()/z['cref'][v].mean()-1)}
rob={'drop_top1pct_risk':zpoint(A[keep_r]),'drop_top1pct_cost':zpoint(A[keep_c]),'lobo':lobo,
     'raw_nonmonotone_rate':float(A['raw_nonmono'].mean())}
summary={'dataset':DATASET,'queries':NQ,'builds':12,'primary_pairs':36,'category_change_rate':float(cat_change.mean()),
 'jointly_feasible_budget_inconsistency_rate':float(((diam_all>0)&all_finite).mean()),
 'all_finite_rate':float(all_finite.mean()),'mixed_finite_censored_rate':float(mixed.mean()),'all_censored_rate':float(all_cens.mean()),
 'mean_diameter_all':float(np.nanmean(diam_all)),'mean_diameter_at_least_two':float(np.nanmean(diam_two)),**point,'bootstrap95':ci,
 'events':events,'robustness':rob}
summary['detection_gate']=bool(summary['category_change_rate']>0 and ci['category_change_rate'][0]>0 and min(x['transport_risk'] for x in lobo)>=0 and rob['drop_top1pct_risk']['risk']>=0)
summary['materiality_gate']=bool((summary['category_change_rate']>=.10 or summary['jointly_feasible_budget_inconsistency_rate']>=.05) and (summary['delta_risk']>=.02 or summary['cost_tax_ratio_of_means']>=.03))
(ROOT/'analysis').mkdir(exist_ok=True)
(ROOT/'analysis/sift_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (ROOT/'analysis/events.csv').open('w',newline='') as f:
 w=csv.writer(f); w.writerow(A.dtype.names); w.writerows(A.tolist())
with (ROOT/'analysis/lobo.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=lobo[0]); w.writeheader(); w.writerows(lobo)
np.savez_compressed(ROOT/'analysis/bootstrap.npz',samples=boot)
print(json.dumps(summary,indent=2))
