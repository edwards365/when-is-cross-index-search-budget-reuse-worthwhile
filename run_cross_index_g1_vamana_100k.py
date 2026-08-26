#!/usr/bin/env python3
import csv,gzip,hashlib,json,os,struct,subprocess,tempfile,time
from pathlib import Path
import h5py,numpy as np
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');BIN=Path('/tmp/g1-rust/target/release/integration-test')
OUT=ROOT/'results/cross_index/g1/main/vamana';OUT.mkdir(parents=True,exist_ok=True);EFS=[10,16,24,32,48,64,96,128,192,256,384,512];STOP=10*1024**3
NORM={'sift_100k':False,'glove100_100k':True,'arxiv_nomic_100k':True}
def fbin(p,a):
 a=np.asarray(a,order='C');
 with open(p,'wb') as f:f.write(struct.pack('<II',*a.shape));a.tofile(f)
def free():s=os.statvfs(ROOT);return s.f_bavail*s.f_frsize
def graph_hash(g):return hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest()
m=json.loads((ROOT/'manifests/cross_index_g1_query_membership.json').read_text());recs={r['dataset']:r for r in m['datasets']};records=[]
for ds in NORM:
 with h5py.File(MAIN/recs[ds]['source_path'],'r') as f:base=np.asarray(f['train'][:100000],dtype=np.float32)
 if NORM[ds]:base/=np.linalg.norm(base,axis=1,keepdims=True)
 q=np.load(ROOT/f'results/cross_index/g1/query_inputs/{ds}_queries.npy');truth=np.load(ROOT/f'results/cross_index/g1/query_inputs/{ds}_truth.npy');order_root=ROOT/'results/hardness_portability_100k/realistic_orders'
 orders={'random':np.random.default_rng(20260915).permutation(100000),'natural_source_order':np.arange(100000),'cluster_block_order':np.load(order_root/f'{ds}_cluster_block_order.npy')}
 with tempfile.TemporaryDirectory(prefix='g1-vamana-100k-',dir='/dev/shm') as td:
  td=Path(td);fbin(td/'queries.fbin',q)
  for history,order in orders.items():
   inverse=np.empty(100000,dtype=np.uint32);inverse[order]=np.arange(100000,dtype=np.uint32);fbin(td/'base.fbin',base[order]);fbin(td/'truth.bin',inverse[truth])
   for seed in (43,59,71):
    run=f'{ds}__seed{seed}__{history}';gz=OUT/f'{run}.csv.gz';mp=OUT/f'{run}.metadata.json'
    if gz.exists() and mp.exists():records.append(json.loads(mp.read_text()));continue
    if free()<STOP:raise RuntimeError('disk below 10 GiB stop line')
    spec={'search_directories':[str(td)],'output_directory':None,'jobs':[{'type':'integration-test','content':{'build':{'alpha':1.2,'l_build':50,'max_degree':32,'pruned_degree':32},'data':{'data':'base.fbin','data_type':'f32','groundtruth':'truth.bin','metric':'cosine' if NORM[ds] else 'l2','queries':'queries.fbin','preprocess':[]},'layer':{'FullPrecision':{'data_type':'f32'}},'search':{'knn':[{'beam_width':None,'knn':10,'search_l':x} for x in EFS]}}}]};(td/'input.json').write_text(json.dumps(spec));out=td/'out.json';t=time.time();subprocess.run([str(BIN),'run','--input-file',str(td/'input.json'),'--output-file',str(out)],check=True,stdout=(td/'stdout.log').open('w'),stderr=(td/'stderr.log').open('w'));elapsed=time.time()-t
    obj=json.loads(out.read_text())[0]['results'];gh=graph_hash(obj['graph']);degrees=[len(x) for x in obj['graph']]
    with gzip.open(gz,'wt',newline='') as f:
     w=csv.writer(f);w.writerow(['dataset','index','history','seed','query_id','query_split','budget','returned_top10_ids','recall_at_10','exact_ndc','graph_hash'])
     for ef,k in zip(EFS,obj['knn']):
      for qi,row in enumerate(k['per_query']):
       labels=order[np.asarray(row['ids'][:10],dtype=np.int64)];recall=len(set(map(int,labels))&set(map(int,truth[qi])))/10;w.writerow([ds,'vamana',history,seed,qi,'design' if qi<250 else 'confirm',ef,';'.join(map(str,labels)),recall,row['misc']['cmps'],gh])
    rec={'dataset':ds,'history':history,'seed':seed,'rows':12000,'graph_hash':gh,'nodes_including_frozen_start':len(degrees),'max_degree':max(degrees),'directed_edges':sum(degrees),'run_seconds':elapsed,'native_cmps':True,'temporary_index_deleted':True,'formal_test_accessed':False,'validation_dev_accessed':False};mp.write_text(json.dumps(rec,indent=2)+'\n');records.append(rec);out.unlink()
(OUT/'runs.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps({'graphs':len(records),'rows':sum(x['rows'] for x in records),'passed':len(records)==27},indent=2))
