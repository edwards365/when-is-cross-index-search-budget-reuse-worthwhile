#!/usr/bin/env python3
import csv,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs');OUT=ROOT/'results/rcrs_signal'
df=pd.read_csv(OUT/'sift_trace_labels.csv');eq=pd.read_csv(OUT/'sift_prefix_equivalence.csv').set_index('query_id');features=['topk_churn','kth_distance_improvement','frontier_kth_gap','candidate_queue_size','new_visited','ndc'];y=df.safe_label.values;X=df[features].replace([np.inf,-np.inf],np.nan)
if len(df)!=1500 or df.groupby('query_id').size().ne(3).any():raise RuntimeError('trace grouping failure')
if X.isna().any().any():raise RuntimeError('nonfinite feature')
metrics=[]
for f in features:
 a=roc_auc_score(y,X[f]);metrics.append({'model':f,'auroc':max(a,1-a),'auprc':max(average_precision_score(y,X[f]),average_precision_score(y,-X[f])),'safe_rate':y.mean(),'rows':len(y),'grouped_cv':False})
oof=np.zeros(len(df));cv=GroupKFold(5)
for tr,te in cv.split(X,y,groups=df.query_id):
 m=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=1,random_state=991,max_iter=1000))]);m.fit(X.iloc[tr],y[tr]);oof[te]=m.predict_proba(X.iloc[te])[:,1]
metrics.append({'model':'L2_logistic_C1','auroc':roc_auc_score(y,oof),'auprc':average_precision_score(y,oof),'safe_rate':y.mean(),'rows':len(y),'grouped_cv':True})
df['score']=oof;curve=[]
for quant in np.linspace(0,1,17):
 th=float(np.quantile(oof,quant));stops=[]
 for q,g in df.groupby('query_id'):
  g=g.sort_values('checkpoint');hit=g[g.score>=th];r=hit.iloc[0] if len(hit) else None;fixed=float(eq.loc[q].native_ndc)
  stops.append((r is not None,False if r is None else not bool(r.safe_label),fixed if r is None else float(r.ndc),fixed))
 a=np.asarray(stops,float);curve.append({'threshold_quantile':quant,'threshold':th,'stop_coverage':a[:,0].mean(),'under_target_rate':a[:,1].mean(),'mean_ndc':a[:,2].mean(),'fixed_mean_ndc':a[:,3].mean(),'gross_ndc_gain':1-a[:,2].mean()/a[:,3].mean()})
with open(OUT/'sift_signal_metrics.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=metrics[0].keys());w.writeheader();w.writerows(metrics)
pd.DataFrame(curve).to_csv(OUT/'sift_coverage_risk.csv',index=False)
best=max((r for r in curve if r['under_target_rate']<=.05),key=lambda r:r['stop_coverage'],default=None)
(OUT/'sift_signal_summary.json').write_text(json.dumps({'logistic_auroc':metrics[-1]['auroc'],'logistic_auprc':metrics[-1]['auprc'],'best_empirical_risk_le_5pct':best,'evidence':'SIFT_DESIGN_GROUPED_CROSSFIT','online_features_exclude_truth':True},indent=2)+'\n')
print((OUT/'sift_signal_summary.json').read_text())
