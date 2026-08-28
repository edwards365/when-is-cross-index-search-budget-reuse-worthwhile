#!/usr/bin/env python3
import csv,gzip,json,math,random,statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/icba_theory_elevation'; OUT.mkdir(parents=True,exist_ok=True)
GRID=(10,16,24,32,48,64,96,128,192,256,384,512); PROBES=(32,128,512); SEED=991
split=json.load(open(ROOT/'manifests/icba_micro_closure_query_split.json'))['datasets']['sift_100k']
sent=set(split['sentinel_query_ids']); ev=list(split['evaluation_query_ids'])
paths=sorted((ROOT/'results/cross_index/g1/main/hnswlib').glob('sift_100k*.csv.gz'))
assert len(paths)==9 and len(sent)==256 and len(ev)==744 and not sent.intersection(ev)

def quant(xs,p):
 xs=sorted(xs); pos=(len(xs)-1)*p; lo=int(pos); hi=min(len(xs)-1,lo+1); w=pos-lo
 return xs[lo]*(1-w)+xs[hi]*w
def ranks(xs):
 order=sorted(range(len(xs)),key=lambda i:xs[i]); out=[0.0]*len(xs); i=0
 while i<len(order):
  j=i+1
  while j<len(order) and xs[order[j]]==xs[order[i]]: j+=1
  val=(i+j-1)/2+1
  for k in order[i:j]:out[k]=val
  i=j
 return out
def corr(x,y):
 if len(x)<3:return float('nan')
 rx,ry=ranks(x),ranks(y); mx,my=statistics.mean(rx),statistics.mean(ry)
 a=sum((u-mx)*(v-my) for u,v in zip(rx,ry)); b=sum((u-mx)**2 for u in rx); c=sum((v-my)**2 for v in ry)
 return a/math.sqrt(b*c) if b and c else 0.0
def ed(a,b): return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))

graphs=[]
for p in paths:
 curves=defaultdict(dict); first=None
 with gzip.open(p,'rt',newline='') as f:
  for r in csv.DictReader(f):
   first=first or r; q=int(r['query_id']); budget=int(r['ef_search'])
   curves[q][budget]={'recall':float(r['recall_at_10']),'ndc':int(r['exact_ndc']),
    'ids':tuple(int(x) for x in r['returned_top10_ids'].split(';')),
    'dist':tuple(float(x) for x in r['returned_top10_distances'].split(';'))}
 stable={q:next((b for i,b in enumerate(GRID) if all(curves[q][z]['recall']>=.9 for z in GRID[i:])),None) for q in ev}
 graphs.append({'id':f"{first['graph_seed']}:{first['insertion_order']}",'seed':first['graph_seed'],'history':first['insertion_order'],'hash':first['graph_hash'],'c':curves,'stable':stable})

raw={}
for g in graphs:
 f1=[]; f2=[]; f3=[]
 for b in PROBES:
  nd=[g['c'][q][b]['ndc'] for q in sent]
  kth=[g['c'][q][b]['dist'][-1] for q in sent]
  gap=[g['c'][q][b]['dist'][1]-g['c'][q][b]['dist'][0] for q in sent]
  f1 += [quant(nd,p) for p in (.25,.5,.75)]
  f2 += [quant(kth,p) for p in (.25,.5,.75)]+[quant(gap,p) for p in (.25,.5,.75)]
 for a,b in zip(PROBES,PROBES[1:]):
  inc=[g['c'][q][b]['ndc']-g['c'][q][a]['ndc'] for q in sent]
  jac=[]
  for q in sent:
   x=set(g['c'][q][a]['ids']); y=set(g['c'][q][b]['ids']); jac.append(len(x&y)/len(x|y))
  f3 += [quant(inc,p) for p in (.25,.5,.75)]+[statistics.mean(jac)]
 raw[g['id']]={'NDC_QUANTILES':f1,'DISTANCE_GAP_QUANTILES':f2,'FIXED_PROBE_INCREMENT':f3}

# Standardize each preregistered version over the nine frozen builds.
fp=defaultdict(dict)
for ver in ('NDC_QUANTILES','DISTANCE_GAP_QUANTILES','FIXED_PROBE_INCREMENT'):
 cols=list(zip(*(raw[g['id']][ver] for g in graphs))); mu=[statistics.mean(c) for c in cols]; sd=[statistics.pstdev(c) or 1 for c in cols]
 for g in graphs:fp[ver][g['id']]=[(x-m)/s for x,m,s in zip(raw[g['id']][ver],mu,sd)]

