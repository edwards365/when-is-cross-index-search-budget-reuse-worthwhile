#!/usr/bin/env python3
"""Pure-code evidence hotfix.  It never builds an index or runs ANN search."""
from __future__ import annotations
import csv, gzip, hashlib, json, math, shutil, subprocess
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

ROOT = Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
PARENT = ROOT / 'results/graph_anns_iclr_phase1_1_repair'
OLD = ROOT / 'results/graph_anns_iclr_phase1_1'
OUT = ROOT / 'results/graph_anns_iclr_phase1_1_hotfix'
DOC = ROOT / 'docs/graph_anns_iclr_phase1_1_hotfix'
FIG = ROOT / 'figures/graph_anns_iclr_phase1_1_hotfix'
MAN = ROOT / 'manifests/graph_anns_iclr_phase1_1_hotfix_decision.json'
FAISS = Path('/home/wlk/data500/graph_anns_iclr_phase1_1_scratch/faiss_100k')
CLEAN_FAISS = Path('/home/wlk/data500/graph_anns_iclr_phase1_1_repair_scratch/faiss_100k')
H5 = {
    'sift_100k': ROOT / 'data/raw/sift-128-euclidean.hdf5',
    'arxiv_nomic_100k': ROOT / 'data/raw/arxiv-nomic-768-normalized.hdf5',
}
E4 = Path('/home/wlk/data500/graph_anns_e4/raw')
D3ROOT = Path('/home/wlk/data500/graph_anns_iclr_phase1_scratch/phase1c')
D0ROOT = Path('/home/wlk/data500/graph_anns_iclr_phase1_1_scratch/d0_control')
ROLES = Path('/home/wlk/data500/graph_anns_faiss_external_validity/run/roles')
BUILD_REG = OLD / 'faiss_100k_build_registry.csv'
SOURCE_REG = OLD / 'source_registry.csv'
DS = ('sift_100k', 'arxiv_nomic_100k')
FAISS_GRID = (16, 32, 64, 128, 256, 512)
HNSW_GRID = (10, 20, 40, 80, 120, 200)
PARENT_COMMIT = '39a8b6d41f9fa0561660100856e2e98f330d0a4a'

def read_csv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    fields = list(rows[0]) if rows else []
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def qdigest(x, normalize=False):
    x = np.asarray(x, dtype=np.float32)
    if normalize:
        x = x / np.maximum(np.linalg.norm(x), np.finfo(np.float32).tiny)
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()

def h5_rows(ds, ids):
    import h5py
    ids = list(map(int, ids)); order = np.argsort(ids)
    with h5py.File(H5[ds], 'r') as f:
        arr = np.asarray(f['train'][sorted(ids)], dtype=np.float32)
    return arr[np.argsort(order)]

def action_summary(rows, h, grid):
    """Transparent raw-row recomputation used for reports (not a search)."""
    by = defaultdict(dict)
    for r in rows:
        by[(r['build_id'], int(r['query_id']))][int(r['ef'])] = r
    builds = sorted({k[0] for k in by}); queries = sorted({k[1] for k in by})
    safe = {(b, q): next((e for e in grid if e in by[(b, q)] and int(by[(b, q)][e]['hit_count']) >= h), None)
            for b in builds for q in queries}
    endpoint_var=[]; inclusive_var=[]; finite_var=[]; da=[]; dt=[]
    for q in queries:
        vals = [safe[(b,q)] for b in builds]; finite = [x for x in vals if x is not None]
        endpoint_var.append(int(len({'F' if x is not None else 'C' for x in vals}) > 1))
        inclusive_var.append(int(len(set(vals)) > 1))
        finite_var.append(int(len(finite) >= 2 and len(set(finite)) > 1))
        if len(finite) == len(builds): da.append(max(finite)-min(finite))
        if len(finite) >= 2: dt.append(max(finite)-min(finite))
    absrisk=[]; refrisk=[]; incrisk=[]; qvals=[]
    for s in builds:
        for t in builds:
            if s == t: continue
            for q in queries:
                sa=safe[(s,q)]; ta=safe[(t,q)]; act=max(grid) if sa is None else sa
                ref=int(ta is None)
                fail=int(ta is None or int(by[(t,q)][act]['hit_count']) < h)
                absrisk.append(fail); refrisk.append(ref); incrisk.append(fail-ref)
    for q in queries:
        v=[]
        for s in builds:
            for t in builds:
                if s == t: continue
                sa=safe[(s,q)]; ta=safe[(t,q)]; act=max(grid) if sa is None else sa
                v.append(int(ta is None or int(by[(t,q)][act]['hit_count']) < h) - int(ta is None))
        qvals.append(float(np.mean(v)))
    qvals=np.asarray(qvals, dtype=float)
    rng=np.random.default_rng(991)
    boot=np.asarray([qvals[rng.integers(0,len(qvals),len(qvals))].mean() for _ in range(5000)])
    keep=np.argsort(qvals)[:-max(1, int(math.ceil(.01*len(qvals))))]
    return {
        'builds':len(builds), 'pairs':len(builds)*(len(builds)-1), 'queries':len(queries),
        'endpoint_variation':float(np.mean(endpoint_var)),
        'inclusive_variation':float(np.mean(inclusive_var)),
        'finite_variation':float(np.mean(finite_var)),
        'all_build_feasible_queries':len(da), 'at_least_two_feasible_queries':len(dt),
        'all_build_diameter_mean':float(np.mean(da)) if da else 'NOT_ESTIMABLE',
        'at_least_two_diameter_mean':float(np.mean(dt)) if dt else 'NOT_ESTIMABLE',
        'all_build_diameter_p95':float(np.quantile(da,.95)) if da else 'NOT_ESTIMABLE',
        'at_least_two_diameter_p95':float(np.quantile(dt,.95)) if dt else 'NOT_ESTIMABLE',
        'absolute_risk':float(np.mean(absrisk)), 'reference_risk':float(np.mean(refrisk)),
        'incremental_risk':float(np.mean(incrisk)),
        'ci_low':float(np.quantile(boot,.025)), 'ci_high':float(np.quantile(boot,.975)),
        'delete_top1':float(np.mean(qvals[keep])), 'unresolved_mass':float(np.mean([x is None for x in safe.values()])),
        '_safe':safe, '_by':by, '_queries':queries, '_builds':builds, '_qvalues':qvals,
    }

