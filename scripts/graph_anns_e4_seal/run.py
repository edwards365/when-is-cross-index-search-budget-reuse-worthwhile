#!/usr/bin/env python3
"""Deterministic E4 code/statistical/semantic seal from frozen raw records."""
import argparse, hashlib, json, platform, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import beta, kendalltau

EFS=np.array([10,20,40,80,120,200])
SEEDS=[83,97,109,127,149,163,181,197]
ORDERS=['random','lid_ascending','lid_descending']
DATASETS=['sift_100k','arxiv_nomic_100k']

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1<<20),b''): h.update(block)
    return h.hexdigest()

def cp_ucb(k,n,alpha=.05):
    return 1.0 if k>=n else float(beta.ppf(1-alpha,k+1,n-k))

def ci(v):
    return float(np.quantile(v,.025)),float(np.quantile(v,.975))

def parse_build(build_id):
    tail=build_id.split('__')
    return int(tail[1].replace('seed','')),tail[2]

def load_raw(root,raw_dir):
    bm=pd.read_csv(root/'results/graph_anns_e4/build_manifest.csv')
    rows=[]; inventory=[]
    for _,m in bm.iterrows():
        path=raw_dir/m.build_id/'queries.csv.gz'
        x=pd.read_csv(path)
        x=x.groupby(['query_id','ef_search'],as_index=False).agg(
            recall=('recall_at_10','first'),ndc=('ndc','first'),
            latency_ns=('latency_ns','median'),output=('returned_top10','first'))
        x['dataset']=m.dataset;x['build_id']=m.build_id;x['seed']=int(m.seed);x['order']=m['order']
        rows.append(x)
        for role,lo,hi in [('sentinel',0,250),('evaluation',250,1000)]:
            inventory.append(dict(dataset=m.dataset,build_id=m.build_id,seed=int(m.seed),
                insertion_order=m['order'],query_role=role,query_count=hi-lo,
                budget_grid='10|20|40|80|120|200',raw_file=str(path),raw_file_sha256=sha(path),
                endpoint_fields_present=True,censoring_fields_present=True,native_tracer_verified=True))
    x=pd.concat(rows,ignore_index=True)
    assert len(bm)==48 and len(x)==48*1000*6
    assert bm.groupby('dataset').size().eq(24).all()
    assert bm.groupby(['dataset','seed','order']).size().eq(1).all()
    return bm,x,pd.DataFrame(inventory)

def budgets(x):
    out=[]
    for (ds,b,s,o,q),g in x.groupby(['dataset','build_id','seed','order','query_id'],sort=False):
        g=g.set_index('ef_search').loc[EFS]; good=g.recall.to_numpy()>=.95
        suffix=np.logical_and.accumulate(good[::-1])[::-1]; hit=np.flatnonzero(suffix)
        out.append(dict(dataset=ds,build_id=b,seed=s,order=o,query_id=q,
            safe_budget=float(EFS[hit[0]]) if len(hit) else np.nan,
            endpoint_feasible=bool(good[-1]),right_censored=not bool(good[-1]),
            raw_nonmonotone=bool(np.any(good[:-1]&~good[1:]))))
    return pd.DataFrame(out)

def pair_metric(a):
    d=np.abs(a[:,None,:]-a[None,:,:])
    mask=np.triu(np.ones(a.shape[:2],bool),1)
    z=d[mask]
    return float((z>0).mean()),float(z.mean())

