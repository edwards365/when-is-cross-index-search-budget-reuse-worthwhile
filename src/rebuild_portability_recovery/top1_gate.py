#!/usr/bin/env python3
import glob, os, sys
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
sys.path.insert(0,os.path.dirname(__file__))
from m0_m1 import load, cp, DATASETS, SEED

root=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
rows=[]
for dataset in DATASETS:
    paths=sorted(glob.glob(os.path.join(root,"results/cross_index/g1/main/hnswlib",f"{dataset}__*.csv.gz")))
    loaded={os.path.basename(p).replace(".csv.gz",""):load(p) for p in paths}
    models={}
    for name,(d,b,q,X,y,c,ndc) in loaded.items():
        split=d[d.ef_search.astype(int)==b[0]].sort_values("query_id").query_split.to_numpy()
        train=split=="cross_index_design"; confirm=split=="cross_index_confirm"
        model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty="l2",solver="lbfgs",max_iter=1000,random_state=SEED))
        model.fit(X[train],y[train])
        raw=model.predict(X[confirm]).astype(int)
        shift=int(max(0,np.max(y[confirm]-raw)))
        models[name]=(model,shift)
    import json
    split=json.load(open(os.path.join(root,"manifests/icba_micro_closure_query_split.json")))
    evaluation=sorted(map(int,split["datasets"][dataset]["evaluation_query_ids"]))
    for sname,(model,shift) in models.items():
        for tname,(d,b,q,X,y,c,ndc) in loaded.items():
            if sname==tname: continue
            pred=np.minimum(model.predict(X).astype(int)+shift,len(b)-1)
            pos={int(x):i for i,x in enumerate(q)}
            idx=np.asarray([pos[x] for x in evaluation])
            fail=((pred[idx]<y[idx])|c[idx])
            online=np.asarray([ndc[(int(q[i]),b[int(pred[i])])] for i in idx])
            fixed=np.asarray([ndc[(int(q[i]),b[-1])] for i in idx])
            gain=fixed-online
            drop=max(1,int(np.ceil(.01*len(idx))))
            keep=np.ones(len(idx),dtype=bool)
            keep[np.argsort(gain)[-drop:]]=False
            f=int(fail[keep].sum()); n=int(keep.sum())
            saving=1-float(online[keep].mean()/fixed[keep].mean())
            rows.append({"dataset":dataset,"source_build":sname,"target_build":tname,
                         "n_before":len(idx),"n_after":n,"dropped":drop,
                         "drop_rule":"largest per-query fixed-minus-M0 NDC gain",
                         "underbudget_after":f,"risk_after":f/n,"cp95_upper_after":cp(f,n),
                         "ndc_saving_after":saving,
                         "safety_direction_holds":cp(f,n)<=.05,
                         "gain_direction_holds":saving>0,
                         "top1_gate":"PASS" if cp(f,n)<=.05 and saving>0 else "FAIL",
                         "evidence_label":"EXPLORATORY_DESIGN_SIMULATION"})
out=pd.DataFrame(rows)
out.to_csv(os.path.join(root,"results/rebuild_portability_recovery/top1_deletion.csv"),index=False)
print(out.groupby("dataset").agg(pairs=("top1_gate","size"),pass_pairs=("top1_gate",lambda x:(x=="PASS").sum()),
 max_cp=("cp95_upper_after","max"),min_saving=("ndc_saving_after","min"),median_saving=("ndc_saving_after","median")).to_string())