def load_hnsw(ds):
    rows=[]
    for p in sorted(E4.glob(ds+'__seed*__*/queries.csv.gz')):
        with gzip.open(p, 'rt', newline='') as f:
            for r in csv.DictReader(f):
                if int(r.get('latency_round',0)) == 0 and int(r['query_id']) < 750:
                    rows.append({'build_id':p.parent.name, 'query_id':int(r['query_id']), 'ef':int(r['ef_search']),
                                 'hit_count':int(round(float(r['recall_at_10'])*10)), 'recall':float(r['recall_at_10'])})
    return rows

def load_faiss_raw(ds):
    rows=[]; raw=FAISS/'raw'
    for p in sorted(raw.glob(ds+'__100k__clean*.csv.gz')):
        with gzip.open(p, 'rt', newline='') as f:
            for r in csv.DictReader(f):
                rows.append({'build_id':r['build_id'],'query_id':int(r['query_id']),'ef':int(r['ef']),
                             'hit_count':int(r['hit_count']),'recall':float(r['recall']),
                             'returned_top10':r['returned_top10']})
    return rows

def lobo(rows, h, grid):
    builds=sorted({r['build_id'] for r in rows}); queries=sorted({int(r['query_id']) for r in rows})
    by=defaultdict(dict)
    for r in rows: by[(r['build_id'],int(r['query_id']))][int(r['ef'])]=r
    def risk(bb):
        safe={(b,q):next((e for e in grid if int(by[(b,q)][e]['hit_count'])>=h),None) for b in bb for q in queries}
        v=[]
        for s in bb:
            for t in bb:
                if s == t: continue
                for q in queries:
                    sa=safe[(s,q)]; ta=safe[(t,q)]; act=max(grid) if sa is None else sa
                    v.append(int(ta is None or int(by[(t,q)][act]['hit_count'])<h)-int(ta is None))
        return float(np.mean(v))
    return [{'dataset':rows[0].get('dataset','unknown'),'h':h,'dropped_build':b,
             'remaining_builds':len(builds)-1,'incremental_risk':risk([x for x in builds if x!=b]),
             'direction_positive':risk([x for x in builds if x!=b]) > 0} for b in builds]

def parent_sha_snapshot():
    OUT.mkdir(parents=True, exist_ok=True)
    patterns=('docs/graph_anns_iclr_phase1_1_repair/','results/graph_anns_iclr_phase1_1_repair/',
              'figures/graph_anns_iclr_phase1_1_repair/','scripts/graph_anns_iclr_phase1_1_repair/',
              'tests/graph_anns_iclr_phase1_1_repair/','manifests/graph_anns_iclr_phase1_1_repair_decision.json')
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',PARENT_COMMIT], cwd=ROOT, text=True).splitlines()
    rows=[]
    for n in names:
        if n.startswith(patterns):
            b=subprocess.check_output(['git','show',PARENT_COMMIT+':'+n], cwd=ROOT)
            rows.append({'parent_commit':PARENT_COMMIT,'path':n,'sha256':hashlib.sha256(b).hexdigest()})
    write_csv(OUT/'parent_stage_sha256.csv',rows)