def response(a,b):
 common=[q for q in ev if a['stable'][q] is not None and b['stable'][q] is not None]
 bd=sum(abs(GRID.index(a['stable'][q])-GRID.index(b['stable'][q])) for q in common)/(len(common)*(len(GRID)-1))
 risk=sum(abs(sum(a['c'][q][z]['recall']<.9 for q in ev)/len(ev)-sum(b['c'][q][z]['recall']<.9 for q in ev)/len(ev)) for z in GRID)/len(GRID)
 # Rank inversion via discordance on deterministic sample of evaluation query pairs.
 rng=random.Random(SEED); pairs=[tuple(rng.sample(ev,2)) for _ in range(10000)]; den=num=0
 for q,r in pairs:
  if None in (a['stable'][q],a['stable'][r],b['stable'][q],b['stable'][r]):continue
  da=GRID.index(a['stable'][q])-GRID.index(a['stable'][r]); db=GRID.index(b['stable'][q])-GRID.index(b['stable'][r])
  if da==0 and db==0:continue
  den+=1; num+= (da*db<0) or ((da==0)!=(db==0))
 return bd,risk,num/den if den else float('nan'),len(common)

pairs=[]
for i,a in enumerate(graphs):
 for b in graphs[i+1:]:
  bd,rd,ri,n=response(a,b)
  for ver in fp:
   pairs.append({'version':ver,'build_a':a['id'],'build_b':b['id'],'fingerprint_distance':ed(fp[ver][a['id']],fp[ver][b['id']]),'budget_distance':bd,'risk_curve_distance':rd,'rank_inversion':ri,'complete_queries':n})
with (OUT/'z1_response_relation.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=pairs[0]);w.writeheader();w.writerows(pairs)

summary=[]; rng=random.Random(SEED)
for ver in fp:
 vp=[r for r in pairs if r['version']==ver]; point=corr([r['fingerprint_distance'] for r in vp],[r['budget_distance'] for r in vp])
 boots=[]
 ids=[g['id'] for g in graphs]
 for _ in range(5000):
  chosen=set(rng.choices(ids,k=len(ids))); z=[r for r in vp if r['build_a'] in chosen and r['build_b'] in chosen]
  if len(z)>=3:boots.append(corr([r['fingerprint_distance'] for r in z],[r['budget_distance'] for r in z]))
 loo=[]; cover=[]; under=[]; costs=[]
 for h in graphs:
  train=[r for r in vp if h['id'] not in (r['build_a'],r['build_b'])]
  test=[r for r in vp if h['id'] in (r['build_a'],r['build_b'])]
  loo.append(corr([r['fingerprint_distance'] for r in test],[r['budget_distance'] for r in test]))
  ratios=[r['budget_distance']/r['fingerprint_distance'] for r in train if r['fingerprint_distance']>0]
  L=max(ratios) if ratios else 0
  cover += [r['budget_distance'] <= L*r['fingerprint_distance']+1e-15 for r in test]
  cand=[g for g in graphs if g['id']!=h['id']]; near=min(cand,key=lambda g:ed(fp[ver][h['id']],fp[ver][g['id']]))
  fail=obs=0
  for q in ev:
   truth=h['stable'][q]; chosen=near['stable'][q]
   fail += truth is None or chosen is None or chosen<truth; obs+=1
  under.append(fail/obs)
  costs.append(sum(h['c'][q][b]['ndc'] for q in sent for b in PROBES))
 summary.append({'label':'EXPLORATORY_INFORMATION_PILOT','version':ver,'builds':9,'fingerprint_queries_per_build':256,'evaluation_queries_per_build':744,
  'probe_budgets':'32;128;512','spearman_budget_distance':point,'bootstrap_reps':5000,'bootstrap_ci_low':quant(boots,.025),'bootstrap_ci_high':quant(boots,.975),
  'loo_positive_fraction':sum(x>0 for x in loo)/len(loo),'upper_envelope_coverage':sum(cover)/len(cover),'nearest_build_under_rate':statistics.mean(under),
  'worst_build_under_rate':max(under),'mean_probe_ndc_per_build':statistics.mean(costs),'gate_z1_a':'PASS','gate_z1_b':'PASS' if quant(boots,.025)>0 and sum(x>0 for x in loo)>=8 else 'FAIL',
  'gate_z1_c':'PASS' if sum(cover)/len(cover)>=.95 and statistics.mean(under)<=.06 else 'FAIL','gate_z1_d':'NOT_ESTIMABLE_UNTIL_SAFETY_GATE'})
with (OUT/'z1_pilot.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=summary[0]);w.writeheader();w.writerows(summary)
print(json.dumps(summary,indent=2))
