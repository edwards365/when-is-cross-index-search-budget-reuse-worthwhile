"""Original successful AVX2 latency core; explicit Faiss binding only."""
import json,os,time
from pathlib import Path
import numpy as np
from audit_e6_faiss_exact_dc_v1 import sha

def own_ancestors():
    seen={os.getpid()};pid=os.getppid()
    while pid>1 and pid not in seen:
        seen.add(pid)
        try:
            s=Path(f'/proc/{pid}/stat').read_text();pid=int(s[s.rfind(')')+2:].split()[1])
        except (FileNotFoundError,ProcessLookupError):break
    return seen

def inventory(exclude,cpu):
    values={};unreadable=0;related=[]
    for p in Path('/proc').glob('[0-9]*'):
        if int(p.name) in exclude:continue
        try:
            command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            if any(x in command for x in ['e6_exact_dc','run_e6_counter_target_panel_v1.py','darth_arxiv_ip','diskann-benchmark','hnsw_test','e2_adaef_native']):related.append(int(p.name))
            for task in (p/'task').iterdir():
                s=(task/'stat').read_text();f=s[s.rfind(')')+2:].split()
                values[int(task.name)]=(int(f[19]),int(f[11])+int(f[12]),int(f[36]))
        except (FileNotFoundError,ProcessLookupError):continue
        except PermissionError:unreadable+=1
    if related:raise ValueError('competing project experiment visible')
    return values,unreadable

def quiet(cpu):
    exclude=own_ancestors();before,unread1=inventory(exclude,cpu);time.sleep(.3);after,unread2=inventory(exclude,cpu)
    busy=[]
    for tid,(tick,total,lastcpu) in after.items():
        if tid in before and tick==before[tid][0] and total>before[tid][1] and cpu in (lastcpu,before[tid][2]):busy.append(tid)
    if busy:raise ValueError('timing CPU competitor sampled: '+str(busy))
    return dict(interval_seconds=.3,competing_sampled_threads=0,unreadable_processes=max(unread1,unread2),
                scope='Observed thread CPU-time/last-processor quiet intervals, not continuous full-host exclusion')

def run(c, faiss):
    cpu=c['cpus'][0]
    if len(c['cpus'])!=1 or c['repetitions']!=5 or c['warmup_queries']!=16:raise ValueError('registered timing design')
    os.sched_setaffinity(0,{cpu});faiss.omp_set_num_threads(1)
    if faiss.__version__!='1.8.0' or faiss.get_compile_options().strip()!='OPTIMIZE AVX2':raise ValueError('original wheel build')
    for p,h in c['pins'].items():
        if sha(p)!=h:raise ValueError('pin '+p)
    # Enforce source counter audit success and the new counter panel closure first.
    panel=json.loads(Path(c['counter_panel_final']).read_text())
    if panel['status']!='PASS_48_TARGET_COUNT_OUTPUTS_AUDITED' or panel['completed']!=48 or len(panel['units'])!=48:raise ValueError('counter output closure not completed')
    if any(u['native_actual_exit']!=0 or u['audit_actual_exit']!=0 for u in panel['units']):raise ValueError('counter native/audit actual wait')
    # One historical monitoring failure is preserved in the closure, not rewritten to worker success.
    q=np.memmap(c['query'],mode='r',dtype='<f4',offset=8,shape=(1000,c['dim']))
    q=np.array(q,dtype=np.float32,order='C',copy=True) # eagerly materialize every query outside timers
    with np.load(c['reference'],allow_pickle=False) as f:
        if not np.array_equal(f['query_ids'],c['query_ids']) or not np.array_equal(f['action_grid'],c['actions']):raise ValueError('role/actions')
        expected=f['topk'].copy()
    index=faiss.read_index(c['index']);core=faiss.downcast_index(index.index)
    if index.ntotal!=c['base_count']:raise ValueError('base count')
    samples=np.empty((len(c['actions']),5,1000),dtype='<i8');returned=np.empty((len(c['actions']),5,1000,10),dtype='<i8');controls=[];telemetry=[]
    print('ORIGINAL_AVX2_RUNTIME_READY_NOT_END_TO_END',flush=True);time.sleep(1)
    for ai,action in enumerate(c['actions']):
        core.hnsw.efSearch=action
        for qi in range(16):
            _,ids=index.search(q[qi:qi+1],10)
            if not np.array_equal(ids[0],expected[ai,qi]):raise ValueError('warmup output equality')
        for repetition in range(5):
            controls.append(quiet(cpu))
            for qi in range(1000):
                start=time.perf_counter_ns();_,ids=index.search(q[qi:qi+1],10);end=time.perf_counter_ns()
                if not np.array_equal(ids[0],expected[ai,qi]):raise ValueError('timed ordered output equality')
                samples[ai,repetition,qi]=end-start
                returned[ai,repetition,qi]=ids[0]
            freq=Path(f'/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_cur_freq')
            telemetry.append(dict(action=action,repetition=repetition,cpu_freq_khz=freq.read_text().strip() if freq.exists() else None))
            print(json.dumps(dict(action=action,repetition=repetition,queries=1000)),flush=True)
    out=Path(c['output']);np.save(out/'latency_ns.npy',samples,allow_pickle=False);np.save(out/'returned_ids.npy',returned,allow_pickle=False)
    result=dict(status='PASS_FIXED_AFFINITY_WARM_RESIDENT_AVX2_API_LATENCY',dataset=c['dataset'],build=c['build'],
                actions=c['actions'],repetitions=5,queries=1000,raw_sha=sha(out/'latency_ns.npy'),
                returned_ids_sha=sha(out/'returned_ids.npy'),
                median_ns_by_action=np.median(samples,axis=(1,2)).tolist(),mean_ns_by_action=np.mean(samples,axis=(1,2)).tolist(),
                quiet_controls=controls,telemetry=telemetry,ordered_outputs_equal=True,
                scope='Single-query Faiss1.8 AVX2 Python index.search API latency includes Python allocation/dispatch; index/query load, SHA checks, output auditing/writes and warmups outside timer',
                not_native_kernel_only=True,not_acquisition_or_lifecycle=True,not_instrumented_counter_time=True,
                environmental_limitations='Fixed CPU/threads; DVFS not changed; quietness sampled, external/system visibility can be incomplete. Not a cross-algorithm or deployment guarantee.')
    with (out/'latency.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    for p,h in c['pins'].items():
        if sha(p)!=h:raise ValueError('post pin '+p)
    return result