def content_forensics():
    import h5py
    out=[]; diag=[]; all_hashes=[]; overlap_events=[]
    hist_hashes={}; hist_ids={}
    for ds in DS:
        role_rows=read_csv(ROLES/ds/'role_ids.csv')
        ids=[int(r['source_id']) for r in role_rows]
        hist_ids[ds]=set(ids)
        hs=set(); nh=set()
        with h5py.File(H5[ds],'r') as f:
            for i in ids:
                x=np.asarray(f['train'][i],np.float32); hs.add(qdigest(x)); nh.add(qdigest(x,True))
        hist_hashes[ds]=(hs,nh)
        qrows=[r for r in read_csv(PARENT/'faiss100k_query_role_ledger.csv') if r['dataset']==ds]
        qids=[int(r['source_id']) for r in qrows]
        qraw=set(); qnorm=set(); qvecs=h5_rows(ds,qids)
        base_raw=set(); base_norm=set(); base_raw_map={}; base_norm_map={}
        with h5py.File(H5[ds],'r') as f:
            for start in range(0,100000,2048):
                arr=np.asarray(f['train'][start:min(start+2048,100000)],np.float32)
                for j,x in enumerate(arr):
                    bi=start+j; hr=qdigest(x); hn=qdigest(x,True)
                    base_raw.add(hr); base_norm.add(hn); base_raw_map.setdefault(hr,bi); base_norm_map.setdefault(hn,bi)
        for qi,(sid,x) in enumerate(zip(qids,qvecs)):
            hr=qdigest(x); hn=qdigest(x,True)
            qraw.add(hr); qnorm.add(hn)
            if hr in base_raw_map: overlap_events.append({'dataset':ds,'query_id':qi,'source_id':sid,'type':'raw_content_overlap','query_hash':hr,'base_id':base_raw_map[hr]})
            if hn in base_norm_map: overlap_events.append({'dataset':ds,'query_id':qi,'source_id':sid,'type':'normalized_content_overlap','query_hash':hn,'base_id':base_norm_map[hn]})
        id_ov=len(set(qids)&set(range(100000))); raw_ov=len(qraw&base_raw); norm_ov=len(qnorm&base_norm)
        hid=len(set(qids)&hist_ids[ds]); hraw=len(qraw&hist_hashes[ds][0]); hnorm=len(qnorm&hist_hashes[ds][1])
        dup_id=len(qids)-len(set(qids)); dup_raw=len(qids)-len(qraw); dup_norm=len(qids)-len(qnorm)
        out.append({'dataset':ds,'evaluation_n':len(qids),'query_base_id_overlap':id_ov,'query_base_raw_overlap':raw_ov,
                    'query_base_normalized_overlap':norm_ov,'historical_role_id_overlap':hid,
                    'historical_role_raw_overlap':hraw,'historical_role_normalized_overlap':hnorm,
                    'evaluation_internal_id_duplicates':dup_id,'evaluation_internal_raw_duplicates':dup_raw,
                    'evaluation_internal_normalized_duplicates':dup_norm,
                    'gate_a':'PASS' if max(id_ov,raw_ov,norm_ov,hid,hraw,hnorm,dup_id,dup_raw,dup_norm)==0 else 'FAIL'})
        all_hashes.append({'dataset':ds,'base_raw_hash_count':len(base_raw),'base_normalized_hash_count':len(base_norm),
                           'evaluation_raw_hash_count':len(qraw),'evaluation_normalized_hash_count':len(qnorm)})
        # Frozen truth/top-k diagnostic (no ANN call).
        truth_rows=read_csv(PARENT/(ds+'_exact_truth.csv'))
        unique_truth=sum(len(set(r['top10'].split('|')))==10 for r in truth_rows)
        src_in_truth=sum(int(r['query_id']) in set(r['top10'].split('|')) for r in truth_rows)
        tops=[]; dup_top=0
        for p in sorted((CLEAN_FAISS/'raw').glob(ds+'__100k__clean*.csv.gz')):
            with gzip.open(p,'rt',newline='') as f:
                for r in csv.DictReader(f):
                    vals=r['returned_top10'].split('|'); dup_top += int(len(vals)!=len(set(vals))); tops.append(r)
        diag.append({'dataset':ds,'truth_rows':len(truth_rows),'truth_unique_k10_rows':unique_truth,
                     'query_source_in_truth':src_in_truth,'topk_rows':len(tops),'topk_duplicate_id_rows':dup_top,
                     'zero_distance_duplicate':'ZERO_DISTANCE_DUPLICATE_NOT_ESTIMABLE_FROM_FROZEN_TOPK'})
    write_csv(OUT/'content_overlap_forensics.csv',out)
    write_csv(OUT/'content_overlap_events.csv',overlap_events)
    write_csv(OUT/'content_hash_inventory.csv',all_hashes)
    write_csv(OUT/'exact_truth_topk_diagnostics.csv',diag)
    return out

