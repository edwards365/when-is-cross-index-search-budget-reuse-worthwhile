#!/usr/bin/env python3
"""Materialize preregistered validation vectors and exact top-10 evidence."""
import hashlib,json,sys
from pathlib import Path
import h5py,numpy as np
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');sys.path.insert(0,str(ROOT/'python'))
from narhnsw.ground_truth import exact_top_k
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.load(open(ROOT/'manifests/rebuild_tax/validation_split.json'));assert m['status']=='FROZEN_BEFORE_VALIDATION_MEMBER_READ';out=ROOT/'results/rebuild_tax/validation_inputs'
 if out.exists():raise RuntimeError('refusing to overwrite validation inputs')
 out.mkdir(parents=True); rec=[]
 for d in m['datasets']:
  ids=np.asarray(d['calibration_source_ids']+d['audit_source_ids'],dtype=np.int64);assert hashlib.sha256(ids.astype('<i8').tobytes()).hexdigest()==d['source_ids_le_i64_sha256']
  with h5py.File(MAIN/d['source_path'],'r') as f:q=np.asarray(f['train'][ids],dtype=np.float32);base=np.asarray(f['train'][:100000],dtype=np.float32)
  normalized='angular' in d['source_path'] or 'normalized' in d['source_path']
  if normalized:q/=np.linalg.norm(q,axis=1,keepdims=True);base/=np.linalg.norm(base,axis=1,keepdims=True)
  truth,dist=exact_top_k(base,q,10,metric='l2'); paths={n:out/f"{d['dataset']}_{n}.npy" for n in ('queries','truth','truth_distances','source_ids')}
  for n,a in [('queries',q),('truth',truth.astype(np.uint32)),('truth_distances',dist.astype(np.float64)),('source_ids',ids)]:np.save(paths[n],a,allow_pickle=False)
  rec.append({'dataset':d['dataset'],'query_count':2000,'dimensions':q.shape[1],'normalized':normalized,**{f'{n}_path':str(p.relative_to(ROOT)) for n,p in paths.items()},**{f'{n}_sha256':sha(p) for n,p in paths.items()}});del q,base,truth,dist
 evidence={'status':'VALIDATION_INPUTS_MATERIALIZED','datasets':rec,'membership_commit':'052395c','formal_test_accessed':False};(ROOT/'manifests/rebuild_tax/validation_inputs.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2))
if __name__=='__main__':main()