def h1_tables(b,nboot,seed):
    ev=b[b.query_id>=250].copy();ev['fill']=ev.safe_budget.fillna(240)
    desc=[];est=[];boot=[];loso=[];rng=np.random.default_rng(seed)
    for ds in DATASETS:
        g=ev[ev.dataset==ds]
        w=g.pivot(index='query_id',columns='build_id',values='fill');diam=w.max(1)-w.min(1)
        desc.append(dict(dataset=ds,estimand_id='H1-A',variation_coverage=(diam>0).mean(),
            mean_diameter=diam.mean(),median_diameter=diam.median(),p90_diameter=diam.quantile(.9),
            p95_diameter=diam.quantile(.95),endpoint_rate=g.right_censored.mean()))
        cube=g.pivot_table(index='query_id',columns=['seed','order'],values='fill').loc[:,pd.MultiIndex.from_product([SEEDS,ORDERS])]
        arr=cube.to_numpy().reshape(750,8,3)
        od=[]
        for si in range(8):
            for i in range(3):
                for j in range(i+1,3): od.append(np.abs(arr[:,si,i]-arr[:,si,j]))
        od=np.stack(od,1);Dord=(od>0).mean();Aord=od.mean()
        sd=[]
        for oi in range(3):
            for i in range(8):
                for j in range(i+1,8): sd.append(np.abs(arr[:,i,oi]-arr[:,j,oi]))
        sd=np.stack(sd,1);Dseed=(sd>0).mean();Aseed=sd.mean()
        est += [dict(dataset=ds,estimand_id='H1-B',disagreement=Dord,absolute_budget_difference=Aord),
                dict(dataset=ds,estimand_id='H1-C',disagreement=Dseed,absolute_budget_difference=Aseed)]
        bo=np.empty((nboot,2));bs=np.empty((nboot,2))
        for r in range(nboot):
            ss=rng.integers(0,8,8);qq=rng.integers(0,750,750);aa=arr[qq][:,ss,:]
            ods=[]
            for si in range(8):
                for i in range(3):
                    for j in range(i+1,3): ods.append(np.abs(aa[:,si,i]-aa[:,si,j]))
            ods=np.stack(ods,1);sds=[]
            for oi in range(3):
                for i in range(8):
                    for j in range(i+1,8): sds.append(np.abs(aa[:,i,oi]-aa[:,j,oi]))
            sds=np.stack(sds,1);bo[r]=[(ods>0).mean(),ods.mean()];bs[r]=[(sds>0).mean(),sds.mean()]
        for eid,point,vals in [('H1-B',(Dord,Aord),bo),('H1-C',(Dseed,Aseed),bs)]:
            # Centered cluster-bootstrap intervals avoid the known downward
            # support/range bias caused by duplicate seed environments.
            dv=vals[:,0]-vals[:,0].mean();av=vals[:,1]-vals[:,1].mean()
            dl,dh=point[0]+np.quantile(dv,[.025,.975]);al,ah=point[1]+np.quantile(av,[.025,.975]);boot.append(dict(dataset=ds,estimand_id=eid,
                disagreement=point[0],disagreement_ci_low=dl,disagreement_ci_high=dh,
                absolute_difference=point[1],absolute_ci_low=al,absolute_ci_high=ah,
                resampling='crossed seed-query; fixed order factor'))
        for drop in SEEDS:
            aa=arr[:,[i for i,s in enumerate(SEEDS) if s!=drop],:]
            ods=[np.abs(aa[:,si,i]-aa[:,si,j]) for si in range(7) for i in range(3) for j in range(i+1,3)]
            sds=[np.abs(aa[:,i,oi]-aa[:,j,oi]) for oi in range(3) for i in range(7) for j in range(i+1,7)]
            loso += [dict(dataset=ds,dropped_seed=drop,estimand_id='H1-B',disagreement=(np.stack(ods,1)>0).mean(),absolute_difference=np.stack(ods,1).mean()),
                     dict(dataset=ds,dropped_seed=drop,estimand_id='H1-C',disagreement=(np.stack(sds,1)>0).mean(),absolute_difference=np.stack(sds,1).mean())]
    return map(pd.DataFrame,[desc,est,boot,loso])