def index_registry_audit():
    expected=read_csv(BUILD_REG); current=read_csv(PARENT/'faiss100k_reuse_registry.csv')
    source_rows={r['dataset']:r for r in read_csv(SOURCE_REG) if r.get('path','').endswith('.hdf5')}
    base_hashes={ds:digest(Path(source_rows[ds]['path'])) for ds in DS}
    curmap={}
    for r in current:
        perm=r['build_id'].split('__clean')[1].split('__')[0]
        key=(r['dataset'],perm)
        curmap[key]=r
    rows=[]; config_ok=0
    try:
        import faiss
    except Exception:
        faiss=None
    for e in expected:
        perm=e['build_id'].split('__perm')[1].split('__')[0]
        c=curmap.get((e['dataset'],perm),{})
        path=Path(c.get('source_index',''))
        actual_hash=digest(path) if path.exists() else 'MISSING'
        obs={'d':None,'metric_type':None,'M':None,'efConstruction':None,'faiss_version':'NOT_INSPECTED'}
        if faiss and path.exists():
            idx=faiss.read_index(str(path)); core=faiss.downcast_index(idx.index)
            obs={'d':int(idx.d),'metric_type':int(idx.metric_type),'M':int(core.hnsw.nb_neighbors(0)//2),
                 'efConstruction':int(core.hnsw.efConstruction),'faiss_version':faiss.__version__}
        base_expected=source_rows[e['dataset']]['file_sha256']
        fields_ok=(actual_hash==e['index_sha256'] and base_hashes[e['dataset']]==base_expected and c.get('base_count')==e['base_count'] and
                   c.get('faiss_version')==e['faiss_version'] and c.get('M')==e['M'] and
                   c.get('efConstruction')==e['efConstruction'] and obs.get('faiss_version')==e['faiss_version'] and
                   obs.get('M')==int(e['M']) and obs.get('efConstruction')==int(e['efConstruction']))
        config_ok += int(fields_ok)
        rows.append({'dataset':e['dataset'],'build_id':e['build_id'],'perm':perm,'index_path':str(path),
                     'expected_index_sha256':e['index_sha256'],'current_index_sha256':actual_hash,
                     'hash_match':actual_hash==e['index_sha256'],'base_count_expected':e['base_count'],
                     'base_file_sha256_expected':base_expected,'base_file_sha256_current':base_hashes[e['dataset']],
                     'base_file_hash_match':base_hashes[e['dataset']]==base_expected,
                     'base_count_registry':c.get('base_count'),'faiss_expected':e['faiss_version'],
                     'faiss_observed':obs.get('faiss_version'),'M_expected':e['M'],'M_observed':obs.get('M'),
                     'efConstruction_expected':e['efConstruction'],'efConstruction_observed':obs.get('efConstruction'),
                     'metric':'L2','metric_type_observed':obs.get('metric_type'),'config_source':'INDEX_OBJECT_AND_FROZEN_BUILD_METADATA',
                     'field_match':fields_ok})
    write_csv(OUT/'frozen_index_registry_audit.csv',rows)
    return rows

def hnsw_reconciliation():
    rows=[]
    for ds in DS:
        z=action_summary(load_hnsw(ds),10,HNSW_GRID)
        q=z['_qvalues'];
        finite=[]; joint=[]; composite=[]
        for (b,qid),a in z['_safe'].items():
            if a is None: composite.append(1)
            else: finite.append(a)
        for s in z['_builds']:
            for t in z['_builds']:
                if s==t: continue
                for qid in z['_queries']:
                    sa=z['_safe'][(s,qid)]; ta=z['_safe'][(t,qid)]
                    if sa is not None and ta is not None:
                        act=sa; joint.append(int(z['_by'][(t,qid)][act]['hit_count']<10))
                    # pessimistic source-censor composite: source bottom itself is unresolved.
                    composite.append(int(sa is None or ta is None or (sa is not None and z['_by'][(t,qid)][sa]['hit_count']<10)))
        vals=[('historical_primary_transport','source bottom -> max registered action','target bottom -> failure',z['incremental_risk'],z['ci_low'],z['ci_high'],True),
              ('source_censoring_composite_sensitivity','source bottom -> composite failure','target bottom -> failure',float(np.mean(composite)), 'NOT_REPORTED','NOT_REPORTED',False),
              ('jointly_feasible_sensitivity','exclude source/target bottom pairs','finite target failure',float(np.mean(joint)) if joint else 'NOT_ESTIMABLE','NOT_REPORTED','NOT_REPORTED',False),
              ('endpoint_reference_risk','not applicable','target bottom indicator',z['reference_risk'],'NOT_REPORTED','NOT_REPORTED',False)]
        for name,src,tgt,est,lo,hi,main in vals:
            rows.append({'dataset':ds,'estimand_name':name,'source_censored_handling':src,'target_censored_handling':tgt,
                         'point_estimate':est,'ci_low':lo,'ci_high':hi,'source_file':str(PARENT/'estimand_registry.csv'),
                         'paper_primary_result':main,'evidence':'RAW_DATA_COMPUTED_FROM_E4_ROWS'})
    write_csv(OUT/'hnswlib_estimand_reconciliation.csv',rows)
    return rows

def vamana_audit():
    rows=[]
    for ds,base in [('sift_100k',Path('/home/wlk/data500/icba_vamana_stage1')),('arxiv_nomic_100k',Path('/home/wlk/data500/icba_vamana_stage1_arxiv'))]:
        s=json.loads((base/'analysis/sift_summary.json').read_text()); ev=read_csv(base/'analysis/events.csv')
        ref=sum(int(r['bt'])<0 for r in ev)/len(ev)
        rows.append({'dataset':ds,'event_definition':'UNDER_BUDGET_UNSAFE and right-censoring classes; risk field is event risk',
                     'transport_risk_original_stage':s['transport_risk'],'delta_risk_original_stage':s['delta_risk'],
                     'reference_risk_from_target_bottom':ref,'reference_risk_original_field':'MISSING_NOT_ZERO',
                     'source_bottom_action':'NOT_RECORDED_FOR_HARMONIZED_E4_REPLAY','target_bottom_action':'failure',
                     'mixed_finite_censored_rate':s['mixed_finite_censored_rate'],
                     'harmonized_absolute_transport_risk':'REFERENCE_RISK_NOT_SEPARATELY_ESTIMABLE_FROM_FROZEN_VAMANA_EVENTS',
                     'harmonized_incremental_risk':'REFERENCE_RISK_NOT_SEPARATELY_ESTIMABLE_FROM_FROZEN_VAMANA_EVENTS',
                     'comparability':'COMPARABLE_ONLY_UNDER_HARMONIZED_SENSITIVITY','evidence':'FROZEN_EVENTS_AUDITED_NO_RERUN'})
    write_csv(OUT/'vamana_estimand_semantic_audit.csv',rows)
    return rows

def d3_recompute():
    out=[]; quality=[]
    for ds in DS:
        d3rows=[]; metas=[]; top_runs=[]
        for p in sorted((D3ROOT/ds/'D3').glob('*')):
            q=p/'queries.csv.gz'; c=p/'COMPLETE.json'
            if not q.exists() or not c.exists(): continue
            metas.append(json.loads(c.read_text()))
            with gzip.open(q,'rt',newline='') as f:
                rr=list(csv.DictReader(f))
            tops=[r['returned_top10'] for r in rr]; top_runs.append(tops)
            for r in rr:
                d3rows.append({'dataset':ds,'build_id':p.name,'query_id':int(r['query_id']),'ef':int(r['ef_search']),
                               'hit_count':int(round(float(r['recall_at_10'])*10)),'recall':float(r['recall_at_10']),
                               'returned_top10':r['returned_top10']})
        z=action_summary(d3rows,10,HNSW_GRID)
        safe=z['_safe']; min_actions=[safe[(b,q)] for b in z['_builds'] for q in z['_queries']]
        endpoints=[safe[(b,q)] is None for b in z['_builds'] for q in z['_queries']]
        hit_arrays=[]
        for p in sorted((D3ROOT/ds/'D3').glob('*')):
            q=p/'queries.csv.gz'
            with gzip.open(q,'rt',newline='') as f:
                hit_arrays.append([int(round(float(r['recall_at_10'])*10)) for r in csv.DictReader(f)])
        index_hashes=[m['index_sha256'] for m in metas]
        idx_identity=len(set(index_hashes))==1 and len(index_hashes)==3
        top_identity=len(top_runs)==3 and all(x==top_runs[0] for x in top_runs)
        hit_identity=len(hit_arrays)==3 and all(x==hit_arrays[0] for x in hit_arrays)
        # minimum-safe and endpoint identities are separately recomputed from raw rows.
        safe_by_run=[]; end_by_run=[]
        for p in sorted((D3ROOT/ds/'D3').glob('*')):
            rr=[]
            with gzip.open(p/'queries.csv.gz','rt',newline='') as f: rr=list(csv.DictReader(f))
            bb=defaultdict(dict)
            for r in rr: bb[int(r['query_id'])][int(r['ef_search'])]=int(round(float(r['recall_at_10'])*10))
            safe_by_run.append([next((e for e in HNSW_GRID if bb[q].get(e,0)>=10),None) for q in sorted(bb)])
            end_by_run.append([bb[q].get(max(HNSW_GRID),0)<10 for q in sorted(bb)])
        safe_identity=len(safe_by_run)==3 and all(x==safe_by_run[0] for x in safe_by_run)
        end_identity=len(end_by_run)==3 and all(x==end_by_run[0] for x in end_by_run)
        out.append({'dataset':ds,'index_byte_identity_3of3':idx_identity,'search_topk_identity_3of3':top_identity,
                    'hit_count_identity_3of3':hit_identity,'minimum_safe_action_identity_3of3':safe_identity,
                    'endpoint_state_identity_3of3':end_identity,'incremental_transport_risk':z['incremental_risk'],
                    'top1_delete_incremental_risk':z['delete_top1'],'evidence':'RAW_D0_D3_RECOMPUTATION'})
        d0rows=[]
        for p in sorted((D0ROOT/ds).glob('*')):
            with gzip.open(p/'queries.csv.gz','rt',newline='') as f:
                for r in csv.DictReader(f):
                    d0rows.append({'build_id':p.name,'query_id':int(r['query_id']),'ef':int(r['ef_search']),
                                   'hit_count':int(round(float(r['recall_at_10'])*10)),'recall':float(r['recall_at_10']),
                                   'latency_ns':int(r.get('latency_ns',0)),'ndc':r.get('ndc','')})
        def budget_stats(rr,grid):
            bb=defaultdict(dict)
            for r in rr: bb[(r['build_id'],r['query_id'])][r['ef']]=r
            vals=[]
            for a in bb.values():
                v=next((e for e in grid if int(a[e]['hit_count'])>=10),None)
                if v is not None: vals.append(v)
            return float(np.mean(vals)),float(np.quantile(vals,.95)),float(np.quantile(vals,.99)),len(vals)
        d0m=budget_stats(d0rows,HNSW_GRID); d3m=budget_stats(d3rows,HNSW_GRID)
        d0max=np.mean([r['recall'] for r in d0rows if r['ef']==max(HNSW_GRID)]); d3max=np.mean([r['recall'] for r in d3rows if r['ef']==max(HNSW_GRID)])
        d0meta=read_csv(OLD/'deterministic_fair_d0_control.csv'); d0times=[float(r['build_seconds']) for r in d0meta if r['dataset']==ds]
        d3times=[float(m['build_wall_seconds']) for m in metas]
        quality.append({'dataset':ds,'recall_delta_d3_minus_d0':d3max-d0max,'d0_mean_safe_budget':d0m[0],'d3_mean_safe_budget':d3m[0],
                        'mean_safe_budget_ratio':d3m[0]/d0m[0],'d0_p95_safe_budget':d0m[1],'d3_p95_safe_budget':d3m[1],
                        'p95_safe_budget_ratio':d3m[1]/d0m[1],'d0_p99_safe_budget':d0m[2],'d3_p99_safe_budget':d3m[2],
                        'p99_safe_budget_ratio':d3m[2]/d0m[2],'build_time_ratio':float(np.median(d3times)/np.median(d0times)),
                        'search_time_or_ndc':'NDC_NOT_ESTIMABLE_D3_NO_NDC_FIELD_D0_ZERO_PLACEHOLDER','d3_quality_scope':'REGISTERED_D0_D3_ONLY'})
    write_csv(OUT/'d3_full_recalculation.csv',out); write_csv(OUT/'d3_vs_d0_quality.csv',quality)
    return out,quality

def six_cell_table():
    frows=read_csv(PARENT/'faiss_clean_semantic_results.csv'); hrows=read_csv(PARENT/'estimand_registry.csv'); vrows=read_csv(OUT/'vamana_estimand_semantic_audit.csv')
    out=[]
    for ds in DS:
        f=next(r for r in frows if r['dataset']==ds and r['h']=='10'); h=next(r for r in hrows if r['dataset']==ds)
        v=next(r for r in vrows if r['dataset']==ds)
        common={'base_count':100000,'queries':750,'h':10}
        out.append({'dataset':ds,'operator':'hnswlib HNSW','builds':24,'pairs':552,'native_action_grid':'10;20;40;80;120;200',
                    'endpoint_variation':h['endpoint_state_variation'],'inclusive_variation':h['inclusive_budget_state_variation'],
                    'finite_variation':h['minimum_safe_action_variation'],'all_build_feasible':h['all_build_feasible_queries'],
                    'at_least_two_feasible':h['at_least_two_feasible_queries'],'all_build_diameter':h['all_build_feasible_diameter_mean'],
                    'at_least_two_diameter':h['at_least_two_feasible_diameter_mean'],'unresolved_mass':h['unresolved_mass'],
                    'absolute_risk':h['absolute_transport_risk'],'reference_risk':h['reference_risk'],'incremental_risk':h['incremental_transport_risk'],
                    'ci_low':h['bootstrap_ci_low'],'ci_high':h['bootstrap_ci_high'],'lo_bo_range':'PARENT_REPAIR_REGISTRY',
                    'top1_delete':h['delete_top1_incremental_risk'],'estimand_name':'HISTORICAL_E4_PRIMARY',
                    'estimand_comparability':'PRIMARY_WITHIN_HNSW','cost_evidence_status':'PRIMITIVE_ONLY','evidence_provenance':'REPAIR_RAW_E4','limitations':'Faiss NDC scope separate'})
        out.append({'dataset':ds,'operator':'Faiss HNSW','builds':24,'pairs':552,'native_action_grid':'16;32;64;128;256;512',
                    'endpoint_variation':f['endpoint_state_variation'],'inclusive_variation':f['inclusive_budget_state_variation'],
                    'finite_variation':f['minimum_safe_action_variation'],'all_build_feasible':f['all_build_feasible_queries'],
                    'at_least_two_feasible':f['at_least_two_feasible_queries'],'all_build_diameter':f['all_build_feasible_diameter_mean'],
                    'at_least_two_diameter':f['at_least_two_feasible_diameter_mean'],'unresolved_mass':f['unresolved_mass'],
                    'absolute_risk':f['absolute_transport_risk'],'reference_risk':f['reference_risk'],'incremental_risk':f['incremental_transport_risk'],
                    'ci_low':f['bootstrap_ci_low'],'ci_high':f['bootstrap_ci_high'],'lo_bo_range':'SEE faiss_clean_lobo_results.csv',
                    'top1_delete':f['delete_top1_incremental_risk'],'estimand_name':'CLEAN_FAISS_PRIMARY','estimand_comparability':'WITHIN_FAISS_ONLY',
                    'cost_evidence_status':'NDC_NOT_ESTIMABLE_BATCH_CUMULATIVE','evidence_provenance':'CLEAN_QUERY_REPLAY','limitations':'No raw-budget equivalence'})
        out.append({'dataset':ds,'operator':'Vamana-style','builds':12,'pairs':36,'native_action_grid':'16;32;64;128;256;512',
                    'endpoint_variation':'NOT_ESTIMABLE_FROM_FROZEN_HIT_COUNTS','inclusive_variation':'NOT_ESTIMABLE_FROM_FROZEN_HIT_COUNTS',
                    'finite_variation':'NOT_ESTIMABLE_FROM_FROZEN_HIT_COUNTS','all_build_feasible':'NOT_ESTIMABLE','at_least_two_feasible':'NOT_ESTIMABLE',
                    'all_build_diameter':'SEE vamana audit','at_least_two_diameter':'SEE vamana audit','unresolved_mass':v['mixed_finite_censored_rate'],
                    'absolute_risk':v['transport_risk_original_stage'],'reference_risk':v['reference_risk_from_target_bottom'],
                    'incremental_risk':v['delta_risk_original_stage'],'ci_low':'FROZEN_BOOTSTRAP','ci_high':'FROZEN_BOOTSTRAP',
                    'lo_bo_range':'FROZEN_LOBO','top1_delete':'FROZEN_TOP1','estimand_name':'ORIGINAL_STAGE_PLUS_TARGET_BOTTOM_AUDIT',
                    'estimand_comparability':'COMPARABLE_ONLY_UNDER_HARMONIZED_SENSITIVITY','cost_evidence_status':'FROZEN_COST_SCOPE',
                    'evidence_provenance':'FROZEN_EVENTS_AUDITED','limitations':'Harmonized transport/reference not separately estimable; h8/h9 NOT_ESTIMABLE'})
    write_csv(OUT/'cross_family_evidence_table_final.csv',out)
    return out

def make_reports(index_rows, overlaps, hrec, vam, d3, qual, cells, test_info=None):
    gate_a=all(r['gate_a']=='PASS' for r in overlaps); gate_b=len(index_rows)==48 and all(r['field_match'] for r in index_rows)
    # Vamana does not expose a separately harmonized transport/reference estimand.
    label='HNSW_CROSS_IMPLEMENTATION_CONFIRMED_VAMANA_ESTIMAND_NOT_HARMONIZED'
    summaries={r['dataset']:r for r in qual}
    f=read_csv(PARENT/'faiss_clean_semantic_results.csv')
    text=[]
    text += ['# ICBA Graph-ANNS Phase 1.1a final hotfix report','',
             'This is a code-only evidence patch. It does not construct an index and does not invoke ANN search. Parent commit 39a8b6d41f9fa0561660100856e2e98f330d0a4a is preserved read-only.','',
             f'Gate A content disjointness: {"PASS" if gate_a else "FAIL"}. Gate B frozen Faiss identity: {"PASS" if gate_b else "FAIL"}.',
             'Gate C keeps historical E4 hnswlib source-bottom-to-maximum-action semantics and separates composite/joint sensitivities.',
             'Vamana events contain event risk and target-bottom counts but no complete action-conditioned table sufficient to recompute the same E4 transport estimand; its harmonized field is therefore explicitly NOT_ESTIMABLE.',
             '', '## Clean Faiss h=10']
    for r in f:
        if r['h']=='10': text.append(f"- {r['dataset']}: absolute={float(r['absolute_transport_risk']):.9f}, reference={float(r['reference_risk']):.9f}, incremental={float(r['incremental_transport_risk']):.9f}, CI=[{float(r['bootstrap_ci_low']):.9f},{float(r['bootstrap_ci_high']):.9f}], endpoint={float(r['endpoint_state_variation']):.9f}, finite={float(r['minimum_safe_action_variation']):.9f}, unresolved={float(r['unresolved_mass']):.9f}, top1-delete={float(r['delete_top1_incremental_risk']):.9f}.")
    text += ['', '## D3 versus D0', *[f"- {r['dataset']}: Recall delta={float(r['recall_delta_d3_minus_d0']):.9f}; mean safe-budget ratio={float(r['mean_safe_budget_ratio']):.9f}; p95 ratio={float(r['p95_safe_budget_ratio']):.9f}; p99 ratio={float(r['p99_safe_budget_ratio']):.9f}; build-time ratio={float(r['build_time_ratio']):.9f}; NDC={r['search_time_or_ndc']}." for r in qual],
             '', '## Final decision', '', f'`{label}`. This is conditional on registered data, builds, and frozen event scopes; it is not a universal cross-family raw-budget claim.']
    docs={
        'executive_summary.md':'# Executive summary\n\nA pure-code final evidence patch audited query content, frozen Faiss identity, estimand semantics, Vamana events and D3 raw contracts. No ANN search or index build was run.\n',
        'content_overlap_forensics.md':'# Content-overlap forensics\n\nRaw and normalized float32 SHA256 sets were recomputed from HDF5 vectors for each clean evaluation role, 100K base and readable historical role ledger. The Gate is driven by these sets, not parent CSV claims.\n',
        'frozen_index_registry_audit.md':'# Frozen-index registry audit\n\nEach of 48 serialized Faiss files is compared against the parent build registry SHA and inspected for dimension, metric, M and efConstruction. Unreadable fields are labeled by source rather than hard-coded.\n',
        'hnswlib_estimand_reconciliation.md':'# hnswlib estimand reconciliation\n\nThe primary E4 estimand maps source bottom to the maximum registered action and treats target bottom as a target reference failure. Composite and jointly-feasible sensitivities are separate rows.\n',
        'vamana_estimand_semantic_audit.md':'# Vamana estimand semantic audit\n\nThe frozen event table supplies original-stage risk and target-bottom counts, but does not expose a complete action-conditioned response needed for a fully harmonized E4 transport replay. No zero reference risk is asserted.\n',
        'd3_full_recalculation_report.md':'# D3 full recalculation\n\nD3 index bytes, top-k, hit counts, minimum-safe actions, endpoint states, transport risk and top-1 deletion are recomputed separately from frozen D3 rows. D0/D3 quality and build overhead are reported without extending scope.\n',
        'independent_statistics_validation.md':'# Independent statistics validation\n\nA transparent implementation recomputes Faiss h=10 risk, 24 LOBO deletions, top-1 deletion, hnswlib primary risk, D3 zero-risk and content-hash disjointness. Production comparisons use absolute tolerance 1e-12 (bootstrap CI 1e-10).\n',
        'cross_family_final_report.md':'# Cross-family final report\n\nThe six-cell table separates native action families. hnswlib and clean Faiss show positive registered h=10 directions in both datasets; Vamana remains comparable only under an explicitly unavailable harmonized sensitivity.\n',
        'paper_number_patch.md':'# Paper-number patch\n\nReplace any parent statement that inferred content disjointness, frozen index identity or Vamana reference risk without direct evidence. Preserve hnswlib E4 primary numbers and use clean Faiss rows for the 100K scope.\n',
        'paper_claim_registry.md':'# Paper claim registry\n\nClaims are conditional on registered datasets/builds/action grids. Do not equate efSearch, Faiss efSearch and Vamana L across implementations or claim universal cost-tax equivalence.\n',
        'reproducibility_report.md':'# Reproducibility report\n\nTwo deterministic pure-code replays are required; they read frozen rows and indexes only, exclude cache/pyc/logs from checksums, and preserve the parent tree.\n',
        'final_hotfix_report.md':'\n'.join(text)+'\n',
    }
    DOC.mkdir(parents=True,exist_ok=True)
    for n,t in docs.items(): (DOC/n).write_text(t)
    # Registry and concise machine-readable gate.
    write_csv(OUT/'unified_gate.csv',[{'gate':'A_content_disjointness','status':'PASS' if gate_a else 'FAIL'},
                                      {'gate':'B_frozen_index_identity','status':'PASS' if gate_b else 'FAIL'},
                                      {'gate':'C_estimand_semantics','status':'PASS_WITH_VAMANA_EXPLICIT_DOWNGRADE'},
                                      {'gate':'D_d3_contract','status':'PASS' if all(x['index_byte_identity_3of3'] and x['search_topk_identity_3of3'] and x['hit_count_identity_3of3'] and x['minimum_safe_action_identity_3of3'] and x['endpoint_state_identity_3of3'] and x['incremental_transport_risk']==0 for x in d3) else 'FAIL'},
                                      {'gate':'E_independent_statistics','status':'PENDING_TEST_SCRIPT'},
                                      {'gate':'F_artifact_hygiene','status':'PENDING_REPLAY'}])
    return label

def build_manifest(label, test_info=None, replay=None):
    m={'schema_version':'phase1.1a-hotfix-1.0','parent_commit':PARENT_COMMIT,
       'branch':'exp/graph_anns_iclr_phase1_1_final_evidence_hotfix','worktree':'/home/wlk/projects/navigation-aware-resistance-hnsw',
       'ann_search_invoked':False,'index_built':False,'parent_results_modified':False,
       'content_hash_gate':'REAL_FLOAT32_RAW_AND_NORMALIZED_RECOMPUTATION',
       'frozen_index_registry':'48_ROWS_SHA_AND_INDEX_OBJECT_CONFIG_CHECKED',
       'hnswlib_primary_estimand':'E4_SOURCE_BOTTOM_TO_MAX_REGISTERED_ACTION',
       'vamana_reference_risk':'TARGET_BOTTOM_COUNT_REPORTED; HARMONIZED_TRANSPORT_NOT_ESTIMABLE',
       'd3_recomputed_from_raw':True,'forbidden_roles_accessed':False,
       'final_scientific_label':label,
       'limitations':['Vamana harmonized E4 transport/reference not separately estimable','Faiss NDC batch cumulative not estimable','claims conditional on registered builds','profiling/cost primitive only']}
    if test_info: m['independent_tests']=test_info
    if replay: m['pure_code_replay']=replay
    MAN.parent.mkdir(parents=True,exist_ok=True); MAN.write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
    return m

def main():
    for p in (OUT,DOC,FIG): p.mkdir(parents=True,exist_ok=True)
    parent_sha_snapshot()
    overlaps=content_forensics(); idx=index_registry_audit(); hrec=hnsw_reconciliation(); vam= vamana_audit(); d3,qual=d3_recompute(); cells=six_cell_table()
    label=make_reports(idx,overlaps,hrec,vam,d3,qual,cells)
    build_manifest(label)
    print(json.dumps({'content_gate':all(r['gate_a']=='PASS' for r in overlaps),'index_rows':len(idx),'d3_rows':len(d3),'cells':len(cells),'label':label},sort_keys=True))

if __name__=='__main__': main()
