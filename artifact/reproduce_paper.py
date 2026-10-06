"""Portable reconstruction from saved records, not new ANN or timing measurements."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time

for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import numpy as np

ROOT = Path(__file__).resolve().parent / 'paper'
DATASETS = {'sift': 'sift-1m-heldout', 'arxiv': 'arxiv-nomic-1.34m-heldout'}
METHODS = {'TCP': 'History-Max', 'TG1000': 'TG1000', 'TG500': 'TG500',
           'fixed1600': 'Fixed-1600', 'endpoint2400': 'Endpoint'}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))

def write_csv(path, rows):
    need(bool(rows), 'Empty output: ' + path.name)
    with path.open('x', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def close(actual, expected, label):
    need(math.isfinite(actual) and math.isfinite(expected)
         and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-9), label)

def check_inputs():
    manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    for name, pin in manifest['files'].items():
        path = (ROOT/name).resolve()
        need(path.is_relative_to(ROOT.resolve()), 'Input escapes root')
        raw = path.read_bytes()
        need(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],
             'Input identity mismatch: ' + name)
    return manifest

def graph_intervals(out):
    source = read_csv(ROOT/'inputs/graph_only_query_clusters.csv')
    expected = read_csv(ROOT/'expected/graph_only_marginal_intervals.csv')
    need(len(source) == 3000 and len(expected) == 4, 'Graph panel size')
    records = []
    for frozen in expected:
        key = (frozen['implementation'], frozen['dataset'])
        group = sorted((r for r in source if (r['implementation'], r['dataset']) == key),
                       key=lambda r: int(r['query_id']))
        need(len(group) == 750 and len({r['query_id'] for r in group}) == 750, 'Graph query membership')
        need(all(int(r['directed_pairs']) == 552 for r in group), 'Directed-pair weight')
        x = np.array([[float(r[k]) for k in ('absolute_pair_mean','reference_pair_mean','increment_pair_mean')]
                      for r in group])
        need(np.allclose(x[:,0]-x[:,1], x[:,2], rtol=0, atol=1e-15), 'Graph paired decomposition')
        indices = np.random.default_rng(991).integers(0,750,(5000,750))
        record = {'implementation':key[0], 'dataset':key[1], 'queries':750,
                  'directed_pairs_per_query':552, 'bootstrap_replicates':5000, 'seed':991}
        for j, metric in enumerate(('absolute','reference','incremental')):
            # Same query draw is shared by all three metrics. Graph set is fixed.
            values = [float(x[:,j].mean()), *map(float,np.quantile(x[:,j][indices].mean(axis=1),[.025,.975]))]
            for suffix, value in zip(('risk','ci_low','ci_high'), values):
                column = metric+'_'+suffix
                close(value, float(frozen[column]), 'F02 '+str(key)+' '+column)
                record[column] = value
        records.append(record)
    write_csv(out/'F02_intervals.csv', records)
    return {'groups':4, 'intervals':12, 'input_level':'Saved per-query means over all directed pairs'}

def crossed(matrix):
    need(matrix.shape == (8,1000) and np.isfinite(matrix).all(), 'Paired matrix shape/values')
    rng = np.random.default_rng(991)
    draws = []
    for start in range(0,5000,100):
        n = min(100,5000-start)
        wt = rng.multinomial(8,np.full(8,1/8),size=n)
        wq = rng.multinomial(1000,np.full(1000,1/1000),size=n)
        draws.extend(((wt@matrix*wq).sum(axis=1)/8000).tolist())
    return np.quantile(draws,[.025,.975])

def operating_points(out):
    expected = read_csv(ROOT/'expected/operating_points.csv')
    comparisons = json.loads((ROOT/'expected/comparisons.json').read_text(encoding='utf-8'))
    points, contrasts = [], []
    for prefix, ds in DATASETS.items():
        with np.load(ROOT/'inputs'/f'{prefix}_paired.npz',allow_pickle=False) as archive:
            a = {k:archive[k].copy() for k in archive.files}
        need(len(a['query_ids']) == 1000 and len(set(a['query_ids'].tolist())) == 1000, 'Paired query IDs')
        for method, display in METHODS.items():
            frozen = next(r for r in expected if r['dataset'] == ds and r['method'] == display)
            row = {'dataset':ds, 'method':display, 'deployed_targets':8}
            for metric, field, scale in [('risk','failure_percent',100), ('ndc','mean_distance_computations',1),
                                         ('search_ns','mean_API_ms',1e-6)]:
                matrix = a[method+'_'+metric]
                need(matrix.shape == (8,1000) and np.isfinite(matrix).all(), 'Incomplete locked deployment')
                row[field] = float(matrix.mean())*scale
                close(row[field],float(frozen[field]), 'F04 point '+ds+' '+method+' '+field)
            points.append(row)
        for frozen in (r for r in comparisons if r['dataset'] == ds):
            baseline = frozen['comparison'].removeprefix('TCP-minus-')
            metric = frozen['metric']
            d = a['TCP_'+metric]-a[baseline+'_'+metric]
            point = float(d.mean()); interval = crossed(d)
            close(point,float(frozen['point']), 'F04 paired mean')
            for actual, wanted in zip(interval, frozen['crossed_percentile95']):
                close(float(actual),float(wanted),'F04 paired interval '+ds+' '+baseline+' '+metric)
            graph = d.mean(axis=1)
            for i, wanted in enumerate(frozen['LOTO_means']):
                close(float(np.delete(graph,i).mean()),float(wanted),'F04 leave-one-target-out')
            contrasts.append({'dataset':ds,'comparison':frozen['comparison'],'metric':metric,
                              'point':point,'ci95_low':float(interval[0]),'ci95_high':float(interval[1])})
    need(len(points)==10 and len(contrasts)==24,'Operating-point output set')
    write_csv(out/'F04_operating_points.csv',points)
    write_csv(out/'F04_paired_intervals.csv',contrasts)
    return {'points':10,'paired_intervals':24,'input_level':'Saved locked-policy per-target/query matrices; API times already averaged over seven repeats'}

def costs(out):
    ledger = read_csv(ROOT/'inputs/component_ledger.csv')
    expected = read_csv(ROOT/'expected/F05_plotted_values.csv')
    curves, boundaries = [], []
    for ds in DATASETS.values():
        ep = next(r for r in ledger if r['dataset']==ds and r['method']=='endpoint2400')
        for method, scenario in [('TCP','TCP'),('TCP_deduplicated','TCP_deduplicated')]:
            r = next(r for r in ledger if r['dataset']==ds and r['method']==method)
            B = (float(r['fixed_extra_ns'])+1000*float(r['acquisition_per_distinct_ns']))/1e9
            D = 1000*(float(ep['eight_target_service_ns_per_query'])-float(r['eight_target_service_ns_per_query']))/1e9
            need(B>=0 and D>0,'Unexpected cost-scenario domain')
            first = math.floor(B/D)+1
            need(B-first*D<0 and B-(first-1)*D>=0,'Strict integer repayment')
            for frozen in (a for a in expected if a['dataset']==ds and a['scenario']==scenario):
                V = int(frozen['round'])
                values = {'upfront_seconds':B,'saving_per_round_seconds':D,
                          'component_delta_seconds':B-V*D,'first_strict_round':first}
                for key, value in values.items():
                    close(value,float(frozen[key]),'F05 '+ds+' '+scenario+' '+key)
                curves.append({'dataset':ds,'scenario':scenario,'Q':1000,'round':V,**values})
            boundaries.append({'dataset':ds,'scenario':scenario,'B_seconds':B,'D_seconds':D,
                               'first_strict_round':first,'with_100_seconds_fixed':math.floor((B+100)/D)+1,
                               'recurring_boundary_ms_per_request':D/8000*1000})
    need(len(curves)==len(expected),'F05 scenario coverage')
    write_csv(out/'F05_curves.csv',curves)
    write_csv(out/'F05_overhead_boundaries.csv',boundaries)
    return {'curve_rows':len(curves),'scenarios':4,'input_level':'Saved component ledger; no component remeasurement'}

def lookup(out):
    blocks = read_csv(ROOT/'inputs/cache_raw_blocks.csv')
    expected = read_csv(ROOT/'expected/cache_lookup_summary.csv')
    memory = read_csv(ROOT/'inputs/cache_memory.csv')
    plotted = read_csv(ROOT/'expected/F06_plotted_values.csv')
    records=[]
    for frozen in expected:
        ds, cap, visits, order = frozen['dataset'], int(frozen['capacity_queries']), int(frozen['visits']), frozen['order']
        group=sorted((r for r in blocks if r['dataset']==ds and int(r['capacity'])==cap
                      and int(r['visits'])==visits and r['order']==order),key=lambda r:int(r['rep']))
        need([int(r['rep']) for r in group]==list(range(7)), 'Cache repeat coverage')
        need(all(int(r['lookups'])==1000*visits and int(r['hits'])==cap*visits for r in group),'Cache hit/lookup counts')
        mean=float(np.mean([float(r['batch_lookup_wall_ns'])/int(r['lookups']) for r in group]))
        close(mean,float(frozen['mean_batch_lookup_ns']),'F06 batch mean')
        records.append({'dataset':ds,'capacity_queries':cap,'visits':visits,'order':order,'mean_batch_lookup_ns':mean,'hit_rate':cap/1000})
    values=[]
    for frozen in plotted:
        ds,cap,metric=frozen['dataset'],int(frozen['capacity_queries']),frozen['metric']
        if metric=='mem':
            r=next(r for r in memory if r['dataset']==ds and r['cached_queries']==str(cap))
            value=float(r['resident_cache_python_bytes'])/1e6
        else:
            r=next(r for r in records if r['dataset']==ds and r['capacity_queries']==cap and r['visits']==100 and r['order']=='cyclic')
            value=r['hit_rate'] if metric=='hit' else r['mean_batch_lookup_ns']
        close(value,float(frozen['value']),'F06 '+metric)
        values.append({**frozen,'value':value})
    write_csv(out/'F06_lookup_means.csv',records)
    write_csv(out/'F06_plotted_values.csv',values)
    return {'cells':len(records),'raw_blocks':len(blocks),'input_level':'Batch timing records; memory is the saved object-size measurement, not remeasured',
            'not_reconstructed':'Per-call pooled p95/p99; not plotted in Figure 6'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--check-inputs',action='store_true')
    parser.add_argument('--parts',nargs='+',choices=['F02','F04','F05','F06'],default=['F02','F04','F05','F06'])
    args=parser.parse_args()
    manifest=check_inputs()
    if args.check_inputs:
        print('PASS_PAPER_INPUTS'); return
    need(args.output is not None,'--output required')
    out=args.output.resolve()
    need(not out.exists(),'Output exists; evidence will not be overwritten')
    need(not out.is_relative_to(ROOT.parent.resolve()),'Output must be outside artifact sources')
    out.mkdir(parents=True)
    start=time.monotonic()
    try:
        results={}
        for name,fn in [('F02',graph_intervals),('F04',operating_points),('F05',costs),('F06',lookup)]:
            if name in args.parts:
                results[name]=fn(out)
                (out/'progress.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
        report={'status':'PASS_SAVED_RECORD_RECONSTRUCTION','results':results,'python':platform.python_version(),
                'numpy':np.__version__,'elapsed_seconds':time.monotonic()-start,'ann_runs':0,'timing_measurements':0,
                'recomputed_intervals':(12 if 'F02' in results else 0)+(24 if 'F04' in results else 0),'original_files_modified':False,
                'scope':'Selected paper-figure statistics. Does not reproduce all narrative panels or original ANN generation.'}
        (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,indent=2))
    except Exception as error:
        (out/'failure.json').write_text(json.dumps({'error':str(error),'type':type(error).__name__})+'\n',encoding='utf-8')
        raise

if __name__=='__main__':
    main()
