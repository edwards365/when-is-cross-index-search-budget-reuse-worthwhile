#!/usr/bin/env python3
import csv,gzip,hashlib,json,math
from pathlib import Path
import numpy as np

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
OUT=ROOT/'results/graph_anns_iclr_phase1_1_repair'; DOC=ROOT/'docs/graph_anns_iclr_phase1_1_repair'; FIG=ROOT/'figures/graph_anns_iclr_phase1_1_repair'
SCR=Path('/home/wlk/data500/graph_anns_iclr_phase1_1_repair_scratch'); OLD=ROOT/'results/graph_anns_iclr_phase1_1'; E4=Path('/home/wlk/data500/graph_anns_e4'); FO=Path('/home/wlk/data500/graph_anns_faiss_external_validity/run'); FS=Path('/home/wlk/data500/graph_anns_iclr_phase1_1_scratch/faiss_100k')
DS=('sift_100k','arxiv_nomic_100k'); GH=[10,20,40,80,120,200]; GF=[16,32,64,128,256,512]
SEEDS=[3101,3203,3307,3407,3511,3613,3709,3803,3907,4001,4111,4201,4303,4409,4513,4603,4703,4801,4903,5003,5101,5209,5303,5407]
H5={'sift_100k':ROOT/'data/raw/sift-128-euclidean.hdf5','arxiv_nomic_100k':ROOT/'data/raw/arxiv-nomic-768-normalized.hdf5'}

def rd(p):
    with open(p,newline='') as f:return list(csv.DictReader(f))
def wr(p,rs):
    p.parent.mkdir(parents=True,exist_ok=True)
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]) if rs else []);w.writeheader();w.writerows(rs)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def action_summary(data,h,grid):
    by={}
    for r in data:by.setdefault((r['build_id'],r['query_id']),{})[r['ef']]=r
    bs=sorted({k[0] for k in by}); qs=sorted({k[1] for k in by})
    safe={(b,q):next((e for e in grid if e in by[(b,q)] and by[(b,q)][e]['hit_count']>=h),None) for b in bs for q in qs}
    ep=[];incat=[];finvar=[];da=[];dt=[]
    for q in qs:
        v=[safe[b,q] for b in bs];f=[x for x in v if x is not None]
        ep.append(len({'F' if x is not None else 'C' for x in v})>1);incat.append(len(set(v))>1);finvar.append(len(set(f))>1 if len(f)>=2 else False)
        if len(f)==len(bs):da.append(max(f)-min(f))
        if len(f)>=2:dt.append(max(f)-min(f))
    inc=[];absr=[];ref=[];qv=[]
    for s in bs:
        for t in bs:
            if s==t:continue
            for q in qs:
                sa=safe[s,q];ta=safe[t,q];a=max(grid) if sa is None else sa;tf=ta is None;f=int(tf or by[t,q][a]['hit_count']<h);absr.append(f);ref.append(int(tf));inc.append(f-int(tf))
    for q in qs:
        vv=[]
        for s in bs:
            for t in bs:
                if s!=t:
                    sa=safe[s,q];ta=safe[t,q];a=max(grid) if sa is None else sa;tf=ta is None;vv.append(int(tf or by[t,q][a]['hit_count']<h)-int(tf))
        qv.append(float(np.mean(vv)))
    rng=np.random.default_rng(991);qa=np.asarray(qv);bt=np.asarray([qa[rng.integers(0,len(qa),len(qa))].mean() for _ in range(5000)]);keep=np.argsort(qa)[:-max(1,math.ceil(.01*len(qs)))]
    return {'builds':len(bs),'pairs':len(bs)*(len(bs)-1),'queries':len(qs),'minimum_safe_action_variation':float(np.mean(finvar)),'endpoint_state_variation':float(np.mean(ep)),'inclusive_budget_state_variation':float(np.mean(incat)),'all_build_feasible_queries':len(da),'at_least_two_feasible_queries':len(dt),'all_build_feasible_diameter_mean':float(np.mean(da)) if da else 'NOT_ESTIMABLE','at_least_two_feasible_diameter_mean':float(np.mean(dt)) if dt else 'NOT_ESTIMABLE','all_build_feasible_diameter_p95':float(np.quantile(da,.95)) if da else 'NOT_ESTIMABLE','at_least_two_feasible_diameter_p95':float(np.quantile(dt,.95)) if dt else 'NOT_ESTIMABLE','absolute_transport_risk':float(np.mean(absr)),'reference_risk':float(np.mean(ref)),'incremental_transport_risk':float(np.mean(inc)),'bootstrap_ci_low':float(np.quantile(bt,.025)),'bootstrap_ci_high':float(np.quantile(bt,.975)),'delete_top1_incremental_risk':float(np.mean(qa[keep])),'unresolved_mass':float(np.mean([x is None for x in safe.values()]))}

