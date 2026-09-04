from pathlib import Path
import pandas as pd, numpy as np, csv, gzip, itertools, json
from scipy.stats import beta
root=Path('/home/wlk/projects/navigation-aware-resistance-hnsw'); out=root/'results/icba_cals_seal'
rules=['native_top_layer','dataset_medoid','farthest_from_medoid','fixed_label_991','fixed_label_4177','high_out_degree','fixed_label_7001','fixed_label_8888']
truth_paths={'sift':root/'results/icba_cals_oracle/design_truth_100k.ibin','arxiv':root/'results/icba_cals_oracle/design_truth_arxiv100k.ibin'}
truth={}
for ds,p in truth_paths.items():
 with p.open('rb') as f:n,k=np.fromfile(f,dtype='<u8',count=2);truth[ds]=np.fromfile(f,dtype='<u4').reshape(int(n),int(k))
fields=['dataset','build','role','raw_ef','query_id','mask','portal_count','base_hits','union_hits','positive_hit_gain','threshold_rescue','base_risk','union_risk','primary_ndc','aux_ndc_sum','total_ndc','memo_candidate_lower_bound','candidate_count']
agg=[]
with gzip.open(out/'subset_results.csv.gz','wt',newline='') as z:
 w=csv.DictWriter(z,fieldnames=fields);w.writeheader()
 for p in sorted(out.glob('lanes_*_*.csv')):
  parts=p.stem.split('_');ds=parts[1];build='_'.join(parts[1:3]);role=parts[3];d=pd.read_csv(p)
  for (ef,qid),g in d.groupby(['raw_ef','query_id'],sort=False):
   pr=g[g.lane_type=='primary'].iloc[0]; base_labels=[int(x) for x in str(pr.topk_labels).split(';')]; gt=set(map(int,truth[ds][int(qid)])); base_hits=len(gt&set(base_labels)); primary_candidates={int(a):float(b) for a,b in zip(str(pr.candidate_labels).split(';'),str(pr.candidate_distances).split(';'))}
   lanes={}
   for _,x in g[g.lane_type=='auxiliary'].iterrows(): lanes[x.portal_rule_id]=({int(a):float(b) for a,b in zip(str(x.candidate_labels).split(';'),str(x.candidate_distances).split(';'))},int(x.ndc))
   local=[]
   for mask in range(256):
    cand=dict(primary_candidates);aux=0
    for j,r in enumerate(rules):
     if mask>>j&1:
      aux+=lanes[r][1]
      for label,dist in lanes[r][0].items():
       if label not in cand or dist<cand[label]:cand[label]=dist
    top=[x[1] for x in sorted((dist,label) for label,dist in cand.items())[:10]];uh=len(gt&set(top));rec={'dataset':ds,'build':build,'role':role,'raw_ef':int(ef),'query_id':int(qid),'mask':mask,'portal_count':int(mask).bit_count(),'base_hits':base_hits,'union_hits':uh,'positive_hit_gain':int(uh>base_hits),'threshold_rescue':int(base_hits<10 and uh>=10),'base_risk':int(base_hits<10),'union_risk':int(uh<10),'primary_ndc':int(pr.ndc),'aux_ndc_sum':aux,'total_ndc':int(pr.ndc)+aux,'memo_candidate_lower_bound':len(cand),'candidate_count':len(cand)};w.writerow(rec);local.append(rec)
   # compact per-query data retained only in compressed output
