"""Distinct full500 source-design NDC replay; never a timing measurement."""
import argparse,csv,json,os,platform,signal,sys
from pathlib import Path
from run_transfer import HERE,sha,pin,load
from run_phase import panel,graph,identities,query_binary,truth_input,write,CheckedProcess

def validate(path,ids,grid,original,neighbors,np):
    seen=set();counts=np.empty((len(grid),len(ids)),dtype=np.uint64)
    with path.open(newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['query_id','ef','ndc','topk']:raise ValueError('Replay CSV schema')
        for row in reader:
            ef,qid,count=map(int,(row['ef'],row['query_id'],row['ndc']))
            if ef not in grid or qid not in ids or count<=0:raise ValueError('Action/query/count')
            j=grid.index(ef);i=int(np.flatnonzero(ids==qid)[0]);cell=(j,i)
            if cell in seen:raise ValueError('Duplicate cell')
            seen.add(cell);found=np.asarray(list(map(int,row['topk'].split(';'))),dtype=np.int64)
            hits=len(set(found.tolist())&set(neighbors[i].tolist()));z_abs=hits<10 or bool(original['z_abs'][-1,i])
            if len(found)!=10 or not np.array_equal(found,original['topk'][j,i]) or hits!=int(original['hits'][j,i]) or z_abs!=bool(original['z_abs'][j,i]):raise ValueError('Native equivalence')
            counts[j,i]=count
    if len(seen)!=len(ids)*len(grid):raise ValueError('Missing cells')
    return counts

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('request','output','input-adapter'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-source-counter',action='store_true');a=p.parse_args()
    if not a.authorize_source_counter:p.error('Explicit new source counter opt-in required')
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux3.11 required')
    cfg=json.loads((HERE/'config.json').read_text());pins=json.loads((HERE/'source_counter_pins.json').read_text());req=json.loads(a.request.read_text())
    if req.get('family')!='e1a' or req.get('phase')!='source':raise ValueError('Source-only E1a request')
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2});plan=dict(cfg['resource_plan'],max_output_growth_bytes=128*1024**2,file_size_bytes=128*1024**2,cpu_seconds=600,wall_seconds=900)
    adapter=load(a.input_adapter/'prepare_inputs.py','source_counter_resources',cfg['dependencies']['input_adapter']);out,t=adapter.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,{'request':a.request},a.outstanding_growth_bytes)
    import resource,numpy as np,h5py
    if np.__version__!='1.26.4' or h5py.__version__!='3.11.0':raise ValueError('Library version')
    for k,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,600),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(k);cap=min([cap]+[x for x in old if x>=0]);resource.setrlimit(k,(cap,cap))
    prior=panel(req['source_panel'],'e1a','source',cfg);row,ids,members,_,_=identities(req,cfg,np);source=Path(req['source']);pin(source,row['source_sha256']);g,count,key=graph(req,cfg)
    source_array=Path(prior['units'][key]['directory'])/'response.npz';pin(source_array,cfg['e1a_response_pins']['source'][key]['sha256'])
    neighbors=truth_input(req['truths']['fixed'],req,cfg,ids,np)
    profiles=Path(req['profiles_adapter']);pin(profiles/'config.json',cfg['dependencies']['profiles_config']);pin(profiles/'native_entry.py',cfg['dependencies']['profiles_entry'])
    for file,h in json.loads((profiles/'config.json').read_text())['files'].items():pin(profiles/file,h)
    build=Path(req['native_build']);receipt=json.loads((build/'completed.json').read_text())
    if (build/'failure.json').exists() or receipt['status']!='PASS_NEW_BUILD_AND_SYNTHETIC_NATIVE_CHECKS' or receipt['config_sha256']!=cfg['dependencies']['profiles_config'] or receipt['entry_sha256']!=cfg['dependencies']['profiles_entry']:raise ValueError('New native build receipt')
    binary=build/'replay500';pin(binary,receipt['binaries']['replay500'])
    out.mkdir(mode=0o700);write(out/'start.json',{'status':'NEW_SOURCE_COUNTER_STARTED','request_sha256':sha(a.request),'source_counter_pins_sha256':sha(HERE/'source_counter_pins.json'),'telemetry':t})
    def timeout(s,f):raise TimeoutError('Source counter wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(900)
    try:
        qb=out/'queries.qbin';query_binary(qb,source,ids,np,h5py);pin(qb,pins['qbin'][req['dataset']]['sha256'])
        if qb.stat().st_size!=pins['qbin'][req['dataset']]['bytes']:raise ValueError('Query byte size')
        grid=cfg['action_grid'];csvpath=out/'counter.csv';process=CheckedProcess(out)
        process.run([str(binary),str(g),str(qb),'l2' if req['dataset']=='sift' else 'ip',','.join(map(str,grid)),'500',str(count),str(csvpath)])
        with np.load(source_array,allow_pickle=False) as original:counts=validate(csvpath,ids,grid,original,neighbors,np)
        with (out/'ndc.npz').open('xb') as f:np.savez_compressed(f,query_ids=ids,action_grid=np.asarray(grid),ndc=counts)
        pin(out/'ndc.npz',pins['ndc_arrays'][key])
        write(out/'completed.json',{'status':'NEW_SOURCE_NDC_NATIVE_EQUIVALENT_MATCH_FROZEN_ARRAY','unit':key,'ndc_sha256':sha(out/'ndc.npz'),'qbin_sha256':sha(qb),'csv_sha256':sha(csvpath),'new_native_binary_sha256':sha(binary),'actual_native_exit_code':process.waits[0],'rows':5500,'formal_wall_clock':'NOT_MEASURED','original_pilot_history_recreated':False})
    except BaseException as e:write(out/'failure.json',{'status':'FAILED_STOP_NO_RETRY','error':repr(e)});raise
    finally:signal.alarm(0)

if __name__=='__main__':main()