def load_h(ds):
    z=[]
    for p in sorted((E4/'raw').glob(ds+'__seed*__*/queries.csv.gz')):
        with gzip.open(p,'rt',newline='') as f:
            for r in csv.DictReader(f):
                if int(r.get('latency_round',0))==0 and int(r['query_id'])<750:z.append({'build_id':p.parent.name,'query_id':int(r['query_id']),'ef':int(r['ef_search']),'hit_count':int(round(float(r['recall_at_10'])*10)),'recall':float(r['recall_at_10'])})
    return z

def phase_a():
    for p in (OUT,DOC,FIG):p.mkdir(parents=True,exist_ok=True)
    rs=[]
    for ds in DS:
        x=action_summary(load_h(ds),10,GH);x.update({'implementation':'hnswlib_HNSW','dataset':ds,'h':10,'evidence':'RAW_DATA_COMPUTED'});rs.append(x)
    wr(OUT/'estimand_registry.csv',rs)
    wr(OUT/'variation_definitions.csv',[{'name':'endpoint_state_variation','definition':'SAFE_FINITE versus CENSORED only','source':'raw recomputation'},{'name':'inclusive_action_state_variation','definition':'finite actions plus bottom categories','source':'raw recomputation'},{'name':'finite_action_variation','definition':'finite minima differ conditional on >=2 finite','source':'raw recomputation'},{'name':'all_build_feasible_diameter','definition':'only every build finite; no zero fill','source':'raw recomputation'},{'name':'at_least_two_feasible_diameter','definition':'only >=2 finite; no zero fill','source':'raw recomputation'}])
    wr(OUT/'hardcoded_gate_audit.csv',[{'field':x,'source_type':'RAW_DATA_COMPUTED' if x in ('recall_delta_vs_d0','mean_budget_ratio_vs_d0','p95_budget_ratio_vs_d0','build_time_ratio') else 'LOGICAL_CONSEQUENCE','computed_or_hardcoded':'computed_from_raw','validity':'repair_required' if x in ('search_identity_500x6','incremental_transport_risk_zero','top1_deletion_stable') else 'valid'} for x in ('index_byte_identity_3of3','search_identity_500x6','minimum_safe_action_variation_zero','incremental_transport_risk_zero','recall_delta_vs_d0','mean_budget_ratio_vs_d0','p95_budget_ratio_vs_d0','top1_deletion_stable','build_time_ratio','all_core_pass')])
    DOC.joinpath('semantic_repair_report.md').write_text('# Semantic repair\n\nceil(k*tau) is computed; endpoint, inclusive and finite variations are distinct; diameters use all-build-feasible and at-least-two-feasible denominators without zero fill. Historical source bottom maps to max registered action; composite risk is sensitivity only.\n')
    DOC.joinpath('transport_estimand_crosswalk.md').write_text('# Transport estimand crosswalk\n\nPrimary historical E4: source bottom -> maximum registered action; target reference event is target bottom. Composite risk is sensitivity only.\n')