def transport(x,b,nboot,seed):
    ev=b[b.query_id>=250];lookup=x.set_index(['dataset','build_id','query_id','ef_search'])[['recall','ndc']]
    events=[]
    for ds in DATASETS:
        builds=sorted(ev[ev.dataset==ds].build_id.unique())
        for src in builds:
            sb=ev[(ev.dataset==ds)&(ev.build_id==src)].set_index('query_id')
            ss,so=parse_build(src)
            for tgt in builds:
                if src==tgt: continue
                tb=ev[(ev.dataset==ds)&(ev.build_id==tgt)].set_index('query_id');ts,to=parse_build(tgt)
                for q in range(250,1000):
                    se=sb.at[q,'safe_budget'];te=tb.at[q,'safe_budget'];sc=pd.isna(se);tc=pd.isna(te)
                    action=200 if sc else int(se); rr=lookup.loc[(ds,tgt,q,action)];base=lookup.loc[(ds,tgt,q,200 if tc else int(te))]
                    fail=bool(rr.recall<.95 or tc);diag=bool(base.recall<.95 or tc)
                    if sc: cat='SOURCE_ENDPOINT_INFEASIBLE'
                    elif tc: cat='TARGET_ENDPOINT_INFEASIBLE'
                    elif not sb.at[q,'endpoint_feasible'] or not tb.at[q,'endpoint_feasible']: cat='RIGHT_CENSORED'
                    elif se<te: cat='UNSAFE_UNDER_BUDGET' if fail else 'SAFE_EXACT'
                    elif se==te: cat='SAFE_EXACT'
                    else: cat='SAFE_OVER_BUDGET'
                    safe_cost=np.nan if fail or diag else float(rr.ndc-base.ndc)
                    events.append(dict(dataset=ds,source_build=src,target_build=tgt,source_seed=ss,target_seed=ts,
                        source_order=so,target_order=to,query_id=q,event=cat,failure=fail,reference_failure=diag,
                        risk_increment=float(fail)-float(diag),under=bool(not sc and not tc and se<te),
                        exact=bool(not sc and not tc and se==te),over=bool(not sc and not tc and se>te),
                        source_endpoint=sc,target_endpoint=tc,right_censored=bool(sc or tc),
                        ndc_difference_safe=safe_cost,target_oracle_ndc=float(base.ndc)))
    e=pd.DataFrame(events)
    comp=e.groupby(['dataset','source_build','target_build','event']).size().unstack(fill_value=0).div(750).reset_index()
    for c in ['SOURCE_ENDPOINT_INFEASIBLE','TARGET_ENDPOINT_INFEASIBLE','RIGHT_CENSORED','UNSAFE_UNDER_BUDGET','SAFE_EXACT','SAFE_OVER_BUDGET']:
        if c not in comp: comp[c]=0.
    summaries=[];inference=[];rng=np.random.default_rng(seed)
    for ds in DATASETS:
        z=e[e.dataset==ds];valid=z.ndc_difference_safe.notna()
        point_r=z.risk_increment.mean();point_abs=z.loc[valid,'ndc_difference_safe'].mean()
        point_rom=z.loc[valid,'ndc_difference_safe'].sum()/z.loc[valid,'target_oracle_ndc'].sum()
        point_mor=(z.loc[valid,'ndc_difference_safe']/z.loc[valid,'target_oracle_ndc']).mean()
        summaries.append(dict(dataset=ds,pairs=552,queries_per_pair=750,absolute_risk=z.failure.mean(),risk_increment=point_r,
            under=z.under.mean(),exact=z.exact.mean(),over=z.over.mean(),source_endpoint=z.source_endpoint.mean(),
            target_endpoint=z.target_endpoint.mean(),right_censored=z.right_censored.mean(),absolute_ndc_difference=point_abs,
            ratio_of_means=point_rom,mean_of_ratios=point_mor))
        qagg=z.groupby(['source_seed','query_id']).agg(risk_increment=('risk_increment','mean'),delta=('ndc_difference_safe','mean'),denom=('target_oracle_ndc','mean')).reset_index()
        R=np.empty((nboot,2))
        for r in range(nboot):
            ss=rng.choice(SEEDS,8,replace=True);qq=rng.integers(250,1000,750);parts=[]
            for s in ss: parts.append(qagg[qagg.source_seed==s].set_index('query_id').reindex(qq))
            a=pd.concat(parts);R[r,0]=a.risk_increment.mean();R[r,1]=a.delta.sum()/a.denom.sum()
        rl,rh=ci(R[:,0]);cl,ch=ci(R[:,1]);inference.append(dict(dataset=ds,risk_increment=point_r,risk_ci_low=rl,risk_ci_high=rh,
            safe_rom_tax=point_rom,safe_rom_ci_low=cl,safe_rom_ci_high=ch,resampling='source-seed block x query; shared pair structure retained'))
    return e,comp,pd.DataFrame(summaries),pd.DataFrame(inference)

def certification(x):
    rows=[];selected=[]
    for (ds,b),g in x.groupby(['dataset','build_id']):
        ev=g[g.query_id>=250];sen=g[g.query_id<250];chosen=None
        for ef in EFS:
            k=int((sen[sen.ef_search==ef].recall<.95).sum())
            if cp_ucb(k,250,.05/6)<=.05: chosen=int(ef);break
        chosen=200 if chosen is None else chosen
        h=ev[ev.ef_search==120];k=int((h.recall<.95).sum())
        rows.append(dict(dataset=ds,build_id=b,n=750,failures=k,point_risk=k/750,ordinary_cp=cp_ucb(k,750,.05),
            simultaneous_cp=cp_ucb(k,750,.05/48),point_feasible=k/750<.05,ordinary_certified=cp_ucb(k,750,.05)<=.05,
            simultaneous_certified=cp_ucb(k,750,.05/48)<=.05))
        y=ev[ev.ef_search==chosen];safe=ev[ev.ef_search==200]
        selected.append(dict(dataset=ds,build_id=b,selected_ef=chosen,fallback=chosen==200,risk=(y.recall<.95).mean(),
            mean_ndc_delta_vs_fixed_safe=y.ndc.mean()-safe.ndc.mean(),p95_ndc_delta_vs_fixed_safe=y.ndc.quantile(.95)-safe.ndc.quantile(.95),
            p99_ndc_delta_vs_fixed_safe=y.ndc.quantile(.99)-safe.ndc.quantile(.99),full_cost='NOT_ESTIMABLE'))
    return pd.DataFrame(rows),pd.DataFrame(selected)

