"""Reconstruct retained narrative results from a pinned saved-record archive.

No ANN, timing, training, or historical launcher is invoked. Output is new.
"""
import argparse,collections,csv,gzip,hashlib,io,json,math,os,platform,time,zipfile
from pathlib import Path
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
import numpy as np
from scipy.stats import beta
from reproduce_paper import need,close,write_csv

ROOT=Path(__file__).resolve().parent

class Inputs:
    def __init__(self,path):
        spec=json.loads((ROOT/'narrative/manifest.json').read_text())
        raw=path.read_bytes()
        need(hashlib.sha256(raw).hexdigest()==spec['archive_sha256'],'Archive identity')
        self.z=zipfile.ZipFile(io.BytesIO(raw))
        need(set(self.z.namelist())==set(spec['files']),'Archive members')
        for name,pin in spec['files'].items():
            data=self.z.read(name)
            need(len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'],'Member '+name)
    def raw(self,name):return self.z.read(name)
    def js(self,name):return json.loads(self.raw(name))
    def rows(self,name):
        data=self.raw(name)
        if name.endswith('.gz'):data=gzip.decompress(data)
        return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
    def npz(self,name):
        with np.load(io.BytesIO(self.raw(name)),allow_pickle=False) as a:
            return {k:a[k] for k in a.files}

def crossed_mean_ratio(failure,cost,endpoint,reps=5000):
    need(failure.shape==cost.shape==endpoint.shape,'Paired shapes')
    nt,nq=failure.shape[:2]
    need(nt==8 and nq==500 and np.isfinite(cost).all() and (endpoint>0).all(),'Recovery panel')
    rng=np.random.default_rng(991); draws=np.empty((reps,2))
    for i in range(reps):
        ti=rng.integers(0,nt,nt);qi=rng.integers(0,nq,nq)
        idx=np.ix_(ti,qi)
        draws[i]=[failure[idx].mean(),1-cost[idx].sum()/endpoint[idx].sum()]
    return np.quantile(draws,[.025,.975],axis=0)

def cube(rows,fields):
    targets=sorted({r['target_build'] for r in rows})
    queries=sorted({int(r['query_position']) for r in rows})
    need(len(targets)==8 and queries==list(range(500)),'Target/query membership')
    need(len(rows)==8*500*7,'Complete 56-direction panel')
    keys=[(r['target_build'],int(r['query_position']),r['source_build']) for r in rows]
    need(len(set(keys))==len(rows),'Duplicate response')
    ordered=sorted(rows,key=lambda r:(r['target_build'],int(r['query_position']),r['source_build']))
    for t in targets:
        group=[r for r in rows if r['target_build']==t]
        sources={r['source_build'] for r in group}
        need(len(sources)==7 and t not in sources,'Source directions')
    return {f:np.array([float(r[f]) for r in ordered]).reshape(8,500,7) for f in fields}

def recovery(data,out):
    records=[];decisions=[]
    for stage in ('s3','s4'):
        ev=data.rows(stage+'_eval.csv.gz');rt=data.rows(stage+'_runtime.csv.gz')
        es=data.js(stage+'_summary.json');rs=data.js(stage+'_runtime_summary.json')
        dr=data.rows(stage+'_decisions.csv')
        for ds in sorted({r['dataset'] for r in ev}):
            arms=sorted({r.get('arm','one_rung') for r in ev if r['dataset']==ds})
            for arm in arms:
                select=lambda rows:[r for r in rows if r['dataset']==ds and r.get('arm','one_rung')==arm]
                a=cube(select(ev),['failure','ndc','endpoint_ndc'])
                e=es[ds] if stage=='s3' else es[ds][arm]
                risk=float(a['failure'].mean());gain=float(1-a['ndc'].sum()/a['endpoint_ndc'].sum())
                close(risk,e['point']['risk'],'Recovery risk');close(gain,e['point']['ndc_gain'],'Recovery work')
                # Full point estimates for every retained arm; intervals for the
                # prospective primary result cited in the manuscript.
                records.append({'panel':stage,'dataset':ds,'arm':arm,'metric':'failure','point':risk,'low':'','high':''})
                records.append({'panel':stage,'dataset':ds,'arm':arm,'metric':'ndc_gain','point':gain,'low':'','high':''})
                times=select(rt)
                if times:
                    b=cube(times,['wall_ns','endpoint_wall_ns'])
                    mean=float(1-b['wall_ns'].sum()/b['endpoint_wall_ns'].sum())
                    expected=rs[ds] if stage=='s3' else rs[ds][arm]
                    close(mean,expected['point']['wall_gain'],'Recovery wall gain')
                    interval=['','']
                    if stage=='s3':
                        ci=crossed_mean_ratio(a['failure'],b['wall_ns'],b['endpoint_wall_ns'])
                        for actual,want in zip(ci[:,0],e['crossed_target_query_95ci']['risk']):close(float(actual),want,'S3 risk CI')
                        for actual,want in zip(ci[:,1],expected['crossed_target_query_95ci']['wall_gain']):close(float(actual),want,'S3 time CI')
                        records[-2].update(low=float(ci[0,0]),high=float(ci[1,0]))
                        interval=ci[:,1].tolist()
                    records.append({'panel':stage,'dataset':ds,'arm':arm,'metric':'wall_gain','point':mean,'low':interval[0],'high':interval[1]})
                d=select(dr);need(len(d)==56,'Decision count')
                counts=collections.Counter(r['decision'] for r in d)
                for key,count in counts.items():
                    decisions.append({'panel':stage,'dataset':ds,'arm':arm,'decision':key,'directions':count})
                action='deployed_action' if stage=='s3' else 'executed_action'
                if stage=='s4' and ds=='sift_100k' and arm in ('B1_FIXED_256_CERTIFIED','B2_SOURCE_ONE_RUNG_CERTIFIED'):
                    need(all(int(r[action])==256 for r in d),'SIFT action identity')
    write_csv(out/'recovery_points.csv',records);write_csv(out/'recovery_decisions.csv',decisions)
    write_csv(out/'registered_sensitivities.csv',data.rows('s3_sensitivity.csv'))
    return {'point_rows':len(records),'prospective_intervals_recomputed':4,
            'level':'Locked source-target/query records; original qualification and seven-repeat extraction upstream',
            'baseline_intervals':'Not recomputed; no baseline interval is reported in current narrative'}

def deep(data,out):
    inventory=data.js('deep_inventory.json'); names=sorted(r['build'] for r in inventory['builds'])
    grid=np.array([200,300,400,600,800,1200]); amap={int(x):i for i,x in enumerate(grid)}
    recall=np.full((8,1500,6),np.nan);ndc=recall.copy()
    for b,name in enumerate(names):
        rows=data.rows('deep/'+name+'.csv');need(len(rows)==9000,'Deep response size')
        seen=set()
        for r in rows:
            key=(int(r['query_id']),amap[int(r['ef'])]);need(key not in seen,'Duplicate Deep cell');seen.add(key)
            recall[b,*key]=float(r['recall']);ndc[b,*key]=float(r['ndc'])
    need(np.isfinite(recall).all() and np.isfinite(ndc).all(),'Deep complete grid')
    cp=lambda f:1.0 if f==500 else float(beta.ppf(.975,f+1,500-f))
    sources=[]
    for b in range(8):
        failures=(recall[b,:500]<.95).sum(axis=0)
        u=[1.0 if f==500 else float(beta.ppf(.95,int(f)+1,500-int(f))) for f in failures]
        sources.append(next((i for i,x in enumerate(u) if x<=.05),5))
    failures=np.zeros((8,500));cost=failures.copy();endpoint=failures.copy();decisions=[]
    for s in range(8):
        candidate=min(sources[s]+1,5)
        for t in range(8):
            if t==s:continue
            cf=int((recall[t,500:1000,candidate]<.95).sum());ef=int((recall[t,500:1000,-1]<.95).sum())
            decision='ABSTAIN' if cp(ef)>.05 else ('DEPLOY_CANDIDATE' if cp(cf)<=.05 else 'FALLBACK_ENDPOINT')
            need(decision!='ABSTAIN','Historical Deep panel unexpectedly abstains')
            action=candidate if decision=='DEPLOY_CANDIDATE' else 5
            failures[t]+=(recall[t,1000:,action]<.95);cost[t]+=ndc[t,1000:,action];endpoint[t]+=ndc[t,1000:,-1]
            decisions.append({'source_build':names[s],'target_build':names[t],'decision':decision,'action':int(grid[action]),'candidate_failures':cf,'endpoint_failures':ef})
    f=failures/7; expected=data.js('deep_summary.json')
    risk=float(f.mean());gain=float(1-cost.sum()/endpoint.sum());interval=crossed_mean_ratio(f,cost,endpoint)
    close(risk,expected['evaluation_risk'],'Deep risk');close(gain,expected['relative_mean_ndc_saving'],'Deep gain')
    for actual,want in zip(interval[:,0],expected['evaluation_risk_crossed_ci']):close(float(actual),want,'Deep risk CI')
    for actual,want in zip(interval[:,1],expected['relative_mean_ndc_saving_crossed_ci']):close(float(actual),want,'Deep work CI')
    need(sum(d['decision']=='DEPLOY_CANDIDATE' for d in decisions)==expected['deploy_candidate'],'Deep deployment')
    write_csv(out/'deep_recovery.csv',[{'risk':risk,'risk_low':interval[0,0],'risk_high':interval[1,0],'ndc_gain':gain,'gain_low':interval[0,1],'gain_high':interval[1,1]}])
    write_csv(out/'deep_decisions.csv',decisions)
    return {'raw_response_rows':72000,'decisions':56,'intervals':2,'level':'All recorded recall/work action responses, source selection and qualification reconstructed'}

def diagnostic(data,out):
    rows=[r for r in data.rows('diagnostic_queries.csv') if r['split']=='confirm']
    groups=collections.defaultdict(dict)
    for r in rows:
        key=(r['index'],r['dataset']);build=(r['seed'],r['history']);q=int(r['query_id'])
        a=groups[key].setdefault(build,{})
        need(q not in a,'Duplicate diagnostic query');a[q]=(int(r['stable_budget']),r['right_censored']=='True')
    expected={(r['index'],r['dataset'],r['source_seed'],r['source_history'],r['target_seed'],r['target_history']):r for r in data.rows('diagnostic_pairs.csv')}
    output=[];zero_cases=[]
    for (impl,ds),builds in sorted(groups.items()):
        need(len(builds)==9,'Nine diagnostic builds')
        for s,sv in sorted(builds.items()):
            for t,tv in sorted(builds.items()):
                if s==t:continue
                need(len(sv)==750 and sv.keys()==tv.keys(),'Diagnostic role pairing')
                cells=collections.defaultdict(set)
                # Preserve the original encoded stable-budget labels, including
                # its no-finite-tail marker. No grid-external interpretation.
                for q in sv:cells[sv[q][0]].add(tv[q][0])
                mixed=sum(len(v)>1 for v in cells.values())
                e=expected[impl,ds,*s,*t]
                need(mixed==int(e['aliasing_groups']) and len(cells)==int(e['source_summary_groups']),'Diagnostic cell match')
                if impl=='vamana' and ds in ('sift_100k','arxiv_nomic_100k') and s[1]==t[1]:
                    need(s[0]!=t[0] and not any(v[1] for v in tv.values()),'Finite Vamana cross-seed demands')
                    envelope={x:max(values) for x,values in cells.items()}
                    identical=sum(envelope[sv[q][0]]==tv[q][0] for q in sv)
                    need(identical==750 and float(e['information_tax_ndc_clipped'])==0,'Zero-cost action identity')
                    zero_cases.append({'dataset':ds,'source_seed':s[0],'target_seed':t[0],'order':s[1],'queries':750,'identical_actions':identical,'saved_cost_difference':float(e['information_tax_ndc_clipped']),'basis':'Same action per query, so the same recorded query/action cost is used on both sides'})
                output.append({'implementation':impl,'dataset':ds,'source_seed':s[0],'source_order':s[1],'target_seed':t[0],'target_order':t[1],'cells':len(cells),'mixed_cells':mixed,'target_no_finite_tail':sum(v[1] for v in tv.values())})
    need(len(output)==648 and sum(r['mixed_cells']>0 for r in output)==594,'Full diagnostic count')
    need(len(zero_cases)==36 and all(sum(r['dataset']==ds for r in zero_cases)==18 for ds in ('sift_100k','arxiv_nomic_100k')),'Vamana 18 pairs per dataset')
    write_csv(out/'diagnostic_pairs.csv',output)
    write_csv(out/'diagnostic_zero_cases.csv',zero_cases)
    return {'pairs':648,'mixed_pairs':594,'level':'Saved query stable-tail labels; original recall-to-label extraction upstream','cost_zero_cases':'36 pairs: per-query envelope and demand actions identical; zero cost follows use of same recorded action, not an independent NDC measurement'}

def refresh(data,out):
    expected=data.js('refresh100k_expected.json'); records=[]
    for ds in ('sift100k','arxiv_nomic_100k'):
        a=data.npz('refresh_'+ds+'.npz');d=a['refresh_risk_increment'];nt,nq=d.shape
        need(np.array_equal(d,a['source_risk'].astype(float)-a['old_source_risk'].astype(float)),'Refresh event identity')
        rng=np.random.default_rng(991);draws=[]
        for start in range(0,5000,100):
            bw=rng.multinomial(nt,np.ones(nt)/nt,size=100)/nt
            qw=rng.multinomial(nq,np.ones(nq)/nq,size=100)/nq
            draws.extend(np.einsum('ij,ij->i',bw@d,qw))
        ci=np.quantile(draws,[.025,.975]);e=next(r for r in expected['tests'] if r['test']==ds+'_matched_source_diagnostic')
        close(float(d.mean()),e['refresh_increment'],'100K refresh point')
        for actual,want in zip(ci,e['increment_ci']):close(float(actual),want,'100K refresh CI')
        records.append({'dataset':ds,'point':float(d.mean()),'low':float(ci[0]),'high':float(ci[1]),'targets':nt,'queries':nq})
    write_csv(out/'refresh100k.csv',records)
    return {'intervals':2,'level':'Saved paired query failure arrays; frozen-policy extraction upstream'}

def alternative_costs(out):
    from reproduce_paper import read_csv,check_inputs
    check_inputs()
    rows=read_csv(ROOT/'paper/inputs/component_ledger.csv'); records=[]
    for ds in sorted({r['dataset'] for r in rows}):
        by={r['method']:r for r in rows if r['dataset']==ds};p=by['TCP_deduplicated']
        def upfront(r):return (float(r['fixed_extra_ns'])+1000*float(r['acquisition_per_distinct_ns']))/1e9
        def service(r):return 1000*float(r['eight_target_service_ns_per_query'])/1e9
        for name,b in by.items():
            B=upfront(p)-upfront(b);D=service(b)-service(p)
            if name in ('TG1000','cache_exact'):need(B>0 and D<0,'Alternative no-repayment signs')
            first=math.floor(B/D)+1 if B>=0 and D>0 else ''
            records.append({'dataset':ds,'policy':'TCP_deduplicated','baseline':name,'Q':1000,'requests_per_round':8000,'policy_upfront_s':upfront(p),'baseline_upfront_s':upfront(b),'policy_round_service_s':service(p),'baseline_round_service_s':service(b),'B_seconds':B,'D_seconds':D,'first_round_delta_s':B-D,'first_strict_round':first,'no_positive_round_if_B_nonnegative_D_nonpositive':B>=0 and D<=0,'unmeasured_net_cost':'excluded, not assumed zero','baseline_scope':b['scope']})
    write_csv(out/'alternative_costs.csv',records)
    return {'comparisons':len(records),'level':'Component-ledger arithmetic, not matched-quality deployment measurement'}

def extensions(data,out):
    mapping=data.js('million_refresh/mapping.json'); expected=data.js('million_refresh/expected.json')
    rng=np.random.default_rng(991); records=[]
    # Preserve original panel order and the one RNG stream across datasets.
    for ds in ('sift-1m-heldout','arxiv-nomic-1.34m-heldout'):
        units=[r for r in mapping if r['dataset']==ds];need(len(units)==8,'Refresh pair count')
        risks=[];queries=None
        for r in units:
            a=data.npz('million_refresh/'+r['key']+'.npz')
            need(a['hits'].shape==(2,2,1000),'Refresh response shape')
            risk=(a['hits']<10).any(axis=1)
            need(np.array_equal(risk,a['z_abs']),'Refresh union event')
            need(np.array_equal(a['hits'][:,1]<10,a['z_endpoint']),'Refresh endpoint event')
            need(len(set(a['query_ids'].tolist()))==1000,'Refresh query IDs')
            if queries is None:queries=a['query_ids']
            need(np.array_equal(queries,a['query_ids']),'Shared refresh queries')
            action={'execute_candidate':0,'endpoint_fallback':1,'abstain':-1}[r['decision']]
            need(int(a['executed_arm'])==action,'Locked refresh action')
            risks.append(risk.astype(float))
        risks=np.array(risks);d=risks[:,1]-risks[:,0];draws=[]
        for _ in range(5000):
            pairs=rng.integers(0,8,8);qs=rng.integers(0,1000,1000)
            draws.append(d[np.ix_(pairs,qs)].mean())
        ci=np.quantile(draws,[.025,.975]);e=expected['dataset_results'][ds]['measures']['source_absolute_risk']
        close(float(d.mean()),e['paired_change_refreshed_minus_initial'],'Million refresh mean')
        for actual,want in zip(ci,e['crossed_bootstrap_95_percentile_ci']):close(float(actual),want,'Million refresh CI')
        for state,key in [(0,'initial_mean'),(1,'refreshed_mean')]:close(float(risks[:,state].mean()),e[key],'Refresh state mean')
        records.append({'dataset':ds,'event':'candidate-or-endpoint failure','pairs':8,'queries':1000,'initial':e['initial_mean'],'refreshed':e['refreshed_mean'],'change':float(d.mean()),'low':float(ci[0]),'high':float(ci[1]),'endpoint_deployments':sum(r['decision']=='endpoint_fallback' for r in units)})
    write_csv(out/'million_refresh.csv',records)
    transfer=[]
    for ds,panel in data.js('million_transfer.json')['datasets'].items():
        rows=panel['directed_rows'];need(len(rows)==56,'Transfer directions')
        risks=np.array([r['target_evaluation_failures_of_1000']/1000 for r in rows])
        close(float(risks.mean()),panel['mean_target_evaluation_risk_over_directions'],'Transfer count mean')
        need(not (risks>.05).any(),'Transfer empirical threshold')
        transfer.append({'dataset':ds,'directions':56,'queries_per_direction':1000,'mean_union_failure':float(risks.mean()),'directions_above_5_percent':int((risks>.05).sum()),'inference':'saved direction counts, not simultaneous certification'})
    write_csv(out/'million_transfer.csv',transfer)
    return {'refresh_intervals':2,'refresh_input':'full saved hit arrays and locked actions','transfer_input':'saved direction failure counts; query-level extraction upstream'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--parts',nargs='+',choices=['recovery','deep','diagnostic','refresh','cost','extensions'],default=['recovery','deep','diagnostic','refresh','cost','extensions'])
    args=ap.parse_args();need(not args.output.exists(),'Output exists');need(not args.output.resolve().is_relative_to(ROOT),'Output inside artifact')
    data=Inputs(args.archive);args.output.mkdir(parents=True);start=time.monotonic()
    try:
        results={}
        for key,fn in [('recovery',recovery),('deep',deep),('diagnostic',diagnostic),('refresh',refresh),('cost',lambda d,o:alternative_costs(o)),('extensions',extensions)]:
            if key in args.parts:
                results[key]=fn(data,args.output);print(key,'PASS',flush=True)
        report={'status':'PASS_SAVED_RECORD_RECONSTRUCTION','results':results,'python':platform.python_version(),'numpy':np.__version__,'elapsed_seconds':time.monotonic()-start,'ANN_runs':0,'timing_measurements':0}
        (args.output/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    except Exception as e:
        (args.output/'failure.json').write_text(json.dumps({'type':type(e).__name__,'error':str(e)})+'\n',encoding='utf-8');raise

if __name__=='__main__':main()
