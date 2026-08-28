#!/usr/bin/env python3
import ast,csv,json,math
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'results/icba_open_world'
GRID=(10,16,24,32,48,64,96,128,192,256,384,512); rank={b:i for i,b in enumerate(GRID)}
split=json.load(open(ROOT/'manifests/icba_micro_closure_query_split.json'))['datasets']
eff=list(csv.DictReader(open(ROOT/'results/cross_index/g1/derived/per_query_effort.csv')))
curves=defaultdict(dict)
for r in eff:
 key=(r['index'],r['dataset'],r['seed'],r['history']); curves[key][int(r['query_id'])]=None if r['right_censored']=='True' else int(r['stable_budget'])
inv={}
for r in csv.DictReader(open(ROOT/'results/cross_index/g1/derived/rank_inversion.csv')):
 a=ast.literal_eval(r['source']); b=ast.literal_eval(r['target']); k=(r['index'],r['dataset'])
 inv[(k,(str(a[0]),a[1]),(str(b[0]),b[1]))]=float(r['rank_inversion'])
 inv[(k,(str(b[0]),b[1]),(str(a[0]),a[1]))]=float(r['rank_inversion'])
rows=[]
for (impl,dataset), keys0 in defaultdict(list, {k:[] for k in []}).items(): pass
groups=defaultdict(list)
for k in curves: groups[(k[0],k[1])].append(k)
for (impl,dataset),keys in sorted(groups.items()):
 sent=split[dataset]['sentinel_query_ids']; ev=split[dataset]['evaluation_query_ids']
 for a in keys:
  for b in keys:
   if a==b: continue
   ca,cb=curves[a],curves[b]; common=[q for q in ev if ca[q] is not None and cb[q] is not None]
   bd=sum(abs(rank[ca[q]]-rank[cb[q]]) for q in common)/(len(common)*(len(GRID)-1)) if common else math.nan
   z2=sum(ca[q]!=cb[q] for q in sent)/len(sent)
   z0=.5*(a[2]!=b[2])+.5*(a[3]!=b[3])
   ri=inv[((impl,dataset),(a[2],a[3]),(b[2],b[3]))]
   rows.append({'implementation':impl,'dataset':dataset,'source_seed':a[2],'source_history':a[3],
    'target_seed':b[2],'target_history':b[3],'z0_metadata_distance':z0,
    'z1_distance':'NOT_ESTIMABLE_UNLABELED_FINGERPRINT_NOT_AVAILABLE','z2_labeled_sentinel_distance':z2,
    'budget_distance_complete_case':bd,'rank_inversion':ri,'complete_case_queries':len(common)})

def quantile(xs,p):
 xs=sorted(xs); return xs[min(len(xs)-1,max(0,math.ceil(p*len(xs))-1))]
wit=[]
for grp in sorted(set((r['implementation'],r['dataset']) for r in rows)):
 g=[r for r in rows if (r['implementation'],r['dataset'])==grp]
 zcut=quantile([r['z0_metadata_distance'] for r in g],.25); bcut=quantile([r['budget_distance_complete_case'] for r in g],.75)
 for r in g:
  if r['z0_metadata_distance']<=zcut and r['budget_distance_complete_case']>=bcut:
   wit.append({**r,'z0_near_threshold':zcut,'budget_far_threshold':bcut,'collision_rule':'TRAIN_QUARTILES_FROZEN_WITHIN_IMPLEMENTATION_DATASET'})
wit=sorted(wit,key=lambda r:(-r['budget_distance_complete_case'],r['z0_metadata_distance']))
for name,data in [('build_observable_distance_fast.csv',rows),('build_response_distance_fast.csv',rows),('empirical_collision_witnesses_fast.csv',wit[:20])]:
 tmp=OUT/(name+'.tmp')
 with open(tmp,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 tmp.replace(OUT/name)
print({'directed_pairs':len(rows),'collision_candidates':len(wit),'reported':min(20,len(wit)),'z1':'NOT_ESTIMABLE'})
