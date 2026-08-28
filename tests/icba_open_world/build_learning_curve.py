#!/usr/bin/env python3
import csv,gzip,json,itertools
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; RAW=ROOT/'results/cross_index/g1/main'; OUT=ROOT/'results/icba_open_world'; GRID=(10,16,24,32,48,64,96,128,192,256,384,512)
split=json.load(open(ROOT/'manifests/icba_micro_closure_query_split.json'))['datasets']; ep={(r['implementation'],r['dataset'],r['history'],r['seed']):r for r in csv.DictReader(open(ROOT/'results/icba_micro_closure/endpoint_audit.csv'))}
def load(p):
 d=defaultdict(dict); first=None
 with gzip.open(p,'rt',newline='') as f:
  for r in csv.DictReader(f): first=first or r; d[int(r['query_id'])][int(r.get('ef_search') or r.get('budget'))]=float(r['recall_at_10'])
 stable={q:next((b for i,b in enumerate(GRID) if all(c[x]>=.9 for x in GRID[i:])),None) for q,c in d.items()}
 return {'dataset':first['dataset'],'implementation':first.get('index') or p.parent.name,'history':first.get('insertion_order') or first.get('history'),'seed':str(first.get('graph_seed') or first.get('seed')),'hash':first['graph_hash'],'stable':stable}
graphs=[load(p) for p in sorted(RAW.glob('*/*.csv.gz'))]; groups=defaultdict(list)
for g in graphs: groups[(g['dataset'],g['implementation'])].append(g)
acc=defaultdict(lambda:[0,0,0,0,0])
for (ds,im),lib in groups.items():
 if ds=='glove100_100k': continue
 sent=split[ds]['sentinel_query_ids']; ev=split[ds]['evaluation_query_ids']
 for target in lib:
  if ep[(im,ds,target['history'],target['seed'])]['endpoint_status']!='CURRENT_ENDPOINT_CERTIFIABLY_SAFE':continue
  pool=[x for x in lib if x['hash']!=target['hash']]; distances={x['hash']:sum(target['stable'][q]!=x['stable'][q] for q in sent) for x in pool}
  for m in range(2,len(pool)+1):
   for subset in itertools.combinations(pool,m):
    best=min(distances[x['hash']] for x in subset); chosen=[x for x in subset if distances[x['hash']]==best]; fail=0
    for q in ev:
     truth=target['stable'][q]; vals=[x['stable'][q] for x in chosen]; budget=GRID[-1] if any(v is None for v in vals) else max(vals); fail+=truth is None or budget<truth
    a=acc[(ds,im,m)];a[0]+=fail;a[1]+=len(ev);a[2]+=1;a[3]+=best;a[4]+=len(chosen)
rows=[]
for (ds,im,m),(f,n,c,d,a) in sorted(acc.items()): rows.append({'dataset':ds,'implementation':im,'historical_builds_m':m,'target_subset_cells':c,'queries_evaluated':n,'under_failures':f,'under_rate':f/n,'mean_nearest_sentinel_distance':d/c,'mean_ambiguity_size':a/c,'independent_target_builds':9,'label':'EXHAUSTIVE_FINITE_LIBRARY_SUBSETS'})
tmp=OUT/'build_learning_curve.csv.tmp'
with open(tmp,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
tmp.replace(OUT/'build_learning_curve.csv');print(*rows,sep='\n')
