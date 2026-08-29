#!/usr/bin/env python3
import csv,hashlib,json,os
import numpy as np

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
OUT=os.path.join(ROOT,'results/graph_anns_positive_closure');os.makedirs(OUT,exist_ok=True)
MAN=os.path.join(ROOT,'manifests/graph_anns_positive_crossfit_split.json')
datasets=('sift_100k','arxiv_nomic_100k');rng=np.random.default_rng(991);payload={'schema_version':1,'seed':991,'fold_count':4,'fold_size':250,'datasets':{}}
roles=[];audit=[]
role_names=('source_train','source_calibration','target_sentinel','target_evaluation')
for ds in datasets:
 p=rng.permutation(1000);folds=[sorted(map(int,p[i*250:(i+1)*250])) for i in range(4)];payload['datasets'][ds]={'folds':{f'F{i}':f for i,f in enumerate(folds)},'cycles':{}}
 for cycle in range(4):
  assignment={'source_train':cycle,'source_calibration':(cycle+1)%4,'target_sentinel':(cycle+2)%4,'target_evaluation':(cycle+3)%4};payload['datasets'][ds]['cycles'][str(cycle)]={r:f'F{j}' for r,j in assignment.items()}
  sets={r:set(folds[j]) for r,j in assignment.items()}
  for r,s in sets.items():
   for q in sorted(s):roles.append({'dataset':ds,'cycle':cycle,'query_id':q,'role':r,'fold':f'F{assignment[r]}'})
  for i,a in enumerate(role_names):
   for b in role_names[i+1:]:audit.append({'dataset':ds,'cycle':cycle,'role_a':a,'role_b':b,'count_a':len(sets[a]),'count_b':len(sets[b]),'intersection_count':len(sets[a]&sets[b]),'gate':'PASS' if not sets[a]&sets[b] else 'FAIL'})
 for q in range(1000):
  counts={r:sum(1 for x in roles if x['dataset']==ds and x['query_id']==q and x['role']==r) for r in role_names};assert all(v==1 for v in counts.values())
with open(MAN,'w') as f:json.dump(payload,f,indent=2,sort_keys=True)
with open(os.path.join(OUT,'query_roles.csv'),'w',newline='') as f:w=csv.DictWriter(f,fieldnames=roles[0]);w.writeheader();w.writerows(roles)
with open(os.path.join(OUT,'crossfit_overlap_audit.csv'),'w',newline='') as f:w=csv.DictWriter(f,fieldnames=audit[0]);w.writeheader();w.writerows(audit)
h=hashlib.sha256(open(MAN,'rb').read()).hexdigest();open(os.path.join(OUT,'crossfit_split_manifest.sha256'),'w').write(f'{h}  manifests/graph_anns_positive_crossfit_split.json\n')
assert all(r['intersection_count']==0 for r in audit);print('CROSSFIT_FIREWALL_PASS',len(roles),len(audit),h)
