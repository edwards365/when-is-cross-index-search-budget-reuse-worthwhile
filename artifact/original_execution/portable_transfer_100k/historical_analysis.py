import numpy as np
import math
GF=[16,32,64,128,256,512]
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
