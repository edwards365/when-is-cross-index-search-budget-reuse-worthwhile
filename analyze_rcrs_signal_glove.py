#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs')
INP = ROOT / 'results/rcrs_signal/glove'
OUT = ROOT / 'results/rcrs_signal'
FEATURES = ['checkpoint','topk_churn','kth_distance_improvement','frontier_kth_gap',
            'candidate_queue_size','top_candidates_size','new_visited','ndc']
SPLITS = {
    'design': (7, 0, 256),
    'calibration': (17, 256, 512),
    'design_eval': (29, 512, 768),
}
ALPHA_FAMILY = 0.05
M = 16

def load(seed, lo, hi):
    t = pd.read_csv(INP / f'seed{seed}_trace.csv')
    e = pd.read_csv(INP / f'seed{seed}_equivalence.csv')
    return t[(t.query_id >= lo) & (t.query_id < hi)].copy(), e[(e.query_id >= lo) & (e.query_id < hi)].copy()

def cp_upper(failures, n, alpha):
    return 1.0 if failures == n else float(beta.ppf(1-alpha, failures+1, n-failures))

data = {k: load(*v) for k, v in SPLITS.items()}
design_t, _ = data['design']
model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, random_state=991, max_iter=2000))
model.fit(design_t[FEATURES], design_t.safe_label)
design_scores = model.predict_proba(design_t[FEATURES])[:, 1]
thresholds = np.unique(np.quantile(design_scores, np.linspace(0, 1, M)))

def evaluate(name, threshold):
    t, e = data[name]
    t = t.copy(); t['score'] = model.predict_proba(t[FEATURES])[:, 1]
    chosen = t[t.score >= threshold].sort_values(['query_id','checkpoint']).groupby('query_id').first()
    rows=[]
    for _, fixed in e.iterrows():
        q=int(fixed.query_id)
        if q in chosen.index:
            x=chosen.loc[q]; recall=float(x.recall_at_10); ndc=float(x.ndc); stopped=1
        else:
            recall=float(fixed.fixed_recall); ndc=float(fixed.native_ndc); stopped=0
        rows.append((q, recall, ndc, stopped, float(fixed.fixed_recall), float(fixed.native_ndc)))
    p=pd.DataFrame(rows,columns=['query_id','recall','ndc','stopped','fixed_recall','fixed_ndc'])
    failures=int((p.recall < .9).sum()); n=len(p)
    return p, {'split':name,'threshold':float(threshold),'n':n,'failures':failures,
      'failure_rate':failures/n,'bonferroni_cp_upper':cp_upper(failures,n,ALPHA_FAMILY/len(thresholds)),
      'stop_coverage':float(p.stopped.mean()),'mean_recall':float(p.recall.mean()),
      'fixed_mean_recall':float(p.fixed_recall.mean()),'recall_difference':float((p.recall-p.fixed_recall).mean()),
      'mean_ndc':float(p.ndc.mean()),'fixed_mean_ndc':float(p.fixed_ndc.mean()),
      'gross_ndc_gain':float(1-p.ndc.mean()/p.fixed_ndc.mean())}

cal=[]
for th in thresholds:
    _, s=evaluate('calibration',th); cal.append(s)
cal_df=pd.DataFrame(cal)
safe=cal_df[cal_df.bonferroni_cp_upper <= .05]
selected=float(safe.sort_values(['mean_ndc','threshold'],ascending=[True,False]).iloc[0].threshold) if len(safe) else float(np.max(thresholds)+1.0)
eval_rows, eval_summary=evaluate('design_eval',selected)
cal_rows, cal_summary=evaluate('calibration',selected)
decision='RCRS_SIGNAL_EXISTS_NEEDS_MORE_CALIBRATION' if len(safe) and eval_summary['recall_difference'] >= -.001 and eval_summary['gross_ndc_gain'] > 0 else 'STOP_RCRS_NO_CERTIFIED_STOPPING_SIGNAL'
cal_df.to_csv(OUT/'glove_threshold_calibration.csv',index=False)
eval_rows.to_csv(OUT/'glove_design_eval_per_query.csv',index=False)
summary={'scope':'MINIMAL_CROSS_REBUILD_SEED_PILOT','model':'L2 logistic C=1 seed=991',
 'candidate_threshold_count':int(len(thresholds)),'bonferroni_family_alpha':ALPHA_FAMILY,
 'certified_candidate_count':int(len(safe)),'selected_policy':'learned_stop' if len(safe) else 'fixed_e0_fallback',
 'selected_threshold':selected if len(safe) else None,'calibration':cal_summary,'design_eval':eval_summary,
 'decision':decision,'cross_history_confirmation':False,'validation_dev_accessed':False,'formal_test_accessed':False}
(OUT/'glove_signal_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
