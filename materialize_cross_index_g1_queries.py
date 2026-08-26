#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
import h5py,numpy as np
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');sys.path.insert(0,str(ROOT/'python'))
from narhnsw.ground_truth import exact_top_k
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.load(open(ROOT/'manifests/cross_index_g1_query_membership.json'));assert m['status']=='FROZEN_BEFORE_QUERY_VECTOR_READ_OR_ANY_G1_GRAPH';out=ROOT/'results/cross_index/g1/query_inputs'
 if out.exists():raise RuntimeError('refusing to overwrite G1 query inputs')
 out.mkdir(parents=True);records=[]
 for d in m['datasets']:
  ids=np.asarray(d['design_source_ids']+d['confirm_source_ids'],dtype=np.int64);assert hashlib.sha256(ids.astype('<i8').tobytes()).hexdigest()==d['source_ids_le_i64_sha256'];order=np.argsort(ids);inverse=np.argsort(order)
  with h5py.File(MAIN/d['source_path'],'r') as f:q=np.asarray(f['train'][ids[order]],dtype=np.float32)[inverse];base=np.asarray(f['train'][:100000],dtype=np.float32)
  norm='angular' in d['source_path'] or 'normalized' in d['source_path']
  if norm:q/=np.linalg.norm(q,axis=1,keepdims=True);base/=np.linalg.norm(base,axis=1,keepdims=True)
  truth,dist=exact_top_k(base,q,10,metric='l2');paths={n:out/f"{d['dataset']}_{n}.npy" for n in ('queries','truth','truth_distances','source_ids')}
  for n,a in [('queries',q),('truth',truth.astype(np.uint32)),('truth_distances',dist.astype(np.float64)),('source_ids',ids)]:np.save(paths[n],a,allow_pickle=False)
  records.append({'dataset':d['dataset'],'query_count':1000,'design_count':250,'confirm_count':750,'dimensions':q.shape[1],'normalized':norm,**{f'{n}_path':str(p.relative_to(ROOT)) for n,p in paths.items()},**{f'{n}_sha256':sha(p) for n,p in paths.items()}});del q,base,truth,dist
 evidence={'status':'FROZEN_G1_QUERY_TRUTH_BEFORE_ANY_GRAPH','membership_commit':'f8858a9','datasets':records,'base_overlap':0,'prior_query_overlap':0,'formal_test_accessed':False,'validation_dev_accessed':False};(ROOT/'manifests/cross_index_g1_query_truth.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2))
if __name__=='__main__':main()
