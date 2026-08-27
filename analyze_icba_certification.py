#!/usr/bin/env python3
import csv, json
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score
from icba_theory import certification_k, certification_power

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs')
OUT=ROOT/'results/theory_generalization';OUT.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(991); alpha=delta=.05; reps=100000
rows=[]
for n in (64,128,256,512,1024):
 for m in (1,4,16):
  k=certification_k(n,m,alpha,delta)
  for p in (.01,.02,.028,.03,.05):
   exact=certification_power(n,m,alpha,delta,p)
   mc=float((rng.binomial(n,p,reps)<=k).mean())
   rows.append((n,m,p,k,exact,mc,mc-exact))
with (OUT/'certification_power.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['n','M','true_failure_rate','k_star','exact_certification_probability','monte_carlo_probability','mc_minus_exact']);w.writerows(rows)

# Continuous-score examples: equal ranking quality does not determine calibrated threshold risk.
n=20000; y=rng.binomial(1,.9,n) # 1=safe
latent=rng.normal(np.where(y==1,1.5,0.0),1.0)
score_a=1/(1+np.exp(-latent)); score_b=score_a**4
gap=[]
for name,score in [('A',score_a),('B_monotone_transform',score_b)]:
 stop=score>=.7
 gap.append({'model':name,'auroc':float(roc_auc_score(y,score)),'auprc':float(average_precision_score(y,score)),
  'threshold':.7,'stop_rate':float(stop.mean()),'unsafe_given_stop':float((y[stop]==0).mean()) if stop.any() else None})
(OUT/'signal_certification_simulation.json').write_text(json.dumps({'seed':991,'n':n,'models':gap},indent=2)+'\n')
print(json.dumps({'rows':len(rows),'preregistered_k_star':certification_k(256,16,.05,.05),'signal_gap':gap},indent=2))