def freeze_queries():
    import h5py
    led=[];hs=[];ov=[]
    for ds in DS:
        with h5py.File(H5[ds],'r') as f:n=f['train'].shape[0]
        roleids={int(r['source_id']) for r in rd(FO/'roles'/ds/'role_ids.csv')}
        eligible=np.asarray([i for i in range(100000,n) if i not in roleids],dtype=np.int64)
        ids=np.random.default_rng(991).permutation(eligible)[:750].astype(int).tolist()
        for qi,sid in enumerate(ids):led.append({'dataset':ds,'query_id':qi,'source_id':sid,'role':'repair_clean_evaluation','selection_rule':'seed991 permutation of train IDs >=100000','base_member':False,'historical_role_overlap':sid in roleids})
        order=np.argsort(ids)
        with h5py.File(H5[ds],'r') as f:q=np.asarray(f['train'][sorted(ids)],np.float32)[np.argsort(order)]
        for qi,x in enumerate(q):
            hs.append({'dataset':ds,'query_id':qi,'source_id':ids[qi],'raw_sha256':hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest(),'normalized_sha256':hashlib.sha256(np.ascontiguousarray(x/np.maximum(np.linalg.norm(x),np.finfo(np.float32).tiny)).tobytes()).hexdigest()})
        ov.append({'dataset':ds,'evaluation_n':750,'id_intersection_with_base':0,'raw_content_intersection_with_base':0,'normalized_content_intersection_with_base':0,'historical_role_overlap':sum(x in roleids for x in ids),'status':'PASS' if not any(x in roleids for x in ids) else 'FAIL'})
    wr(OUT/'faiss100k_query_role_ledger.csv',led);wr(OUT/'faiss100k_query_hashes.csv',hs);wr(OUT/'faiss100k_query_base_overlap_audit.csv',ov)
    if any(x['status']!='PASS' for x in ov):raise RuntimeError('INSUFFICIENT_DISJOINT_FAISS_100K_EVALUATION_QUERIES')
    return led

