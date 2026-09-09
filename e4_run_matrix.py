#!/usr/bin/env python3
import csv,gzip,hashlib,json,os,resource,shutil,struct,subprocess,time
from pathlib import Path
import h5py,numpy as np,yaml
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw'); OUT=Path('/home/wlk/data500/graph_anns_e4')
BIN=ROOT/'build-r0/hnsw_gate_a_benchmark'; EFS='10,20,40,80,120,200'; SEEDS=[83,97,109,127,149,163,181,197]
DS=['sift_100k','arxiv_nomic_100k']; ORDERS=['random','lid_ascending','lid_descending']; EXPECTED_HEAD='9d69be57fb67d566637c19b2c45bce1288d61f3f'
LIDROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-cibs-stage1/results/hardness_portability_100k/lid_orders')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def matrix(p,a):
 a=np.asarray(a,dtype='<f4',order='C')
 with open(p,'wb') as f:f.write(struct.pack('<QQ',*a.shape));a.tofile(f)
def truthbin(p,a):
 a=np.asarray(a,dtype='<u4',order='C')
 with open(p,'wb') as f:f.write(struct.pack('<QQ',*a.shape));a.tofile(f)
def orderbin(p,a):
 with open(p,'wb') as f:f.write(struct.pack('<Q',len(a)));np.asarray(a,dtype='<u4').tofile(f)
def exact(base,q,k=10,batch=16):
 out=np.empty((len(q),k),dtype=np.uint32);bn=np.einsum('ij,ij->i',base,base)
 for s in range(0,len(q),batch):
  z=q[s:s+batch];d=np.einsum('ij,ij->i',z,z)[:,None]+bn[None,:]-2*z@base.T;np.maximum(d,0,out=d)
  ix=np.argpartition(d,k-1,axis=1)[:,:k]
  for i in range(len(z)):out[s+i]=ix[i][np.lexsort((ix[i],d[i,ix[i]]))]
 return out
def peak_run(cmd,stdout,stderr):
 p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'});peak=0
 while p.poll() is None:
  try:
   for line in Path(f'/proc/{p.pid}/status').read_text().splitlines():
    if line.startswith('VmRSS:'):peak=max(peak,int(line.split()[1])*1024)
  except FileNotFoundError:pass
  time.sleep(.1)
 if p.returncode:raise subprocess.CalledProcessError(p.returncode,cmd)
 return peak
def main():
    assert subprocess.run(['git','merge-base','--is-ancestor',EXPECTED_HEAD,'HEAD'],cwd=ROOT).returncode==0
 assert BIN.exists();cfg=yaml.safe_load((ROOT/'configs/gate_a/gate_a_100k.yaml').read_text());OUT.mkdir(parents=True,exist_ok=True)
 access=OUT/'query_access_log.jsonl'; rows=[]
 for ds in DS:
  d=cfg['datasets'][ds];ids=np.load(ROOT/f'manifests/graph_anns_e4_{ds}_confirmatory_ids.npy',allow_pickle=False)
  work=OUT/'inputs'/ds;work.mkdir(parents=True,exist_ok=True);bp=work/'base.f32bin';qp=work/'confirmatory.f32bin';tp=work/'truth.u32bin'
  with h5py.File(ROOT/d['source'],'r') as f:
   base=np.asarray(f['train'][:100000],dtype=np.float32);q=np.asarray(f['train'][ids],dtype=np.float32)
  if d['normalized']:
   base/=np.maximum(np.linalg.norm(base,axis=1,keepdims=True),1e-30);q/=np.maximum(np.linalg.norm(q,axis=1,keepdims=True),1e-30)
  t0=time.time();truth=exact(base,q);matrix(bp,base);matrix(qp,q);truthbin(tp,truth)
  with access.open('a') as f:f.write(json.dumps({'time':time.time(),'dataset':ds,'member':'train','ids_sha256':sha(ROOT/f'manifests/graph_anns_e4_{ds}_confirmatory_ids.npy'),'rows':len(ids),'purpose':'E4_CONFIRMATORY','future_replication_accessed':False,'validation_dev_accessed':False,'formal_test_accessed':False})+'\n')
  lid=np.load(LIDROOT/f'{ds}_order.npy',allow_pickle=False);order_map={'random':np.random.default_rng(20260915).permutation(100000),'lid_ascending':lid,'lid_descending':lid[::-1]}
  for seed in SEEDS:
   for oname in ORDERS:
    run=f'{ds}__seed{seed}__{oname}';rd=OUT/'raw'/run;done=rd/'COMPLETE.json'
    if done.exists():rows.append(json.loads(done.read_text()));continue
    if shutil.disk_usage(OUT).free < 100*2**30:raise RuntimeError('data disk below 100 GiB stop line')
    rd.mkdir(parents=True,exist_ok=True);op=work/f'{oname}.orderbin'
    if not op.exists():orderbin(op,order_map[oname])
    cmd=['taskset','-c','0',str(BIN),str(bp),str(op),str(qp),str(tp),'-','ip' if d['normalized'] else 'l2','16','100',str(seed),ds,'original','-',EFS,'100','5',EXPECTED_HEAD,'e4-cpu0',run,str(rd)]
    with (rd/'stdout.log').open('w') as so,(rd/'stderr.log').open('w') as se:peak=peak_run(cmd,so,se)
    # Preserve raw native measurements compactly and checksum replay artifacts.
    with open(rd/'queries.csv','rb') as fi,gzip.open(rd/'queries.csv.gz','wb',compresslevel=6) as fo:shutil.copyfileobj(fi,fo)
    (rd/'queries.csv').unlink();(rd/'edges.csv').unlink() # index is authoritative replay artifact
    meta=json.loads((rd/'metadata.json').read_text());rec={'dataset':ds,'build_id':run,'seed':seed,'order':oname,'status':'COMPLETE','index_sha256':sha(rd/'index.bin'),'queries_sha256':sha(rd/'queries.csv.gz'),'truth_sha256':sha(tp),'build_seconds':meta['build_seconds'],'peak_rss_bytes':peak,'index_size_bytes':meta['index_size_bytes'],'rows':30000,'confirmatory_queries':1000,'ef_levels':6,'latency_rounds':5}
    done.write_text(json.dumps(rec,indent=2)+'\n');rows.append(rec)
    with (OUT/'progress.json').open('w') as f:json.dump({'complete':len(rows),'total':48,'last':run,'free_gib':shutil.disk_usage(OUT).free/2**30,'time':time.time()},f,indent=2)
  del base,q,truth,lid,order_map
 with (OUT/'build_runs.json').open('w') as f:json.dump(rows,f,indent=2)
 print(json.dumps({'complete':len(rows),'total':48,'passed':len(rows)==48},indent=2))
if __name__=='__main__':main()
