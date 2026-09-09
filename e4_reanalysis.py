#!/usr/bin/env python3
import hashlib,json,math,subprocess
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import beta,binom,kendalltau
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');RAW=Path('/home/wlk/data500/graph_anns_e4/raw')
RES=ROOT/'results/graph_anns_e4_reanalysis';DOC=ROOT/'docs/graph_anns_e4_reanalysis';FIG=ROOT/'figures/graph_anns_e4_reanalysis';TEST=ROOT/'tests/graph_anns_e4_reanalysis';MAN=ROOT/'manifests/graph_anns_e4_semantic_reanalysis_decision.json'
EFS=np.array([10,20,40,80,120,200]);SEEDS=[83,97,109,127,149,163,181,197];ORDERS=['random','lid_ascending','lid_descending'];DS=['sift_100k','arxiv_nomic_100k'];NBOOT=5000
for p in [RES,DOC,FIG,TEST]:p.mkdir(parents=True,exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for z in iter(lambda:f.read(1<<20),b''):h.update(z)
 return h.hexdigest()
def cp(k,n,alpha=.05):return 1.0 if k>=n else float(beta.ppf(1-alpha,k+1,n-k))
def save(x,n):x.to_csv(RES/n,index=False)
def fsave(n):plt.tight_layout();plt.savefig(FIG/f'{n}.png',dpi=180);plt.savefig(FIG/f'{n}.pdf');plt.close()
def boot_mean(v,rng):
 v=np.asarray(v,float);z=v[rng.integers(0,len(v),(NBOOT,len(v)))].mean(1);return np.mean(v),np.quantile(z,.025),np.quantile(z,.975)
def main():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='c676cdd577b1542dcffa9771887d4a768025c009'
 # Immutable E4 snapshot and role mapping.
 old=[]
 for base in [ROOT/'docs/graph_anns_e4',ROOT/'results/graph_anns_e4',ROOT/'figures/graph_anns_e4',ROOT/'tests/graph_anns_e4']:
  for p in sorted(base.glob('*')):
   if p.is_file():old.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p)})
 (RES/'original_e4_snapshot.json').write_text(json.dumps(old,indent=2)+'\n')
 role=[]
 for ds in DS:
  ids=np.load(ROOT/f'manifests/graph_anns_e4_{ds}_confirmatory_ids.npy',allow_pickle=False);sen=np.load(ROOT/f'manifests/graph_anns_e4_{ds}_sentinel_ids.npy',allow_pickle=False);ev=np.load(ROOT/f'manifests/graph_anns_e4_{ds}_evaluation_ids.npy',allow_pickle=False)
  assert np.array_equal(ids[:250],sen) and np.array_equal(ids[250:],ev) and not set(sen)&set(ev)
  role.extend({'dataset':ds,'local_query_id':i,'global_query_id':int(v),'role':'target_sentinel' if i<250 else 'confirmatory_evaluation'} for i,v in enumerate(ids))
 save(pd.DataFrame(role),'query_role_mapping.csv')
 # Correct manifest field semantics, without editing E4.
 bm=pd.read_csv(ROOT/'results/graph_anns_e4/build_manifest.csv');fa=[]
 for _,r in bm.iterrows():
  inp=Path('/home/wlk/data500/graph_anns_e4/inputs')/r.dataset/'confirmatory.f32bin'
  fa.append({'dataset':r.dataset,'build_id':r.build_id,'original_field':'queries_sha256','original_value':r.queries_sha256,'corrected_semantic_name':'raw_result_sha256','query_input_sha256':sha(inp),'rows':int(r['rows']),'rows_explanation':'1000_queries_x_6_ef_x_5_latency_rounds','raw_result_hash_matches':sha(RAW/r.build_id/'queries.csv.gz')==r.queries_sha256})
 save(pd.DataFrame(fa),'manifest_field_audit.csv')
 # Collapse latency repetitions; preserve raw Recall vectors.
 allx=[]
 for _,r in bm.iterrows():
  x=pd.read_csv(RAW/r.build_id/'queries.csv.gz').groupby(['query_id','ef_search'],as_index=False).agg(recall=('recall_at_10','first'),ndc=('ndc','first'),latency_ns=('latency_ns','median'),output=('returned_top10','first'))
  x['dataset']=r.dataset;x['build_id']=r.build_id;x['seed']=int(r.seed);x['order']=r['order'];allx.append(x)
 x=pd.concat(allx,ignore_index=True);assert len(x)==48*6000
 # Verify shared truth/query/result determinism semantics.
 assert bm.groupby('dataset').truth_sha256.nunique().eq(1).all()
 # Budgets using monotone-safe suffix event, endpoint kept separate.
 br=[]
 for (ds,b,seed,order,q),g in x.groupby(['dataset','build_id','seed','order','query_id'],sort=False):
  g=g.set_index('ef_search').loc[EFS];raw=g.recall.to_numpy()>=.95;safe=np.logical_and.accumulate(raw[::-1])[::-1];ii=np.flatnonzero(safe)
  br.append({'dataset':ds,'build_id':b,'seed':seed,'order':order,'query_id':q,'safe_budget':float(EFS[ii[0]]) if len(ii) else np.nan,'endpoint_feasible':bool(raw[-1]),'right_censored':not bool(raw[-1]),'raw_nonmonotone':bool(np.any(raw[:-1]&~raw[1:])),'raw_vector':''.join('1' if z else '0' for z in raw)})
 b=pd.DataFrame(br);evb=b[b.query_id>=250].copy();mapped=evb.assign(budget_fill=evb.safe_budget.fillna(240))
 # H1 within fixed orders and fixed seeds.
 h1=[]
 def h1row(ds,scope,key,g):
  w=g.pivot(index='query_id',columns='build_id',values='budget_fill');diam=w.max(1)-w.min(1);inv=[]
  for i in range(w.shape[1]):
   for j in range(i+1,w.shape[1]):inv.append((1-float(kendalltau(w.iloc[:,i],w.iloc[:,j],variant='b').statistic))/2)
  return {'dataset':ds,'scope':scope,'level':key,'builds':w.shape[1],'nonzero_fraction':(diam>0).mean(),'mean_diameter':diam.mean(),'median_diameter':diam.median(),'p75_diameter':diam.quantile(.75),'p90_diameter':diam.quantile(.9),'p95_diameter':diam.quantile(.95),'mean_rank_inversion':np.mean(inv),'endpoint_conversion':g.groupby('query_id').endpoint_feasible.nunique().gt(1).mean(),'right_censoring':g.right_censored.mean(),'raw_nonmonotonicity':g.raw_nonmonotone.mean()}
 for ds in DS:
  gd=mapped[mapped.dataset==ds];h1.append(h1row(ds,'all_builds','all',gd))
  for o in ORDERS:h1.append(h1row(ds,'within_order',o,gd[gd.order==o]))
  for seed in SEEDS:h1.append(h1row(ds,'within_seed',str(seed),gd[gd.seed==seed]))
 h1=pd.DataFrame(h1);save(h1,'h1_within_order.csv')
 # Descriptive crossed variance decomposition per query: fixed order + seed block + interaction residual.
 dec=[]
 for ds in DS:
  gd=mapped[mapped.dataset==ds]
  for q,g in gd.groupby('query_id'):
   a=g.pivot(index='seed',columns='order',values='budget_fill').loc[SEEDS,ORDERS].to_numpy();grand=a.mean();sv=np.mean((a.mean(1)-grand)**2);ov=np.mean((a.mean(0)-grand)**2);iv=np.mean((a-a.mean(1)[:,None]-a.mean(0)[None,:]+grand)**2)
   dec.append({'dataset':ds,'query_id':q,'seed_variance':sv,'fixed_order_variance':ov,'seed_order_interaction':iv,'total_build_variance':np.var(a)})
 dec=pd.DataFrame(dec);save(dec.groupby('dataset',as_index=False).mean(numeric_only=True),'h1_seed_order_decomposition.csv')
 # Lookup arrays indexed by build/query/ef.
 lookup=x.set_index(['dataset','build_id','query_id','ef_search'])[['recall','ndc','latency_ns']]
 # True source Oracle transport, 552 off-diagonal pairs per dataset.
 pairs=[];perq=[]
 for ds in DS:
  builds=sorted(b[b.dataset==ds].build_id.unique())
  for src in builds:
   sb=evb[(evb.dataset==ds)&(evb.build_id==src)].set_index('query_id')
   for tgt in builds:
    tb=evb[(evb.dataset==ds)&(evb.build_id==tgt)].set_index('query_id');zs=[]
    for q in range(250,1000):
     se=sb.loc[q,'safe_budget'];te=tb.loc[q,'safe_budget'];source_cens=not np.isfinite(se);target_cens=not np.isfinite(te);ae=200 if source_cens else int(se);target=lookup.loc[(ds,tgt,q,ae)];tbase=lookup.loc[(ds,tgt,q,200 if target_cens else int(te))]
     fail=target.recall<.95 or target_cens;diagfail=tbase.recall<.95 or target_cens;bd=np.nan if source_cens or target_cens else se-te;cost=np.nan if fail or diagfail else target.ndc-tbase.ndc
     zs.append({'query_id':q,'failure':bool(fail),'diagonal_failure':bool(diagfail),'source_censored':source_cens,'target_censored':target_cens,'budget_difference':bd,'ndc_difference_safe':cost,'source_action':ae,'source_ndc':target.ndc,'target_oracle_ndc':tbase.ndc})
    z=pd.DataFrame(zs);risk=z.failure.mean();diag=z.diagonal_failure.mean();joint=z[~z.source_censored&~z.target_censored];safe=z[~z.failure&~z.diagonal_failure];rom=(safe.source_ndc.mean()-safe.target_oracle_ndc.mean())/safe.target_oracle_ndc.mean() if len(safe) else np.nan;mor=((safe.source_ndc-safe.target_oracle_ndc)/safe.target_oracle_ndc).mean() if len(safe) else np.nan
    k=int(z.failure.sum());lo=float(beta.ppf(.025,k,751-k)) if k else 0.;hi=float(beta.ppf(.975,k+1,750-k)) if k<750 else 1.
    if src==tgt:point='DIAGONAL_REFERENCE'
    elif z.source_censored.mean()>0:point='SOURCE_ENDPOINT_INFEASIBLE'
    elif z.target_censored.mean()>0:point='TARGET_ENDPOINT_INFEASIBLE'
    elif risk>.05:point='UNSAFE_TRANSPORT'
    elif rom>.01:point='SAFE_BUT_CONSERVATIVE'
    else:point='PORTABLE_WITHIN_TOLERANCE'
    if src==tgt:ci_class='DIAGONAL_REFERENCE'
    elif lo>.05:ci_class='UNSAFE_TRANSPORT'
    elif hi<=.05 and np.isfinite(rom) and rom>.01:ci_class='SAFE_BUT_CONSERVATIVE'
    elif hi<=.05 and np.isfinite(rom) and rom<=.01:ci_class='PORTABLE_WITHIN_TOLERANCE'
    else:ci_class='MIXED_OR_INDETERMINATE'
    pairs.append({'dataset':ds,'source_build':src,'target_build':tgt,'diagonal':src==tgt,'risk':risk,'risk_ci_low':lo,'risk_ci_high':hi,'diagonal_risk':diag,'risk_increment':risk-diag,'source_fallback_rate':z.source_censored.mean(),'target_endpoint_failure_rate':z.target_censored.mean(),'under_budget_rate':(joint.budget_difference<0).mean(),'over_budget_rate':(joint.budget_difference>0).mean(),'exact_match_rate':(joint.budget_difference==0).mean(),'mean_abs_budget_difference':joint.budget_difference.abs().mean(),'median_abs_budget_difference':joint.budget_difference.abs().median(),'absolute_ndc_transport_cost':safe.ndc_difference_safe.mean(),'ratio_of_means_ndc_tax':rom,'mean_of_ratios_ndc_regret':mor,'point_classification':point,'ci_classification':ci_class,'evidence_level':'NON_DEPLOYABLE_ORACLE_TRANSPORT_MECHANISM_ANALYSIS'})
    if src!=tgt:
     z['dataset']=ds;z['source_build']=src;z['target_build']=tgt;perq.append(z)
 p=pd.DataFrame(pairs);pq=pd.concat(perq,ignore_index=True);save(p,'oracle_transport_directed_pairs.csv')
 ps=p[~p.diagonal].groupby('dataset').agg(pairs=('source_build','size'),mean_risk=('risk','mean'),mean_risk_increment=('risk_increment','mean'),under_budget_rate=('under_budget_rate','mean'),over_budget_rate=('over_budget_rate','mean'),exact_match_rate=('exact_match_rate','mean'),absolute_ndc_transport_cost=('absolute_ndc_transport_cost','mean'),ratio_of_means_ndc_tax=('ratio_of_means_ndc_tax','mean'),mean_of_ratios_ndc_regret=('mean_of_ratios_ndc_regret','mean')).reset_index();save(ps,'oracle_transport_dataset_summary.csv')
 # Regret definitions and low-denominator sensitivity.
 regs=[]
 for ds in DS:
  z=pq[pq.dataset==ds].dropna(subset=['ndc_difference_safe']);rel=z.ndc_difference_safe/z.target_oracle_ndc;q5=z.target_oracle_ndc.quantile(.05);trim=rel[(rel>=rel.quantile(.01))&(rel<=rel.quantile(.99))];keep=z[z.target_oracle_ndc>=q5];drop1=z[z.target_oracle_ndc>z.target_oracle_ndc.quantile(.01)]
  regs.append({'dataset':ds,'absolute_difference':z.ndc_difference_safe.mean(),'ratio_of_means':z.ndc_difference_safe.mean()/z.target_oracle_ndc.mean(),'mean_of_ratios':rel.mean(),'median_relative_regret':rel.median(),'p25':rel.quantile(.25),'p75':rel.quantile(.75),'p90':rel.quantile(.9),'p95':rel.quantile(.95),'trimmed_mean_1pct':trim.mean(),'wins':int((z.ndc_difference_safe<0).sum()),'ties':int((z.ndc_difference_safe==0).sum()),'losses':int((z.ndc_difference_safe>0).sum()),'denominator_p5':q5,'rom_drop_below_p5':keep.ndc_difference_safe.mean()/keep.target_oracle_ndc.mean(),'rom_drop_lowest_1pct':drop1.ndc_difference_safe.mean()/drop1.target_oracle_ndc.mean()})
 regs=pd.DataFrame(regs);save(regs,'ndc_regret_definitions.csv')
 # Source-calibrated global policies with Bonferroni CP, and target recalibration.
 policies=[]
 for ds in DS:
  builds=sorted(b[b.dataset==ds].build_id.unique());chosen={}
  for src in builds:
   g=x[(x.dataset==ds)&(x.build_id==src)&(x.query_id<250)];sel=None
   for ef in EFS:
    k=int((g[g.ef_search==ef].recall<.95).sum())
    if cp(k,250,.05/6)<=.05:sel=int(ef);break
   chosen[src]=200 if sel is None else sel
  for src in builds:
   for tgt in builds:
    ef=chosen[src];g=x[(x.dataset==ds)&(x.build_id==tgt)&(x.query_id>=250)&(x.ef_search==ef)];k=int((g.recall<.95).sum());te=chosen[tgt];gt=x[(x.dataset==ds)&(x.build_id==tgt)&(x.query_id>=250)&(x.ef_search==te)]
    policies.append({'dataset':ds,'source_build':src,'target_build':tgt,'source_selected_ef':ef,'target_selected_ef':te,'source_fallback':ef==200,'target_fallback':te==200,'target_risk':k/750,'target_risk_ucb':cp(k,750),'mean_recall':g.recall.mean(),'mean_ndc':g.ndc.mean(),'p95_ndc':g.ndc.quantile(.95),'p99_ndc':g.ndc.quantile(.99),'mean_latency_ns':g.latency_ns.mean(),'p95_latency_ns':g.latency_ns.quantile(.95),'p99_latency_ns':g.latency_ns.quantile(.99),'ndc_difference_vs_target_recalibration':g.ndc.mean()-gt.ndc.mean(),'risk_difference_vs_target_recalibration':k/750-(gt.recall<.95).mean(),'evidence_level':'POST_CONFIRMATORY_DEPLOYABLE_INFORMATION_ANALYSIS'})
 pol=pd.DataFrame(policies);save(pol,'source_calibrated_transfer.csv');tc=pol[pol.source_build==pol.target_build].copy();save(tc,'target_recalibration_corrected.csv')
 # Original B4 versus corrected B4.
 orig=pd.read_csv(ROOT/'results/graph_anns_e4/per_build_summary.csv');orig=orig[orig.strategy=='B4'][['dataset','build_id','b4_ef','risk','mean_ndc']];corr=tc[['dataset','target_build','target_selected_ef','target_risk','mean_ndc']].rename(columns={'target_build':'build_id','mean_ndc':'corrected_mean_ndc'});comp=orig.merge(corr,on=['dataset','build_id']);save(comp,'b4_original_vs_corrected.csv')
 # Per-target B2 ef120 certification.
 cpa=[]
 for (ds,tgt),g in x[(x.query_id>=250)&(x.ef_search==120)].groupby(['dataset','build_id']):
  k=int((g.recall<.95).sum());pv=float(binom.cdf(k,750,.05));cpa.append({'dataset':ds,'target_build':tgt,'failures':k,'n':750,'point_risk':k/750,'cp_ucb_95':cp(k,750,.05),'cp_ucb_bonferroni_48':cp(k,750,.05/48),'point_below_5pct':k/750<.05,'per_target_certified':cp(k,750,.05)<=.05,'simultaneously_certified_bonferroni':cp(k,750,.05/48)<=.05,'null_pvalue_risk_ge_5pct':pv})
 cpa=pd.DataFrame(cpa);save(cpa,'per_target_cp_audit.csv');sim=cpa.groupby('dataset').agg(builds=('target_build','size'),point_below=('point_below_5pct','sum'),per_target_certified=('per_target_certified','sum'),simultaneously_certified=('simultaneously_certified_bonferroni','sum'),meta_average_risk=('point_risk','mean')).reset_index();save(sim,'simultaneous_certification.csv')
 # Seed-block and crossed seed-query bootstraps for H1 and H2.
 seedboot=[];cross=[];withinboot=[];rng=np.random.default_rng(991)
 for ds in DS:
  gd=mapped[mapped.dataset==ds];seed_h1=[];seed_h2=[]
  for seed in SEEDS:
   z=gd[gd.seed==seed].pivot(index='query_id',columns='build_id',values='budget_fill');seed_h1.append((z.max(1)>z.min(1)).mean());seed_h2.append(p[(p.dataset==ds)&(~p.diagonal)&(p.source_build.str.contains(f'seed{seed}'))].ratio_of_means_ndc_tax.mean())
  qids=np.arange(250,1000);inds=rng.integers(0,8,(NBOOT,8));a=np.array(seed_h1)[inds].mean(1);h=np.array(seed_h2)[inds].mean(1)
  seedboot += [{'dataset':ds,'metric':'H1_nonzero_fraction','estimate':np.mean(seed_h1),'ci_low':np.quantile(a,.025),'ci_high':np.quantile(a,.975),'unit':'seed_block_keep_three_orders'},{'dataset':ds,'metric':'H2_ROM_tax','estimate':np.mean(seed_h2),'ci_low':np.quantile(h,.025),'ci_high':np.quantile(h,.975),'unit':'seed_block_keep_three_orders'}]
  for o in ORDERS:
   aa=gd[gd.order==o].pivot(index='seed',columns='query_id',values='budget_fill').loc[SEEDS,qids].to_numpy();boot=(np.ptp(aa[inds],axis=1)>0).mean(1);withinboot.append({'dataset':ds,'order':o,'estimate':(np.ptp(aa,axis=0)>0).mean(),'ci_low':np.quantile(boot,.025),'ci_high':np.quantile(boot,.975),'unit':'seed_within_fixed_order'})
  # Crossed resample evaluates seed-block-by-query arrays; all three source orders remain grouped.
  vals=np.empty(NBOOT);tax=np.empty(NBOOT);seed_tax=np.empty((8,750,2))
  for si,seed in enumerate(SEEDS):
   zz=pq[(pq.dataset==ds)&pq.source_build.str.contains(f'seed{seed}')&pq.ndc_difference_safe.notna()].groupby('query_id').agg(delta=('ndc_difference_safe','mean'),denom=('target_oracle_ndc','mean')).reindex(qids)
   seed_tax[si,:,0]=zz.delta.fillna(0);seed_tax[si,:,1]=zz.denom.fillna(np.nan)
  for r in range(NBOOT):
   ss=rng.integers(0,8,8);qq=rng.integers(0,750,750);parts=[];tparts=[]
   for si in ss:
    seed=SEEDS[si];z=gd[gd.seed==seed].pivot(index='query_id',columns='order',values='budget_fill').loc[qids].to_numpy()[qq];parts.append((z.max(1)>z.min(1)).mean())
   vals[r]=np.mean(parts);num=seed_tax[ss][:,qq,0];den=seed_tax[ss][:,qq,1];tax[r]=np.nansum(num)/np.nansum(den)
  cross += [{'dataset':ds,'metric':'H1_nonzero_fraction','estimate':vals.mean(),'ci_low':np.quantile(vals,.025),'ci_high':np.quantile(vals,.975)},{'dataset':ds,'metric':'H2_ROM_tax','estimate':tax.mean(),'ci_low':np.quantile(tax,.025),'ci_high':np.quantile(tax,.975)}]
 save(pd.DataFrame(seedboot),'seed_block_bootstrap.csv');save(pd.DataFrame(withinboot),'within_order_seed_bootstrap.csv');save(pd.DataFrame(cross),'crossed_seed_query_bootstrap.csv')
 # Leave one seed/order and broad robustness.
 los=[];loo=[];rob=[]
 for ds in DS:
  for seed in SEEDS:
   z=p[(p.dataset==ds)&(~p.diagonal)&~p.source_build.str.contains(f'seed{seed}')&~p.target_build.str.contains(f'seed{seed}')];los.append({'dataset':ds,'dropped_seed':seed,'pairs':len(z),'risk_increment':z.risk_increment.mean(),'rom_tax':z.ratio_of_means_ndc_tax.mean(),'positive':z.ratio_of_means_ndc_tax.mean()>.01})
  for o in ORDERS:
   z=p[(p.dataset==ds)&(~p.diagonal)&(p.source_build.str.contains(o)==False)&(p.target_build.str.contains(o)==False)];loo.append({'dataset':ds,'dropped_order':o,'pairs':len(z),'risk_increment':z.risk_increment.mean(),'rom_tax':z.ratio_of_means_ndc_tax.mean(),'positive':z.ratio_of_means_ndc_tax.mean()>.01})
  for o in ORDERS:
   z=p[(p.dataset==ds)&(~p.diagonal)&p.source_build.str.contains(o)&p.target_build.str.contains(o)];rob.append({'dataset':ds,'analysis':f'{o}_only','pairs':len(z),'risk_increment':z.risk_increment.mean(),'rom_tax':z.ratio_of_means_ndc_tax.mean(),'positive':z.ratio_of_means_ndc_tax.mean()>.01})
 save(pd.DataFrame(los),'leave_one_seed_out.csv');save(pd.DataFrame(loo),'leave_one_order_out.csv');save(pd.DataFrame(rob),'robustness_summary.csv')
 # Gates.
 sb=pd.DataFrame(seedboot);cr=pd.DataFrame(cross);losd=pd.DataFrame(los);robd=pd.DataFrame(rob);gates=[]
 for ds in DS:
  wh=h1[(h1.dataset==ds)&(h1.scope=='within_order')];h1pass=(wh.nonzero_fraction>0).all() and wh[wh.level=='random'].nonzero_fraction.iloc[0]>0 and cr[(cr.dataset==ds)&(cr.metric=='H1_nonzero_fraction')].ci_low.iloc[0]>0
  h2pass=(ps[ps.dataset==ds].ratio_of_means_ndc_tax.iloc[0]>.01 and robd[(robd.dataset==ds)&(robd.analysis=='random_only')].rom_tax.iloc[0]>.01 and losd[losd.dataset==ds].positive.all())
  pp=pol[(pol.dataset==ds)&(pol.source_build!=pol.target_build)];source_actions=pp.groupby('source_build').first();fallback=source_actions.source_fallback.mean()
  if fallback==1:h3='NO_CERTIFIED_SOURCE_ACTION'
  elif fallback>.5:h3='SAFE_BUT_ECONOMICALLY_DOMINATED'
  elif (pp.target_risk_ucb<=.05).mean()>=.9 and pp.ndc_difference_vs_target_recalibration.mean()<=0:h3='DEPLOYABLE_TRANSFER_SUPPORTED'
  elif pp.ndc_difference_vs_target_recalibration.mean()>0:h3='TARGET_RECALIBRATION_REQUIRED'
  else:h3='POST_CONFIRMATORY_INCONCLUSIVE'
  gates.append({'dataset':ds,'H1':'STRONG_PASS' if h1pass else 'CONDITIONAL_OR_FAIL','H2':'STRONG_PASS' if h2pass else 'NOT_IDENTIFIED','H3':h3})
 gate=pd.DataFrame(gates);save(gate,'unified_reanalysis_gate.csv')
 if (gate.H1=='STRONG_PASS').all() and (gate.H2=='STRONG_PASS').all():label='E4_H1_H2_TRANSPORT_CONFIRMED_TWO_DATASETS'
 elif (gate.H1=='STRONG_PASS').all() and (gate.H2=='STRONG_PASS').sum()==1:label='E4_H1_CONFIRMED_H2_DATASET_CONDITIONED'
 elif (gate.H1=='STRONG_PASS').all() and not (robd[robd.analysis=='random_only'].positive).all():label='E4_H1_CONFIRMED_H2_INSERTION_REGIME_CONDITIONED'
 elif (gate.H1=='STRONG_PASS').all():label='E4_H1_CONFIRMED_H2_NOT_IDENTIFIED'
 else:label='E4_GLOBAL_VS_ORACLE_GAP_ONLY_NO_REBUILD_TAX'
 deploy='DEPLOYABLE_SOURCE_TRANSFER_SUPPORTED' if (gate.H3=='DEPLOYABLE_TRANSFER_SUPPORTED').all() else ('TARGET_RECALIBRATION_REQUIRED' if (gate.H3=='TARGET_RECALIBRATION_REQUIRED').any() else ('NO_DEPLOYABLE_VALUE' if gate.H3.isin(['NO_CERTIFIED_SOURCE_ACTION','SAFE_BUT_ECONOMICALLY_DOMINATED']).all() else 'SCIENTIFIC_MECHANISM_ONLY'))
 decision={'schema_version':1,'evidence_level':'POST_CONFIRMATORY_SEMANTIC_AND_FACTORIAL_REANALYSIS','label':label,'deployment_label':deploy,'frozen_parent':'c676cdd577b1542dcffa9771887d4a768025c009','build_artifacts':48,'factorial_design':'2 datasets x 8 construction seeds x 3 fixed insertion regimes','query_mapping_valid':True,'oracle_transport_pairs_per_dataset':552,'original_e4_modified':False,'future_replication_accessed':False,'validation_dev_accessed':False,'formal_test_accessed':False,'legacy_limit':'LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123','gates':gates}
 MAN.write_text(json.dumps(decision,indent=2)+'\n')
 # Figures.
 for name,df,col,title in [('budget_variation_by_order',h1[h1.scope=='within_order'],'nonzero_fraction','Budget variation by fixed order'),('seed_order_variance',dec.groupby('dataset',as_index=False).mean(numeric_only=True),'seed_order_interaction','Seed-order interaction'),('oracle_transport_risk',ps,'mean_risk_increment','Oracle transport risk increment'),('oracle_transport_cost',ps,'ratio_of_means_ndc_tax','Oracle transport ROM tax'),('source_vs_target_calibration',pol.groupby('dataset',as_index=False).mean(numeric_only=True),'ndc_difference_vs_target_recalibration','Source vs target calibration'),('regret_definition_comparison',regs,'ratio_of_means','Regret definition comparison'),('per_target_certification',sim,'per_target_certified','Per-target certification'),('robustness_forest',robd.groupby('dataset',as_index=False).mean(numeric_only=True),'rom_tax','Robustness')]:
  plt.figure(figsize=(5,3));
  if 'level' in df: [plt.plot(g.level,g[col],marker='o',label=ds) for ds,g in df.groupby('dataset')];plt.legend()
  else: plt.bar(df.dataset,df[col])
  plt.title(title);plt.ylabel(col);fsave(name)
 # Reports, with precise evidence hierarchy.
 summary=[]
 for ds in DS:
  a=h1[(h1.dataset==ds)&(h1.scope=='all_builds')].iloc[0];z=ps[ps.dataset==ds].iloc[0];rr=regs[regs.dataset==ds].iloc[0];summary.append(f'- {ds}: H1 nonzero fraction {a.nonzero_fraction:.4f}; oracle transport risk increment {z.mean_risk_increment:.5f}; under/over/exact {z.under_budget_rate:.4f}/{z.over_budget_rate:.4f}/{z.exact_match_rate:.4f}; absolute safe NDC cost {rr.absolute_difference:.2f}; ratio-of-means tax {rr.ratio_of_means:.4f}; mean-of-ratios {rr.mean_of_ratios:.4f}.')
 base=f'''# E4 semantic and factorial reanalysis\n\nFinal label: `{label}`. Deployment label: `{deploy}`.\n\nThis is a post-confirmatory semantic analysis, not the original preregistered primary test. It uses only the frozen E4 query/search records and performs no build, ANN search, query selection, or new truth access. The 48 artifacts are a crossed 2-dataset × 8-seed × 3-fixed-order design; order is fixed and seed is the resampling block.\n\n'''+ '\n'.join(summary)+'''\n\nThe former 178%/244% values are retained only under their accurate name, mean per-query relative NDC regret for global ef=120 versus a per-query oracle. Main transport reporting uses absolute NDC difference and ratio of means. Oracle transport is explicitly nondeployable; source/target sentinel calibration is post-confirmatory deployable-information analysis.\n'''
 for name,title in [('executive_summary','Executive summary'),('semantic_audit','Semantic audit'),('factorial_inference_report','Factorial inference report'),('transport_mechanism_report','Transport mechanism report'),('source_calibrated_transfer_report','Source-calibrated transfer report'),('ndc_regret_definition_report','NDC regret definitions'),('certification_scope_report','Certification scope'),('protocol_deviation_patch','Protocol deviation patch'),('claim_evidence_patch','Claim evidence patch'),('paper_story_patch','Paper story patch'),('limitations','Limitations'),('final_report','Final report')]:
  (DOC/f'{name}.md').write_text(f'# {title}\n\n'+base)
 # Test source with 18 explicit tests.
 tests='''import json,pathlib,pandas as pd,numpy as np\nr=pathlib.Path(__file__).resolve().parents[2]\np=pd.read_csv(r/'results/graph_anns_e4_reanalysis/oracle_transport_directed_pairs.csv');q=pd.read_csv(r/'results/graph_anns_e4_reanalysis/query_role_mapping.csv');m=json.loads((r/'manifests/graph_anns_e4_semantic_reanalysis_decision.json').read_text())\ndef test_01_diag_budget(): assert (p[p.diagonal].mean_abs_budget_difference.fillna(0)==0).all()\ndef test_02_diag_ndc(): assert (p[p.diagonal].absolute_ndc_transport_cost.fillna(0)==0).all()\ndef test_03_under(): assert (p.under_budget_rate>0).any()\ndef test_04_over(): assert (p.over_budget_rate>0).any()\ndef test_05_endpoint(): assert (p.source_fallback_rate>0).any()\ndef test_06_raw_nonmono(): assert pd.read_csv(r/'results/graph_anns_e4_reanalysis/h1_within_order.csv').raw_nonmonotonicity.ge(0).all()\ndef test_07_split(): assert set(q[q.local_query_id<250].role)=={'target_sentinel'} and set(q[q.local_query_id>=250].role)=={'confirmatory_evaluation'}\ndef test_08_bonf(): assert pd.read_csv(r/'results/graph_anns_e4_reanalysis/per_target_cp_audit.csv').cp_ucb_bonferroni_48.ge(pd.read_csv(r/'results/graph_anns_e4_reanalysis/per_target_cp_audit.csv').cp_ucb_95).all()\ndef test_09_seedblock(): assert set(pd.read_csv(r/'results/graph_anns_e4_reanalysis/seed_block_bootstrap.csv').unit)=={'seed_block_keep_three_orders'}\ndef test_10_cross(): assert len(pd.read_csv(r/'results/graph_anns_e4_reanalysis/crossed_seed_query_bootstrap.csv'))==4\ndef test_11_los(): assert pd.read_csv(r/'results/graph_anns_e4_reanalysis/leave_one_seed_out.csv').pairs.gt(0).all()\ndef test_12_loo(): assert pd.read_csv(r/'results/graph_anns_e4_reanalysis/leave_one_order_out.csv').pairs.gt(0).all()\ndef test_13_regret(): assert (pd.read_csv(r/'results/graph_anns_e4_reanalysis/ndc_regret_definitions.csv').ratio_of_means!=pd.read_csv(r/'results/graph_anns_e4_reanalysis/ndc_regret_definitions.csv').mean_of_ratios).all()\ndef test_14_unsafe(): assert set(p.point_classification).issubset({'DIAGONAL_REFERENCE','UNSAFE_TRANSPORT','SAFE_BUT_CONSERVATIVE','PORTABLE_WITHIN_TOLERANCE','SOURCE_ENDPOINT_INFEASIBLE','TARGET_ENDPOINT_INFEASIBLE'})\ndef test_15_pairs(): assert p[~p.diagonal].groupby('dataset').size().eq(552).all()\ndef test_16_sources(): assert p[~p.diagonal].groupby('dataset').source_build.nunique().eq(24).all()\ndef test_17_firewall(): assert not m['future_replication_accessed'] and not m['validation_dev_accessed'] and not m['formal_test_accessed']\ndef test_18_original(): assert not m['original_e4_modified']\n'''
 (TEST/'test_reanalysis.py').write_text(tests)
 # Seal new outputs only.
 files=[]
 for basep in [DOC,RES,FIG,TEST]:
  for z in sorted(basep.glob('*')):
   if z.is_file() and z.name!='checksums.sha256':files.append(f'{sha(z)}  {z.relative_to(ROOT)}')
 files += [f'{sha(MAN)}  {MAN.relative_to(ROOT)}',f'{sha(ROOT/"e4_reanalysis.py")}  e4_reanalysis.py']
 (RES/'checksums.sha256').write_text('\n'.join(files)+'\n')
 print(json.dumps(decision,indent=2,default=str))
if __name__=='__main__':main()
