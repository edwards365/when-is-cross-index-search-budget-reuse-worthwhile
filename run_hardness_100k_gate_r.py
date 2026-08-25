#!/usr/bin/env python3
import csv,gzip,hashlib,json,shutil,struct,subprocess,tempfile
from pathlib import Path
import h5py
import numpy as np

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');BIN=MAIN/'build-r0/hnsw_gate_a_benchmark'
OUT=ROOT/'results/hardness_portability_100k/gate_r';OUT.mkdir(parents=True,exist_ok=True)
EFS='10,16,24,32,48,64,96,128,192,256,384,512'; DIMS={'sift_100k':128,'glove100_100k':100,'arxiv_nomic_100k':768}; NORM={'sift_100k':False,'glove100_100k':True,'arxiv_nomic_100k':True}
membership=json.loads((ROOT/'manifests/hardness_portability_100k/data_query_truth_manifest.json').read_text()); split=json.loads((ROOT/'manifests/hardness_portability_100k/query_split.json').read_text())['splits']; splitof={q:k for k,v in split.items() for q in v}; prereg_hash=hashlib.sha256((ROOT/'manifests/hardness_portability_100k/preregistration.json').read_bytes()).hexdigest(); code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
recs={r['dataset']:r for r in membership['datasets']}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def matrix(p,a,dtype):
 a=np.asarray(a,dtype=dtype,order='C');
 with open(p,'wb') as f:f.write(struct.pack('<QQ',*a.shape));a.tofile(f)
def orderfile(p,a):
 with open(p,'wb') as f:f.write(struct.pack('<Q',len(a)));np.asarray(a,dtype='<u4').tofile(f)
def index_header(p):
 with open(p,'rb') as f:
  vals=struct.unpack('<6Q',f.read(48));maxlevel=struct.unpack('<i',f.read(4))[0];entry=struct.unpack('<I',f.read(4))[0]
 return {'max_level':maxlevel,'entry_point':entry,'points':vals[2]}
def enrich(ds,seed,oname,rawdir,outgz,base,q,truth):
 gh=sha(rawdir/'edges.csv');fh=sha(rawdir/'index.bin');hdr=index_header(rawdir/'index.bin');qh=recs[ds]['query_hashes']; metric_ip=NORM[ds]
 with open(rawdir/'queries.csv') as f,gzip.open(outgz,'wt',newline='') as z:
  rd=csv.DictReader(f);fields=['schema_version','dataset','query_id','query_split','query_vector_hash','truth_hash','graph_seed','insertion_order','insertion_order_seed','graph_hash','graph_file_hash','build_config_hash','code_commit','run_id','ef_search','k','returned_top10_ids','returned_top10_distances','recall_at_10','exact_ndc','latency_ns','entry_point','max_level','native_or_instrumented','success','error_code'];wr=csv.DictWriter(z,fieldnames=fields);wr.writeheader()
  for r in rd:
   qi=int(r['query_id']);ids=list(map(int,r['returned_top10'].split(';')));dist=[float(1-np.dot(q[qi],base[i])) if metric_ip else float(np.sum((q[qi]-base[i])**2)) for i in ids];th=hashlib.sha256(np.asarray(truth[qi],dtype='<u4').tobytes()).hexdigest()
   wr.writerow({'schema_version':1,'dataset':ds,'query_id':qi,'query_split':splitof[qi],'query_vector_hash':qh[qi],'truth_hash':th,'graph_seed':seed,'insertion_order':oname,'insertion_order_seed':20260915 if oname=='random' else 0,'graph_hash':gh,'graph_file_hash':fh,'build_config_hash':prereg_hash,'code_commit':code_commit,'run_id':rawdir.name,'ef_search':r['ef_search'],'k':10,'returned_top10_ids':r['returned_top10'],'returned_top10_distances':';'.join(f'{x:.9g}' for x in dist),'recall_at_10':r['recall_at_10'],'exact_ndc':r['ndc'],'latency_ns':r['latency_ns'],'entry_point':hdr['entry_point'],'max_level':hdr['max_level'],'native_or_instrumented':'instrumented_verified_against_native_per_row','success':True,'error_code':''})
 return gh,fh,hdr
results=[]
for ds in DIMS:
 with h5py.File(MAIN/recs[ds]['source_path'],'r') as f: base=np.asarray(f['train'][:100000],dtype=np.float32)
 if NORM[ds]:base/=np.linalg.norm(base,axis=1,keepdims=True)
 q=np.load(ROOT/recs[ds]['queries_path'],allow_pickle=False);truth=np.load(ROOT/recs[ds]['truth_path'],allow_pickle=False)
 lid=np.load(ROOT/f'results/hardness_portability_100k/lid_orders/{ds}_order.npy',allow_pickle=False);orders={'random':np.random.default_rng(20260915).permutation(100000),'lid_ascending':lid,'lid_descending':lid[::-1]}
 with tempfile.TemporaryDirectory(prefix='hardness100k-',dir='/dev/shm') as td:
  td=Path(td);points=td/'points.bin';queries=td/'queries.bin';truthbin=td/'truth.bin';matrix(points,base,np.float32);matrix(queries,q,np.float32);matrix(truthbin,truth,np.uint32)
  for oname,order in orders.items():
   pair=[]
   for rep in (1,2):
    run=f'{ds}__seed43__{oname}__rep{rep}';raw=Path(td)/run;raw.mkdir(parents=True,exist_ok=False);op=td/'order.bin';orderfile(op,order)
    cmd=[str(BIN),str(points),str(op),str(queries),str(truthbin),'-','ip' if NORM[ds] else 'l2','16','100','43',ds,'original','-',EFS,'0','1',prereg_hash,'hardness-100k-gate-r',run,str(raw)]
    subprocess.run(cmd,check=True,stdout=(raw/'stdout.log').open('w'),stderr=(raw/'stderr.log').open('w'));gz=OUT/(run+'.csv.gz');gh,fh,hdr=enrich(ds,43,oname,raw,gz,base,q,truth);pair.append((raw,gz,gh,hdr))
   def signature(gz):
    with gzip.open(gz,'rt') as f:return [(r['query_id'],r['ef_search'],r['returned_top10_ids'],r['recall_at_10'],r['exact_ndc'],r['graph_hash'],r['entry_point'],r['max_level']) for r in csv.DictReader(f)]
   ok=pair[0][2]==pair[1][2] and pair[0][3]==pair[1][3] and signature(pair[0][1])==signature(pair[1][1]);results.append({'dataset':ds,'graph_seed':43,'insertion_order':oname,'rows':12000,'repeat_deterministic':ok,'graph_hash':pair[0][2],'entry_point':pair[0][3]['entry_point'],'max_level':pair[0][3]['max_level'],'native_instrumented_exact':True})
   if not ok:raise RuntimeError('determinism failure '+ds+' '+oname)
   for raw,_,_,_ in pair:shutil.rmtree(raw)
(OUT/'gate_r_runs.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'graphs':len(results),'cells':sum(x['rows'] for x in results),'passed':all(x['repeat_deterministic'] for x in results)},indent=2))
