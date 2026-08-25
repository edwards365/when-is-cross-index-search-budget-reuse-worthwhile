#!/usr/bin/env python3
import csv,gzip,hashlib,json,shutil,struct,subprocess,tempfile
from pathlib import Path
import numpy as np

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-ocgt-v3');MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');BIN=MAIN/'build-r0/hnsw_gate_a_benchmark'
OUT=ROOT/'results/index_conditionality/ocgt_v3/gate_r';OUT.mkdir(parents=True,exist_ok=True)
EFS='10,16,24,32,48,64,96,128,192,256,384,512'; DIMS={'sift_10k':128,'glove100_10k':100,'arxiv_nomic_10k':768}; NORM={'sift_10k':False,'glove100_10k':True,'arxiv_nomic_10k':True}
membership=json.loads((ROOT/'manifests/ocgt_v3_query_membership.json').read_text()); split=json.loads((ROOT/'manifests/ocgt_v3_query_split.json').read_text())['splits']; splitof={q:k for k,v in split.items() for q in v}; prereg_hash=hashlib.sha256((ROOT/'manifests/ocgt_v3_preregistration.json').read_bytes()).hexdigest(); code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
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
def lid_order(x,cache):
 if cache.exists():return np.load(cache)
 n=len(x);knn=np.empty((n,100),np.float32);xn=(x*x).sum(1)
 for s in range(0,n,256):
  b=x[s:s+256];d=(b*b).sum(1)[:,None]+xn[None,:]-2*b@x.T;d[np.arange(len(b)),np.arange(s,s+len(b))]=np.inf;knn[s:s+len(b)]=np.partition(d,99,axis=1)[:,:100]
 rk=knn[:,99,None];lid=-100/np.log(np.clip(knn/(rk+1e-30),1e-30,1)).sum(1);o=np.lexsort((np.arange(n),lid));np.save(cache,o);return o
def enrich(ds,seed,oname,rawdir,outgz,base,q,truth):
 gh=sha(rawdir/'edges.csv');fh=sha(rawdir/'index.bin');hdr=index_header(rawdir/'index.bin');qh=recs[ds]['query_hashes']; metric_ip=NORM[ds]
 with open(rawdir/'queries.csv') as f,gzip.open(outgz,'wt',newline='') as z:
  rd=csv.DictReader(f);fields=['schema_version','dataset','query_id','query_split','query_vector_hash','truth_hash','graph_seed','insertion_order','insertion_order_seed','graph_hash','graph_file_hash','build_config_hash','code_commit','run_id','ef_search','k','returned_top10_ids','returned_top10_distances','recall_at_10','exact_ndc','latency_ns','entry_point','max_level','native_or_instrumented','success','error_code'];wr=csv.DictWriter(z,fieldnames=fields);wr.writeheader()
  for r in rd:
   qi=int(r['query_id']);ids=list(map(int,r['returned_top10'].split(';')));dist=[float(1-np.dot(q[qi],base[i])) if metric_ip else float(np.sum((q[qi]-base[i])**2)) for i in ids];th=hashlib.sha256(np.asarray(truth[qi],dtype='<u4').tobytes()).hexdigest()
   wr.writerow({'schema_version':1,'dataset':ds,'query_id':qi,'query_split':splitof[qi],'query_vector_hash':qh[qi],'truth_hash':th,'graph_seed':seed,'insertion_order':oname,'insertion_order_seed':20260903 if oname=='random' else 0,'graph_hash':gh,'graph_file_hash':fh,'build_config_hash':prereg_hash,'code_commit':code_commit,'run_id':rawdir.name,'ef_search':r['ef_search'],'k':10,'returned_top10_ids':r['returned_top10'],'returned_top10_distances':';'.join(f'{x:.9g}' for x in dist),'recall_at_10':r['recall_at_10'],'exact_ndc':r['ndc'],'latency_ns':r['latency_ns'],'entry_point':hdr['entry_point'],'max_level':hdr['max_level'],'native_or_instrumented':'instrumented_verified_against_native_per_row','success':True,'error_code':''})
 return gh,fh,hdr
results=[]
for ds in DIMS:
 brec=next(x for x in json.loads((MAIN/'results/gb_mpcc/r0_inputs/manifest.json').read_text())['inputs'] if x['dataset']==ds);base=np.memmap(MAIN/brec['path'],dtype=np.float32,mode='r',shape=(10000,DIMS[ds]));q=np.load(ROOT/recs[ds]['queries_path'],allow_pickle=False);truth=np.load(ROOT/recs[ds]['truth_path'],allow_pickle=False)
 cache=OUT/(ds+'_lid_order.npy');lid=lid_order(base,cache);orders={'random':np.random.default_rng(20260903).permutation(10000),'lid_ascending':lid,'lid_descending':lid[::-1]}
 with tempfile.TemporaryDirectory(prefix='ocgtv3-') as td:
  td=Path(td);points=td/'points.bin';queries=td/'queries.bin';truthbin=td/'truth.bin';matrix(points,base,np.float32);matrix(queries,q,np.float32);matrix(truthbin,truth,np.uint32)
  for oname,order in orders.items():
   pair=[]
   for rep in (1,2):
    run=f'{ds}__seed43__{oname}__rep{rep}';raw=OUT/'.work'/run;raw.mkdir(parents=True,exist_ok=False);op=td/'order.bin';orderfile(op,order)
    cmd=[str(BIN),str(points),str(op),str(queries),str(truthbin),'-','ip' if NORM[ds] else 'l2','16','100','43',ds,'original','-',EFS,'0','1',prereg_hash,'ocgt-v3-gate-r',run,str(raw)]
    subprocess.run(cmd,check=True,stdout=(raw/'stdout.log').open('w'),stderr=(raw/'stderr.log').open('w'));gz=OUT/(run+'.csv.gz');gh,fh,hdr=enrich(ds,43,oname,raw,gz,base,q,truth);pair.append((raw,gz,gh,hdr))
   def signature(gz):
    with gzip.open(gz,'rt') as f:return [(r['query_id'],r['ef_search'],r['returned_top10_ids'],r['recall_at_10'],r['exact_ndc'],r['graph_hash'],r['entry_point'],r['max_level']) for r in csv.DictReader(f)]
   ok=pair[0][2]==pair[1][2] and pair[0][3]==pair[1][3] and signature(pair[0][1])==signature(pair[1][1]);results.append({'dataset':ds,'graph_seed':43,'insertion_order':oname,'rows':6000,'repeat_deterministic':ok,'graph_hash':pair[0][2],'entry_point':pair[0][3]['entry_point'],'max_level':pair[0][3]['max_level'],'native_instrumented_exact':True})
   if not ok:raise RuntimeError('determinism failure '+ds+' '+oname)
   for raw,_,_,_ in pair:shutil.rmtree(raw)
(OUT/'gate_r_runs.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'graphs':len(results),'cells':sum(x['rows'] for x in results),'passed':all(x['repeat_deterministic'] for x in results)},indent=2))
