# Generated from the pinned historical E2 function; see provenance.json.
import csv
import json
import os
from pathlib import Path
import struct
import sys
import time

DATASETS = {'sift-1m-heldout': 'sift', 'arxiv-nomic-1.34m-heldout': 'arxiv'}
# np, input_path, load_input and CAMPAIGN are bound by cache_stage.py.


def write_json(p, obj):
    with Path(p).open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())


def write_csv(p, rows):
    assert rows
    with Path(p).open('x', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        f.flush(); os.fsync(f.fileno())


def cache_key(context,query):
    return context+query


def cache_get(cache,context,query):
    # Python bytes equality resolves hash collisions using the full context/query bytes.
    return cache.get(cache_key(context,query))


def cache_bytes(cache):
    return sys.getsizeof(cache)+sum(sys.getsizeof(k)+sys.getsizeof(v) for k,v in cache.items())


def e2(conf,out):
    rows=[];mem=[];correct=[];rawblocks=[]
    for ds,prefix in DATASETS.items():
        qbin=input_path(conf,prefix,'queries')
        blob=qbin.read_bytes();magic,n,dim=struct.unpack('<8sQQ',blob[:24])
        assert n==1000 and len(blob)==24+n*(8+4*dim)
        queries=[];ids=[]
        for i in range(n):
            start=24+i*(8+4*dim);ids.append(struct.unpack('<Q',blob[start:start+8])[0]);queries.append(blob[start+8:start+8+4*dim])
        truth=load_input(conf,prefix,'truth')
        assert np.array_equal(truth['query_ids'],ids)
        assert np.isfinite(truth['scores']).all() and all(len(set(x))==10 for x in truth['neighbor_raw_ids'])
        context_obj=dict(base_version=conf['membership']['sha256'],dataset=ds,
                         metric='squared_l2' if prefix=='sift' else 'inner_product',transform='original_float32_bits',
                         k=10,filter='none',permission='research-role',tie='frozen_exact_top10_order')
        context=json.dumps(context_obj,sort_keys=True,separators=(',',':')).encode()+b'\0'
        values=[truth['neighbor_raw_ids'][i].astype('<i8').tobytes()+truth['scores'][i].astype('<f4').tobytes() for i in range(n)]
        full={cache_key(context,q):v for q,v in zip(queries,values)};assert len(full)==1000
        for q,v in zip(queries,values):assert cache_get(full,context,q)==v
        for field in context_obj:
            changed=dict(context_obj);changed[field]=str(changed[field])+'-changed'
            altered=json.dumps(changed,sort_keys=True,separators=(',',':')).encode()+b'\0'
            assert cache_get(full,altered,queries[0]) is None
        changed_query=bytes([queries[0][0]^1])+queries[0][1:]
        assert cache_get(full,context,changed_query) is None
        # Different Python objects with identical complete bytes must hit.
        assert cache_get(full,context,bytes(bytearray(queries[0])))==values[0]
        correct.append(dict(dataset=ds,all_ids_scores_bit_exact=True,context_miss_controls=len(context_obj),
                            query_bit_miss=True,lookup_semantics='full bytes equality; preloaded immutable exact values',
                            magic_hex=magic.hex(),query_count=1000))
        caches={c:{cache_key(context,queries[i]):values[i] for i in range(c)} for c in [0,100,500,1000]}
        for c,cache in caches.items():
            mem.append(dict(dataset=ds,cached_queries=c,capacity_fraction=c/1000,
                            resident_cache_python_bytes=cache_bytes(cache),key_payload_bytes=sum(len(k) for k in cache),
                            value_payload_bytes=sum(len(v) for v in cache.values()),
                            byte_cap=cache_bytes(cache),admission='first c role queries; fixed static cache'))
        profile=load_input(conf,prefix,'profile')
        mem.append(dict(dataset=ds,cached_queries='TCP-seven-source-full-history',capacity_fraction='',
                        resident_cache_python_bytes='',key_payload_bytes='',value_payload_bytes='',byte_cap='',
                        admission='raw ndarray lower bound per target: hits+ndc+topk on seven source graphs = '+str(sum(profile[k].nbytes for k in ['hits','ndc','topk'])*7//8)+' bytes; model/control excluded'))
        workload=[]
        for c in caches:
            for v in [1,2,10,50,100]:
                for order in ['cyclic','shuffled']:workload.append((c,v,order))
        blocks={key:[] for key in workload};rng=np.random.default_rng(991)
        for rep in range(7):
            for j in rng.permutation(len(workload)):
                c,v,order=workload[j]; sequence=np.tile(np.arange(1000),v)
                if order=='shuffled':sequence=np.random.default_rng(991+v).permutation(sequence)
                seq=[queries[int(i)] for i in sequence];cache=caches[c]
                for q in queries[:100]:cache_get(cache,context,q)
                durations=[];hit=0;start=time.perf_counter_ns()
                for q in seq:
                    t=time.perf_counter_ns();value=cache_get(cache,context,q);durations.append(time.perf_counter_ns()-t)
                    hit+=value is not None
                elapsed=time.perf_counter_ns()-start
                assert hit==c*v and min(durations)>0
                # Batch path excludes per-lookup clock/list costs; includes key construction and value access.
                start=time.perf_counter_ns();batch_hits=sum(cache_get(cache,context,q) is not None for q in seq)
                batch=time.perf_counter_ns()-start;assert batch_hits==hit
                blocks[(c,v,order)].append((elapsed,batch,durations,hit))
                rawblocks.append(dict(dataset=ds,capacity=c,visits=v,order=order,rep=rep,
                                      lookups=len(seq),hits=hit,per_call_timer_batch_wall_ns=elapsed,
                                      batch_lookup_wall_ns=batch,mean_per_call_timer_ns=float(np.mean(durations)),
                                      p95_per_call_timer_ns=float(np.quantile(durations,.95)),
                                      p99_per_call_timer_ns=float(np.quantile(durations,.99))))
            print(json.dumps({'stage':'E2','dataset':ds,'rep':rep}),flush=True)
        for (c,v,order),parts in blocks.items():
            alltimes=np.concatenate([np.asarray(x[2]) for x in parts])
            rows.append(dict(dataset=ds,capacity_queries=c,visits=v,order=order,lookups_per_rep=1000*v,
                             hit_rate=c/1000,mean_batch_lookup_ns=float(np.mean([x[1]/(1000*v) for x in parts])),
                             mean_per_call_timed_ns=float(alltimes.mean()),p95_timed_ns=float(np.quantile(alltimes,.95)),
                             p99_timed_ns=float(np.quantile(alltimes,.99)),repetitions=7,
                             scope='lookup includes full-key construction; scores copied as immutable bytes; miss acquisition excluded'))
        np.savez_compressed(out/(prefix+'_all_lookup_wall_ns.npz'),
                            **{f'capacity{c}_V{v}_{order}':np.asarray([x[2] for x in parts],dtype=np.uint64)
                               for (c,v,order),parts in blocks.items()})
        del full,blocks,profile
    write_csv(out/'cache_lookup_summary.csv',rows);write_csv(out/'cache_memory.csv',mem)
    write_csv(out/'cache_raw_blocks.csv',rawblocks);write_json(out/'cache_correctness.json',correct)
    return {'status':'COMPLETE_NEW_STATIC_EXACT_CACHE_MEASUREMENT','workload_cells':len(rows),
            'raw_blocks':len(rawblocks),'correctness':correct,
            'limitations':['Fixed host single CPU Python bytes dictionary; no production or end-to-end latency claim.',
                           'Static preload; cyclic workloads exceed intermediate capacities; no LRU adaptation.',
                           'Timing inputs use existing query objects; transport/parsing and miss acquisition not measured.',
                           'Memory includes stored dict/bytes objects; temporary query/result buffers and interpreter excluded.']}


def fresh_resources(conf):
    mem={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    total_rss=0;unreadable=0
    for p in Path('/proc').glob('[0-9]*/status'):
        try:
            for line in p.read_text().splitlines():
                if line.startswith('VmRSS:'):total_rss+=int(line.split()[1])*1024
        except (OSError,ValueError):unreadable+=1
    stat=lambda:list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
    first=stat();time.sleep(.2);last=stat();diff=[b-a for a,b in zip(first,last)]
    iowait=diff[4]/sum(diff) if sum(diff)>0 else None
    v=os.statvfs(CAMPAIGN);free=v.f_bavail*v.f_frsize
    assert mem['MemAvailable']>=160*1024**3 and mem['MemAvailable']-conf['resources']['expected_rss_bytes']>=80*1024**3
    assert total_rss+64*1024**3<=.6*mem['MemTotal']
    assert free-conf['resources']['project_growth_bytes']>=200*1024**3
    assert iowait is not None and iowait<.15
    assert 4 in os.sched_getaffinity(0)
    return dict(available_ram_bytes=mem['MemAvailable'],machine_observed_rss_bytes=total_rss,
                unreadable_status_count=unreadable,total_ram_bytes=mem['MemTotal'],disk_free_bytes=free,
                iowait_fraction=iowait,remaining_declared_growth_bytes=conf['resources']['project_growth_bytes'],
                observation='read-only snapshot; no claim of continuous kernel resource quota')