# Aggregate exactly; memory is audited as sufficient for this 3.1M-row table.
d=pd.read_csv(out/'subset_results.csv.gz')
a=d.groupby(['dataset','build','role','raw_ef','mask','portal_count']).agg(n=('query_id','size'),primary_failures=('base_risk','sum'),union_failures=('union_risk','sum'),positive_hit_gain=('positive_hit_gain','sum'),threshold_rescues=('threshold_rescue','sum'),mean_recall=('union_hits','mean'),mean_ndc=('total_ndc','mean'),median_ndc=('total_ndc','median'),p95_ndc=('total_ndc',lambda x:np.quantile(x,.95)),p99_ndc=('total_ndc',lambda x:np.quantile(x,.99))).reset_index()
a['mean_recall']/=10;a['primary_risk']=a.primary_failures/a.n;a['union_risk']=a.union_failures/a.n;a['rescue_rate']=a.threshold_rescues/a.primary_failures.replace(0,np.nan)
a.to_csv(out/'subset_summary.csv',index=False)
eligible=a[(a.role=='selection')&(a.portal_count.between(1,4))].copy()
def choose(g):return g.sort_values(['union_risk','threshold_rescues','positive_hit_gain','portal_count','mean_ndc','mask'],ascending=[True,False,False,True,True,True]).iloc[0]
actions=[]
for (ds,b,ef),g in eligible.groupby(['dataset','build','raw_ef']):
 x=choose(g);actions.append({'action_scope':'TARGET_SPECIFIC_SELECTED_FIXED_SET','dataset':ds,'build':b,'raw_ef':ef,'mask':int(x['mask'])})
for (ds,ef),g in eligible.groupby(['dataset','raw_ef']):
 q=g.groupby(['mask','portal_count']).agg(union_risk=('union_risk','mean'),threshold_rescues=('threshold_rescues','sum'),positive_hit_gain=('positive_hit_gain','sum'),mean_ndc=('mean_ndc','mean')).reset_index();x=choose(q);actions.append({'action_scope':'DATASET_LEVEL_SELECTED_FIXED_SET','dataset':ds,'build':'ALL','raw_ef':ef,'mask':int(x['mask'])})
for ef,g in eligible.groupby('raw_ef'):
 q=g.groupby(['mask','portal_count']).agg(union_risk=('union_risk','mean'),threshold_rescues=('threshold_rescues','sum'),positive_hit_gain=('positive_hit_gain','sum'),mean_ndc=('mean_ndc','mean')).reset_index();x=choose(q);actions.append({'action_scope':'CROSS_DATASET_SELECTED_FIXED_SET','dataset':'ALL','build':'ALL','raw_ef':ef,'mask':int(x['mask'])})
actions=pd.DataFrame(actions);actions['portal_rule_ids']=actions['mask'].map(lambda m:';'.join(r for j,r in enumerate(rules) if int(m)>>j&1));actions.to_csv(out/'selection_actions.csv',index=False)
hold=a[a.role=='holdout'];ev=[]
for _,x in actions.iterrows():
 g=hold[hold.raw_ef.eq(x.raw_ef)&hold['mask'].eq(x['mask'])]
 if x.dataset!='ALL':g=g[g.dataset.eq(x.dataset)]
 if x.build!='ALL':g=g[g.build.eq(x.build)]
 for _,z in g.iterrows():ev.append({**x.to_dict(),**{k:z[k] for k in ['build','n','primary_failures','union_failures','positive_hit_gain','threshold_rescues','mean_recall','mean_ndc','p95_ndc','p99_ndc','primary_risk','union_risk','rescue_rate']},'risk_ucb95':float(beta.ppf(.95,z.union_failures+1,z.n-z.union_failures)) if z.union_failures<z.n else 1.0})
pd.DataFrame(ev).to_csv(out/'holdout_results.csv',index=False)
# Correctly distinct per-query Oracle summaries.
od=[]
for (ds,b,role,ef),g in d.groupby(['dataset','build','role','raw_ef']):
 for name,h in [('PER_QUERY_ORACLE_SIZE_1_4',g[g.portal_count.between(1,4)]),('PER_QUERY_ORACLE_ALL_256',g)]:
  q=h.groupby('query_id').agg(base=('base_hits','first'),best=('union_hits','max'));od.append({'dataset':ds,'build':b,'role':role,'raw_ef':ef,'oracle':name,'status':'NON_DEPLOYABLE_ORACLE_UPPER_BOUND','mean_recall':q.best.mean()/10,'positive_hit_gain':int((q.best>q.base).sum()),'threshold_rescues':int(((q.base<10)&(q.best>=10)).sum()),'risk':float((q.best<10).mean())})
pd.DataFrame(od).to_csv(out/'oracle_hierarchy.csv',index=False)
print('subset rows',len(d),'actions',len(actions),'holdout eval',len(ev))
