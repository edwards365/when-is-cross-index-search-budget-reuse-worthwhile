#!/usr/bin/env python3
import glob,json,math,os,sys
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
sys.path.insert(0,os.path.join(ROOT,'src/rebuild_portability_recovery'))
from m0_m1 import load,cp,DATASETS,SEED
OUT=os.path.join(ROOT,'results/icba_positive_recovery');os.makedirs(OUT,exist_ok=True)
SPLIT=json.load(open(os.path.join(ROOT,'manifests/icba_micro_closure_query_split.json')))
REPS=500

def metrics(raw,y,c,ndc,q,b,eidx,shift):
    alloc=np.minimum(raw+shift,len(b)-1)
    fail=int(np.sum((alloc[eidx]<y[eidx])|c[eidx])); n=len(eidx)
    costs=np.asarray([ndc[(int(q[i]),b[int(alloc[i])])] for i in eidx],float)
    endpoint=float(np.mean(alloc[eidx]==len(b)-1))
    return fail/n,cp(fail,n),float(costs.mean()),float(np.quantile(costs,.95)),endpoint,fail

b0=[];b1=[];b2=[]
for dataset in DATASETS:
    paths=sorted(glob.glob(os.path.join(ROOT,'results/cross_index/g1/main/hnswlib',f'{dataset}__*.csv.gz')))
    builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths}
    models={}
    for name,(d,b,q,X,y,c,ndc) in builds.items():
        first=d[d.ef_search.astype(int)==b[0]].sort_values('query_id')
        design=first.query_split.to_numpy()=='cross_index_design'
        confirm=first.query_split.to_numpy()=='cross_index_confirm'
        model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty='l2',solver='lbfgs',max_iter=1000,random_state=SEED))
        model.fit(X[design],y[design])
        raw=model.predict(X).astype(int)
        source_shift=int(max(0,np.max(y[confirm]-raw[confirm])))
        models[name]=(raw,source_shift)
    sentinel=sorted(map(int,SPLIT['datasets'][dataset]['sentinel_query_ids']))
    evaluation=sorted(map(int,SPLIT['datasets'][dataset]['evaluation_query_ids']))
    assert len(sentinel)==256 and len(evaluation)==744 and not set(sentinel)&set(evaluation)
    for sname,(raw,source_shift) in models.items():
        for tname,(d,b,q,X,y,c,ndc) in builds.items():
            if sname==tname: continue
            pos={int(x):i for i,x in enumerate(q)}; sidx=np.asarray([pos[x] for x in sentinel]); eidx=np.asarray([pos[x] for x in evaluation])
            ndcf=float(np.mean([ndc[(int(q[i]),b[-1])] for i in eidx]))
            grid=[metrics(raw,y,c,ndc,q,b,eidx,sh) for sh in range(len(b))]
            r0,u0,n0,p0,e0,f0=grid[0]; r1,u1,n1,p1,e1,f1=grid[min(source_shift,len(b)-1)]
            common={'dataset':dataset,'source_build':sname,'target_build':tname,'n_eval':len(eidx),'fixed_safe_mean_ndc':ndcf,'source_shift_levels':source_shift,'evidence_label':'PAIRED_QUERY_REPLAY_NOT_NEW_QUERY_GENERALIZATION'}
            b0.append(dict(common,method='B0',shift_levels=0,underbudget=f0,risk=r0,cp95_upper=u0,mean_ndc=n0,p95_ndc=p0,ndc_saving_vs_fixed=1-n0/ndcf,endpoint_fraction=e0,gate_s='PASS' if u0<=.05 else 'FAIL'))
            b1.append(dict(common,method='B1',shift_levels=source_shift,underbudget=f1,risk=r1,cp95_upper=u1,mean_ndc=n1,p95_ndc=p1,ndc_saving_vs_fixed=1-n1/ndcf,endpoint_fraction=e1,gate_s='PASS' if u1<=.05 else 'FAIL'))
            pairseed=SEED+sum(ord(z) for z in sname+'|'+tname)
            for k in (32,64,128,256):
                rng=np.random.default_rng(pairseed+k); shifts=[]
                for rep in range(REPS):
                    si=sidx if k==256 else rng.choice(sidx,size=k,replace=False)
                    shifts.append(int(np.clip(max(0,np.max(y[si]-raw[si])),0,len(b)-1)))
                risks=[];ups=[];means=[];p95s=[];ends=[];fails=[]
                for sh in shifts:
                    rr,uu,nn,pp,ee,ff=grid[sh];risks.append(rr);ups.append(uu);means.append(nn);p95s.append(pp);ends.append(ee);fails.append(ff)
                b2.append({'method':'B2','dataset':dataset,'source_build':sname,'target_build':tname,'k':k,'reps':REPS,'n_eval':len(eidx),
                 'underbudget_count_mean':float(np.mean(fails)),'empirical_risk_mean':float(np.mean(risks)),'empirical_risk_p95':float(np.quantile(risks,.95)),
                 'cp95_upper_mean':float(np.mean(ups)),'cp95_upper_p95':float(np.quantile(ups,.95)),'gate_s_pass_fraction':float(np.mean(np.asarray(ups)<=.05)),
                 'mean_ndc':float(np.mean(means)),'p95_ndc':float(np.mean(p95s)),'fixed_safe_mean_ndc':ndcf,'ndc_saving_vs_fixed':float(1-np.mean(means)/ndcf),
                 'b1_mean_ndc':n1,'ndc_saving_vs_b1':float(1-np.mean(means)/n1),'target_shift_mean':float(np.mean(shifts)),'target_shift_p95':float(np.quantile(shifts,.95)),
                 'source_shift_levels':source_shift,'endpoint_fraction':float(np.mean(ends)),'fallback_rate':0.,'sentinel_truth_count':k,
                 'marginal_label':'MARGINAL_CONFORMAL_ELIGIBLE','pac_label':'PAC_FIXED_TARGET_ELIGIBLE' if k>=59 else 'PAC_FIXED_TARGET_INELIGIBLE',
                 'evaluation_label':'EX_POST_EVALUATION_PASS' if np.quantile(ups,.95)<=.05 else 'EX_POST_EVALUATION_FAIL','outer_label':'OUTER_BUILD_NOT_CERTIFIED',
                 'gate_s':'PASS' if np.quantile(ups,.95)<=.05 else 'FAIL','seed':SEED,'used_source_shift':False,'used_history_donors':False,'used_target_evaluation_for_calibration':False,
                 'evidence_label':'PAIRED_QUERY_REPLAY_NOT_NEW_QUERY_GENERALIZATION'})

pd.DataFrame(b0).to_csv(os.path.join(OUT,'b0_raw.csv'),index=False)
pd.DataFrame(b1).to_csv(os.path.join(OUT,'b1_source_robust.csv'),index=False)
pd.DataFrame(b2).to_csv(os.path.join(OUT,'b2_true_target_only.csv'),index=False)
summary=pd.DataFrame(b2).groupby(['dataset','k']).agg(pairs=('gate_s','size'),pass_pairs=('gate_s',lambda x:(x=='PASS').sum()),median_saving_fixed=('ndc_saving_vs_fixed','median'),median_saving_b1=('ndc_saving_vs_b1','median'),min_saving_b1=('ndc_saving_vs_b1','min'),median_shift=('target_shift_mean','median'),max_cp=('cp95_upper_p95','max')).reset_index()
summary.to_csv(os.path.join(OUT,'b2_summary.csv'),index=False);print(summary.to_string(index=False))