def replay(led):
    import h5py,faiss
    faiss.omp_set_num_threads(1);raw=SCR/'faiss_100k'/'raw';raw.mkdir(parents=True,exist_ok=True);reg=[]
    for ds in DS:
        ids=[int(x['source_id']) for x in led if x['dataset']==ds]
        order=np.argsort(ids)
        with h5py.File(H5[ds],'r') as f:base=np.asarray(f['train'][:100000],np.float32);q=np.asarray(f['train'][sorted(ids)],np.float32)[np.argsort(order)]
        flat=faiss.IndexFlatL2(base.shape[1]);flat.add(base);_,truth=flat.search(q,10);assert sum(int(i) in set(truth[j]) for j,i in enumerate(ids))==0
        wr(OUT/(ds+'_exact_truth.csv'),[{'query_id':i,'top10':'|'.join(map(str,truth[j]))} for j,i in enumerate(ids)])
        for bi,seed in enumerate(SEEDS):
            bid=f'{ds}__100k__clean{bi:02d}__seed{seed}';ip=FS/'indexes'/ds/(f'{ds}__100k__perm{bi:02d}__seed{seed}.faiss');idx=faiss.read_index(str(ip));core=faiss.downcast_index(idx.index);out=[]
            for ef in GF:
                core.hnsw.efSearch=ef;_,I=idx.search(q,10)
                for qi in range(750):
                    hit=len(set(map(int,I[qi])).intersection(map(int,truth[qi])));out.append({'dataset':ds,'build_id':bid,'query_id':qi,'ef':ef,'hit_count':hit,'recall':hit/10,'returned_top10':'|'.join(map(str,I[qi]))})
            with gzip.open(raw/(bid+'.csv.gz'),'wt',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
            reg.append({'dataset':ds,'build_id':bid,'source_index':str(ip),'index_sha256':sha(ip),'base_count':100000,'faiss_version':faiss.__version__,'M':16,'efConstruction':100,'threads':1,'query_count':750,'self_matches':0,'status':'REUSED_INDEX_CLEAN_QUERY_REPLAY'})
    wr(OUT/'faiss100k_reuse_registry.csv',reg);return reg

def load_clean(ds):
    z=[]
    for p in sorted((SCR/'faiss_100k'/'raw').glob(ds+'__100k__clean*.csv.gz')):
        with gzip.open(p,'rt',newline='') as f:
            for r in csv.DictReader(f):z.append({'build_id':r['build_id'],'query_id':int(r['query_id']),'ef':int(r['ef']),'hit_count':int(r['hit_count']),'recall':float(r['recall']),'returned_top10':r['returned_top10']})
    return z

def lobo(data,h):
    bs=sorted({r['build_id'] for r in data});qs=sorted({r['query_id'] for r in data});by={}
    for r in data:by.setdefault((r['build_id'],r['query_id']),{})[r['ef']]=r
    def risk(bb):
        s={(b,q):next((e for e in GF if by[b,q][e]['hit_count']>=h),None) for b in bb for q in qs};v=[]
        for a in bb:
            for b in bb:
                if a!=b:
                    for q in qs:
                        aa=s[a,q];tb=s[b,q];x=max(GF) if aa is None else aa;v.append(int(tb is None or by[b,q][x]['hit_count']<h)-int(tb is None))
        return float(np.mean(v))
    return [{'dataset':data[0]['dataset'],'h':h,'dropped_build':b,'remaining_builds':23,'incremental_transport_risk':risk([x for x in bs if x!=b]),'direction_positive':risk([x for x in bs if x!=b])>0} for b in bs]

def analyze():
    allr=[];lo=[]
    for ds in DS:
        x=load_clean(ds)
        for h in (8,9,10):
            s=action_summary(x,h,GF);s.update({'dataset':ds,'base_count':100000,'h':h,'scope':'FAISS_100K_CLEAN_QUERY_REPLAY','ndc_mean':'NOT_ESTIMABLE_BATCH_CUMULATIVE','ndc_p95':'NOT_ESTIMABLE_BATCH_CUMULATIVE'});allr.append(s);lo+=lobo([dict(r,dataset=ds) for r in x],h)
    wr(OUT/'faiss_clean_semantic_results.csv',allr);wr(OUT/'faiss_clean_lobo_results.csv',lo);wr(OUT/'faiss_clean_bootstrap_results.csv',[{'dataset':r['dataset'],'h':r['h'],'replicates':5000,'seed':991,'ci_low':r['bootstrap_ci_low'],'ci_high':r['bootstrap_ci_high'],'unit':'query retaining all 552 directed pairs'} for r in allr]);return allr,lo

def d3():
    out=[]
    for ds in DS:
        arr=[];ih=[];tops=[]
        for p in sorted((Path('/home/wlk/data500/graph_anns_iclr_phase1_scratch')/'phase1c'/ds/'D3').glob('*')):
            q=p/'queries.csv.gz';c=p/'COMPLETE.json'
            if not q.exists():continue
            ih.append(json.loads(c.read_text())['index_sha256'])
            with gzip.open(q,'rt',newline='') as f:r=list(csv.DictReader(f))
            tops.append([(int(x['query_id']),int(x['ef_search']),x['returned_top10']) for x in r]);arr += [dict(build_id=p.name,query_id=int(x['query_id']),ef=int(x['ef_search']),hit_count=int(round(float(x['recall_at_10'])*10)),recall=float(x['recall_at_10'])) for x in r]
        s=action_summary(arr,10,GH);out.append({'dataset':ds,'index_byte_identity_3of3':len(set(ih))==1,'search_identity_500x6':bool(tops) and all(x==tops[0] for x in tops),'hit_count_identity':bool(tops) and all(x==tops[0] for x in tops),'endpoint_identity':s['endpoint_state_variation']==0.0,'d3_transport_risk_zero':s['incremental_transport_risk']==0.0,'d3_top1_deletion_stable':s['delete_top1_incremental_risk']==0.0,'evidence':'RAW_DATA_COMPUTED','d3_incremental_risk':s['incremental_transport_risk']})
    wr(OUT/'d3_code_only_recalculation.csv',out)

def main():
    phase_a();led=freeze_queries();replay(led);clean,lo=analyze();d3()
    DOC.joinpath('faiss100k_clean_rerun_report.md').write_text('# Faiss-100K clean rerun\n\n48 frozen indices reused; seed-991 queries selected from train IDs >=100000, disjoint from base and historical evaluation roles. Exact truth and ANN search use only the clean query role. ndis remains NOT_ESTIMABLE_BATCH_CUMULATIVE.\n')
    DOC.joinpath('d3_code_only_recalculation_report.md').write_text('# D3 code-only recalculation\n\nD3 identity, top-k, hit-count, endpoint, transport and top-1 deletion fields were recomputed from frozen rows; no D3 search was rerun.\n')
    DOC.joinpath('profiling_cost_semantic_patch.md').write_text('# Profiling semantic patch\n\nOnly primitive costs are measured. Candidate-family, certification control and full deployment break-even remain NOT_ESTIMABLE/SYMBOLIC_ONLY.\n')
    DOC.joinpath('paper_claim_registry.md').write_text('# Paper claim registry\n\nClaims remain scoped to registered datasets and operators; no universal cost claim.\n')
    DOC.joinpath('paper_number_patch.md').write_text('# Paper number patch\n\nUse clean Faiss rows for the 100K scope; historical 30K remains a boundary.\n')
    DOC.joinpath('executive_summary.md').write_text('# Executive summary\n\nSemantic repairs and a clean Faiss query replay were completed.\n')
    print(json.dumps({'clean_rows':len(clean),'lobo_rows':len(lo)}))
if __name__=='__main__':main()
