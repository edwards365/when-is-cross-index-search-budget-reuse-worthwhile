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
rows=[];b5=[]
for dataset in DATASETS:
    paths=sorted(glob.glob(os.path.join(ROOT,'results/cross_index/g1/main/hnswlib',f'{dataset}__*.csv.gz')))
    builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths}
    sentinel=sorted(map(int,SPLIT['datasets'][dataset]['sentinel_query_ids'])); evaluation=sorted(map(int,SPLIT['datasets'][dataset]['evaluation_query_ids']))
    for tname,(td,tb,tq,tX,ty,tc,tndc) in builds.items():
        first=td[td.ef_search.astype(int)==tb[0]].sort_values('query_id'); design=set(first[first.query_split=='cross_index_design'].query_id.astype(int)); confirm=set(first[first.query_split=='cross_index_confirm'].query_id.astype(int))
        train_overlap=len(design&set(evaluation)); confirm_overlap=len(confirm&set(evaluation))
        b5.append({'dataset':dataset,'target_build':tname,'status':'TARGET_RETRAIN_BASELINE_NOT_ESTIMABLE','reason':'target design/confirm query IDs overlap target evaluation IDs','target_design_count':len(design),'target_confirm_count':len(confirm),'target_evaluation_count':len(evaluation),'design_evaluation_overlap':train_overlap,'confirm_evaluation_overlap':confirm_overlap,'target_evaluation_used':False,'evidence_label':'PAIRED_QUERY_REPLAY_NOT_NEW_QUERY_GENERALIZATION'})
    for sname,(sd,sb,sq,sX,sy,sc,sndc) in builds.items():
        first=sd[sd.ef_search.astype(int)==sb[0]].sort_values('query_id'); design=first.query_split.to_numpy()=='cross_index_design'; confirm=first.query_split.to_numpy()=='cross_index_confirm'
        model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty='l2',solver='lbfgs',max_iter=1000,random_state=SEED));model.fit(sX[design],sy[design]); raw=model.predict(sX).astype(int); source_shift=int(max(0,np.max(sy[confirm]-raw[confirm])))
        for tname,(td,b,q,X,y,c,ndc) in builds.items():
            if sname==tname:continue
            pos={int(v):i for i,v in enumerate(q)}; sidx=np.asarray([pos[v] for v in sentinel]); eidx=np.asarray([pos[v] for v in evaluation]); shift=int(max(0,np.max(y[sidx]-raw[sidx])))
            a1=np.minimum(raw+source_shift,len(b)-1);a2=np.minimum(raw+shift,len(b)-1)
            c1=np.asarray([ndc[(int(q[i]),b[int(a1[i])])] for i in eidx]);c2=np.asarray([ndc[(int(q[i]),b[int(a2[i])])] for i in eidx]); benefit=c1-c2
            drop=np.argsort(-benefit)[:math.ceil(.01*len(eidx))]; keep=np.ones(len(eidx),bool);keep[drop]=False; idx=eidx[keep]
            f=int(np.sum((a2[idx]<y[idx])|c[idx])); n=len(idx); n1=float(np.mean([ndc[(int(q[i]),b[int(a1[i])])] for i in idx])); n2=float(np.mean([ndc[(int(q[i]),b[int(a2[i])])] for i in idx]))
            rows.append({'method':'B2','dataset':dataset,'source_build':sname,'target_build':tname,'k':256,'removed_queries':int((~keep).sum()),'remaining_queries':n,'target_shift_levels':shift,'source_shift_levels':source_shift,'underbudget_count':f,'risk':f/n,'cp95_upper':cp(f,n),'gate_s':'PASS' if cp(f,n)<=.05 else 'FAIL','b1_mean_ndc_after_removal':n1,'b2_mean_ndc_after_removal':n2,'ndc_saving_vs_b1_after_removal':1-n2/n1,'direction_improves':n2<n1-1e-12,'outer_label':'OUTER_BUILD_NOT_CERTIFIED','evidence_label':'PAIRED_QUERY_REPLAY_NOT_NEW_QUERY_GENERALIZATION'})
pd.DataFrame(rows).to_csv(os.path.join(OUT,'top1_deletion.csv'),index=False);pd.DataFrame(b5).to_csv(os.path.join(OUT,'b5_target_retrain.csv'),index=False)
print('TOP1',len(rows),sum(r['gate_s']=='PASS' for r in rows),sum(r['direction_improves'] for r in rows));print(pd.DataFrame(b5).groupby('dataset').agg(builds=('status','size'),design_overlap=('design_evaluation_overlap','sum'),confirm_overlap=('confirm_evaluation_overlap','sum')).to_string())
