#!/usr/bin/env python3
import csv,gzip,json,random,math
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'results/cross_index/g1/main'; OUT=ROOT/'results/icba_open_world'
GRID=(10,16,24,32,48,64,96,128,192,256,384,512); KS=(32,64,128,256); REPS=300; SEED=991
split=json.load(open(ROOT/'manifests/icba_micro_closure_query_split.json'))['datasets']
end={(r['implementation'],r['dataset'],r['history'],r['seed']):r for r in csv.DictReader(open(ROOT/'results/icba_micro_closure/endpoint_audit.csv'))}

def load(path):
 d=defaultdict(dict); first=None
 with gzip.open(path,'rt',newline='') as f:
  for r in csv.DictReader(f):
   first=first or r; d[int(r['query_id'])][int(r.get('ef_search') or r.get('budget'))]=float(r['recall_at_10'])
 stable={q:next((b for i,b in enumerate(GRID) if all(c[x]>=.9 for x in GRID[i:])),None) for q,c in d.items()}
 return {'dataset':first['dataset'],'implementation':first.get('index') or path.parent.name,
  'history':first.get('insertion_order') or first.get('history'),
  'seed':str(first.get('graph_seed') or first.get('seed')),'hash':first['graph_hash'],'stable':stable}

graphs=[load(p) for p in sorted(RAW.glob('*/*.csv.gz'))]
groups=defaultdict(list)
for g in graphs: groups[(g['dataset'],g['implementation'])].append(g)
rng=random.Random(SEED); acc=defaultdict(lambda:[0,0,0,0])
for (dataset,impl), library in groups.items():
 sent=split[dataset]['sentinel_query_ids']; ev=split[dataset]['evaluation_query_ids']
 for target in library:
  if end[(impl,dataset,target['history'],target['seed'])]['endpoint_status']!='CURRENT_ENDPOINT_CERTIFIABLY_SAFE': continue
  pool=[x for x in library if x['hash']!=target['hash']]
  mismatch=[[target['stable'][q]!=x['stable'][q] for q in sent] for x in pool]
  for k in KS:
   for _ in range(REPS):
    ids=rng.sample(range(len(sent)),k)
    ds=[sum(mm[i] for i in ids) for mm in mismatch]; best=min(ds); chosen=[pool[i] for i,v in enumerate(ds) if v==best]
    fail=0
    for q in ev:
     truth=target['stable'][q]; vals=[x['stable'][q] for x in chosen]
     budget=GRID[-1] if any(v is None for v in vals) else max(vals)
     fail += truth is None or budget<truth
    a=acc[(dataset,impl,k)]; a[0]+=fail; a[1]+=len(ev); a[2]+=1; a[3]+=len(chosen)
rows=[]
for (dataset,impl,k),(fail,n,reps,ambiguity) in sorted(acc.items()):
 rows.append({'dataset':dataset,'implementation':impl,'sentinel_k':k,'replicate_build_cells':reps,
  'queries_evaluated':n,'under_failures':fail,'under_rate':fail/n,'mean_ambiguity_size':ambiguity/reps,
  'master_seed':SEED,'subsamples_per_build':REPS,'lane':'LABELED_TARGET_SENTINEL_NON_DEPLOYABLE'})
tmp=OUT/'sentinel_learning_curve_fast.csv.tmp'
with open(tmp,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
tmp.replace(OUT/'sentinel_learning_curve_fast.csv')
print(json.dumps(rows,indent=2))
