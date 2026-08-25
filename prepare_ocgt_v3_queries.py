#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
import h5py,numpy as np,yaml

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-ocgt-v3')
MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
sys.path.insert(0,str(ROOT/'python'))
from narhnsw.ground_truth import exact_top_k
OUT=ROOT/'results/index_conditionality/ocgt_v3/query_inputs';OUT.mkdir(parents=True,exist_ok=False)
cfg=yaml.safe_load((ROOT/'configs/gate_a/gate_a_100k.yaml').read_text())
names={'sift_10k':'sift_100k','glove100_10k':'glove100_100k','arxiv_nomic_10k':'arxiv_nomic_100k'}
r0=json.loads((MAIN/'results/gb_mpcc/r0_inputs/manifest.json').read_text())
records=[]
for offset,(ds,key) in enumerate(names.items()):
 d=cfg['datasets'][key]; src=MAIN/d['source']; design_ids=np.load(MAIN/d['query_source_ids'],allow_pickle=False)
 rng=np.random.default_rng(20260901+offset); pool=np.setdiff1d(np.arange(10000,100000,dtype=np.int64),design_ids,assume_unique=False); ids=np.sort(rng.choice(pool,500,replace=False))
 with h5py.File(src,'r') as f: q=np.asarray(f['train'][ids],dtype=np.float32)
 if d['normalized']: q/=np.linalg.norm(q,axis=1,keepdims=True)
 brec=next(x for x in r0['inputs'] if x['dataset']==ds); base=np.memmap(MAIN/brec['path'],dtype=np.float32,mode='r',shape=(10000,brec['dimensions']))
 bh={hashlib.sha256(np.ascontiguousarray(x).tobytes()).digest() for x in base}; qh=[hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest() for x in q]
 if len(set(qh))!=500 or any(bytes.fromhex(h) in bh for h in qh): raise RuntimeError(ds+' query overlap/duplicate')
 truth,td=exact_top_k(base,q,10,metric='l2');truth=truth.astype(np.uint32);td=td.astype(np.float64)
 qp=OUT/(ds+'_queries.npy');tp=OUT/(ds+'_truth.npy');dp=OUT/(ds+'_truth_distances.npy');ip=OUT/(ds+'_source_ids.npy')
 for p,a in [(qp,q),(tp,truth),(dp,td),(ip,ids)]:np.save(p,a,allow_pickle=False)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 records.append({'dataset':ds,'source_path':str(d['source']),'source_sha256':d['source_sha256'],'source_member':'train','selection_seed':20260901,'seed_offset':offset,'source_id_range':[10000,100000],'source_ids_path':str(ip.relative_to(ROOT)),'source_ids_sha256':sha(ip),'queries_path':str(qp.relative_to(ROOT)),'queries_sha256':sha(qp),'truth_path':str(tp.relative_to(ROOT)),'truth_sha256':sha(tp),'truth_distances_path':str(dp.relative_to(ROOT)),'truth_distances_sha256':sha(dp),'query_count':500,'base_size':10000,'dimensions':brec['dimensions'],'normalized':d['normalized'],'query_hashes':qh,'unique_queries':True,'base_overlap_count':0,'design_source_id_overlap_count':int(np.isin(ids,design_ids).sum()),'formal_test_accessed':False})
split_rng=np.random.default_rng(20260902); perm=split_rng.permutation(500); split={'calibration':sorted(map(int,perm[:125])),'confirmatory_audit':sorted(map(int,perm[125:]))}
membership={'schema_version':1,'protocol':'OCGT-v3','status':'FROZEN_FALLBACK_QUERY_MEMBERSHIP','datasets':records,'validation_dev_found':False,'fallback_used':True,'formal_test_accessed':False}
mp=ROOT/'manifests/ocgt_v3_query_membership.json';sp=ROOT/'manifests/ocgt_v3_query_split.json';mp.write_text(json.dumps(membership,indent=2)+'\n');sp.write_text(json.dumps({'schema_version':1,'protocol':'OCGT-v3','seed':20260902,'rng':'numpy.random.Generator(PCG64)','permutation_sha256':hashlib.sha256(np.asarray(perm,dtype='<u4').tobytes()).hexdigest(),'splits':split,'same_ids_across_graphs':True},indent=2)+'\n')
print(json.dumps({'datasets':[(r['dataset'],r['queries_sha256'],r['truth_sha256']) for r in records],'split_counts':{k:len(v) for k,v in split.items()}},indent=2))