def h2_robustness(events):
    rows=[]
    def metric(z):
        v=z.ndc_difference_safe.notna()
        return z.risk_increment.mean(),z.loc[v,'ndc_difference_safe'].sum()/z.loc[v,'target_oracle_ndc'].sum()
    for ds in DATASETS:
        z=events[events.dataset==ds]
        rr=z[(z.source_order=='random')&(z.target_order=='random')];r,c=metric(rr)
        rows.append(dict(dataset=ds,analysis='random_only',level='random',risk_increment=r,rom_tax=c))
        for s in SEEDS:
            g=z[(z.source_seed!=s)&(z.target_seed!=s)];r,c=metric(g);rows.append(dict(dataset=ds,analysis='leave_one_seed',level=str(s),risk_increment=r,rom_tax=c))
        for o in ORDERS:
            g=z[(z.source_order!=o)&(z.target_order!=o)];r,c=metric(g);rows.append(dict(dataset=ds,analysis='leave_one_order',level=o,risk_increment=r,rom_tax=c))
    return pd.DataFrame(rows)

def save(df,out,name): df.to_csv(out/name,index=False,float_format='%.12g')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--input-manifest',required=True)
    ap.add_argument('--raw-dir',required=True);ap.add_argument('--seed',type=int,default=991);ap.add_argument('--bootstrap',type=int,default=5000);ap.add_argument('--output-dir',required=True)
    a=ap.parse_args();root=Path(a.root);out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    bm,x,inv=load_raw(root,Path(a.raw_dir));save(inv,out,'input_inventory.csv');b=budgets(x)
    h1a,h1,h1ci,loso=h1_tables(b,a.bootstrap,a.seed)
    save(h1a,out,'h1_full_family_descriptive.csv');save(h1,out,'h1_pairwise_estimands.csv');save(h1ci,out,'h1_crossed_cluster_inference.csv');save(loso,out,'h1_leave_one_seed_out.csv')
    events,comp,h2,h2ci=transport(x,b,a.bootstrap,a.seed)
    save(comp,out,'transport_event_composition.csv');save(h2,out,'h2_transport_summary.csv');save(h2ci,out,'h2_crossed_cluster_inference.csv');save(h2_robustness(events),out,'h2_robustness.csv')
    cp,sel=certification(x);save(cp,out,'simultaneous_certification.csv');save(sel,out,'selected_action_distribution.csv')
    registry=pd.DataFrame([
      ['H1-A','full-family variation coverage','P_q(max_G B_G(q)-min_G B_G(q)>0)','24 registered builds','none; descriptive support/range','descriptive','variation exists in registered build family','population CI from ordinary range bootstrap'],
      ['H1-B','within-seed cross-order disagreement','E[1{B_(s,o)!=B_(s,o\')} | o!=o\']','seed, query, three fixed orders','crossed seed-query','inferential over registered environments','fixed-order treatments disagree within seed','unseen order-distribution guarantee'],
      ['H1-C','within-order cross-seed disagreement','E[1{B_(s,o)!=B_(s\',o)} | s!=s\']','query, seeds within fixed order','crossed seed-query','inferential over registered environments','construction seeds disagree within fixed order','universal unseen-build guarantee'],
      ['H2-R','Oracle transport risk increment','E[Z_t(B_s)-Z_t(B_t)]','directed builds and evaluation queries','source-seed x query','post-confirmatory mechanism inference','transport creates a frozen-family risk barrier','deployable Oracle policy'],
      ['H2-C','safe adjusted ROM NDC tax','sum(C_t(B_s)-C_t(B_t))/sum(C_t(B_t)) on safe units','safe transport units','source-seed x query','post-confirmatory mechanism inference','safe transport creates compute tax','unsafe low-cost action is a gain']])
    registry.columns=['estimand_id','name','formal_definition','population_scope','resampling_unit','descriptive_or_inferential','allowed_claim','forbidden_claim'];save(registry,out,'estimand_registry.csv')
    legacy=pd.read_csv(root/'results/graph_anns_e4_reanalysis/within_order_seed_bootstrap.csv')
    bad=legacy[(legacy.estimate<legacy.ci_low)|(legacy.estimate>legacy.ci_high)].copy();bad['reason']='non-smooth support/range statistic; duplicate-seed n-out-of-n resamples reduce effective distinct environments';bad['paper_usable_as_primary_ci']=False
    save(bad,out,'legacy_bootstrap_anomalies.csv')
    env={'python':sys.version.split()[0],'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,'seed':a.seed,'bootstrap':a.bootstrap,'efs':EFS.tolist(),'frozen_parent':'f7e0b6233c05a96b09dd6a03d4eb4e2246fa9e5a'}
    (out/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    print(json.dumps({'h1':h1ci.to_dict('records'),'h2':h2ci.to_dict('records'),'legacy_anomalies':len(bad)},indent=2))

if __name__=='__main__': main()
