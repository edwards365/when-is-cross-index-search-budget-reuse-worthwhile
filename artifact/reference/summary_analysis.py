# Inspection reference extracted from the frozen analysis.
# Only the resource import and host-bound main/launcher are omitted.
# This public extraction has NOT rerun the historical analysis.
"""New retrospective analysis only. Never calls ANN, an old worker, or bootstrap."""
import argparse
import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import sys
import time

import numpy as np
from scipy.stats import beta


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, obj):
    with Path(path).open('x') as f:
        json.dump(obj, f, indent=2, allow_nan=False)


def table(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('x', newline='') as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)


def labels(hits):
    safe = hits == 10
    tails = np.logical_and.accumulate(safe[:, ::-1, :], axis=1)[:, ::-1, :]
    lab = np.where(tails.any(axis=1), tails.argmax(axis=1), hits.shape[1])
    assert np.array_equal(lab < hits.shape[1], safe[:, -1, :])
    return lab, safe, tails


def summaries(lab, t, builds):
    src = np.delete(lab, t, axis=0).T
    out = {'vector': src, 'max': src.max(axis=1), 'action': np.minimum(src.max(axis=1), 10)}
    out.update({'single:' + builds[s]: lab[s] for s in range(8) if s != t})
    return out


def cells(x):
    _, inverse = np.unique(x, axis=0, return_inverse=True)
    return [np.flatnonzero(inverse == i) for i in range(int(inverse.max()) + 1)]


def coverage(x, b, bot):
    cc = cells(x); n = len(b)
    cnt = {'singleton_query_n': 0, 'mixed_query_n': 0, 'finite_mixed_query_n': 0,
           'finite_bot_mixed_query_n': 0, 'all_bot_query_n': 0, 'mixed_cell_n': 0}
    for ii in cc:
        u = np.unique(b[ii]); finite = u[u != bot]
        cnt['singleton_query_n'] += int(len(ii) == 1)
        cnt['mixed_query_n'] += len(ii) * int(len(u) > 1)
        cnt['mixed_cell_n'] += int(len(u) > 1)
        cnt['finite_mixed_query_n'] += len(ii) * int(len(finite) > 1)
        cnt['finite_bot_mixed_query_n'] += len(ii) * int(len(finite) > 0 and bot in u)
        cnt['all_bot_query_n'] += len(ii) * int(len(finite) == 0)
    return dict(n_query=n, n_cell=len(cc), max_cell_size=max(map(len, cc)),
                non_singleton_fraction=1-cnt['singleton_query_n']/n,
                mixed_query_fraction=cnt['mixed_query_n']/n,
                finite_mixed_fraction=cnt['finite_mixed_query_n']/n,
                finite_bot_mixed_fraction=cnt['finite_bot_mixed_query_n']/n,
                excluded_fraction=0, **cnt)


def objective(x, safe, costs, ordered):
    """Safe and costs are action x query. Costs are never assumed monotone."""
    cc = cells(x); n = costs.shape[1]
    feasible = np.stack([safe[:, ii].all(axis=1) for ii in cc])
    h = np.stack([costs[:, ii].sum(axis=1, dtype=np.float64) for ii in cc])
    h = np.where(feasible, h, np.inf)
    bad = ~feasible.any(axis=1)
    ind = np.where(safe, costs, np.inf).min(axis=0)
    jid = float(ind.mean()) if np.isfinite(ind).all() else None
    jx = float(h.min(axis=1).sum()/n) if not bad.any() else None
    jo = None
    if ordered and not bad.any():
        dp = h[0].copy()
        for row in h[1:]:
            dp = row + np.minimum.accumulate(dp)
        jo = float(dp.min()/n) if np.isfinite(dp).any() else None
    return dict(J_identity=jid, J_summary=jx, J_order=jo,
                information_gap=None if jid is None or jx is None else jx-jid,
                order_gap=None if jx is None or jo is None else jo-jx,
                individually_infeasible_n=int((~safe.any(axis=0)).sum()),
                infeasible_cell_n=int(bad.sum()),
                queries_in_infeasible_cells=sum(len(ii) for ii, fail in zip(cc, bad) if fail),
                objective_status='FEASIBLE' if jx is not None else 'INFEASIBLE',
                order_status=('NOT_DEFINED_VECTOR' if not ordered else 'FEASIBLE' if jo is not None else 'INFEASIBLE'))


def ucb(f, n, alpha):
    return 1.0 if f == n else float(beta.ppf(1-alpha, f+1, n-f))


def qualified(fc, fe, n, alpha):
    u, e = ucb(fc, n, alpha), ucb(fe, n, alpha)
    return ('UNDEPLOYABLE' if e > .05 else 'ENDPOINT' if u > .05 else 'CANDIDATE'), u, e


def selftest():
    h = np.array([[[10, 0, 10], [0, 10, 10], [10, 0, 10]]])
    b, s, t = labels(h)
    assert b.tolist() == [[2, 3, 0]] and s[0, 0, 0] and not t[0, 0, 0]
    safe = np.array([[1, 1], [1, 1], [1, 1]], dtype=bool)
    cost = np.array([[9, 9], [2, 3], [5, 4]], dtype=float)
    a = objective(np.array([0, 0]), safe, cost, True)
    assert a['J_summary'] == 2.5  # not the smallest safe action
    assert objective(np.array([0, 0]), np.array([[1,0],[0,1]], bool), cost[:2], True)['J_summary'] is None
    # Ordered optimum checked by enumeration, not prefix-min DP.
    for x, mask in [(np.array([0,1]), safe), (np.array([0,1]), np.array([[0,1],[1,1],[1,1]],bool))]:
        r = objective(x, mask, cost, True)
        brute = min(sum(cost[a,q] for q,a in enumerate(aa))/2 for aa in itertools.product(range(3),repeat=2)
                    if aa[0] <= aa[1] and all(mask[a,q] for q,a in enumerate(aa)))
        assert r['J_order'] == brute
    assert qualified(0, 500, 500, .05)[0] == 'UNDEPLOYABLE'
    assert qualified(50, 0, 500, .05)[0] == 'ENDPOINT'
    assert qualified(0, 0, 500, .05)[0] == 'CANDIDATE'
    assert ucb(500,500,.05) == 1
    print('SYNTHETIC_CONTROLS_PASS_NO_DATASET_ANALYSIS')


def run(conf, out):
    p = conf['paths']; policy = json.load(open(p['policy']))
    builds = policy['build_ids']; grid = np.array(policy['action_grid'])
    assert len(builds) == 8 and len(grid) == 11 and policy['k'] == 10 and policy['recall_target'] == .95
    audit = json.load(open(p['profile_audit']))
    assert audit['status'] == 'PASS_FULL_ORDERED_ID_AND_NATIVE_COUNT_AUDIT'
    locked = json.load(open(p['decision']))['rows']
    baselines = json.load(open(p['baselines']))
    membership = np.load(p['membership'], allow_pickle=False)
    cov, obj, bud, pol, sens, qchecks = [], [], [], [], [], []
    for ds, prefix in [('sift-1m-heldout','sift'),('arxiv-nomic-1.34m-heldout','arxiv')]:
        arrays = {}
        for role, n in [('target_certification',500),('target_evaluation',1000)]:
            path = next(r['array_path'] for r in audit['rows'] if r['dataset']==ds and r['role']==role)
            assert path in conf['inputs']
            with np.load(path, allow_pickle=False) as z:
                assert z['hits'].shape == (8,11,n) and z['ndc'].shape == (8,11,n)
                assert np.array_equal(z['action_grid'],grid) and z['build_ids'].tolist()==builds
                assert np.array_equal(z['query_ids'],membership[prefix+'_'+role+'_ids'])
                assert len(np.unique(z['query_ids'])) == n
                arrays[role] = {k:z[k].copy() for k in ['hits','ndc','query_ids']}
        assert not np.intersect1d(arrays['target_certification']['query_ids'],arrays['target_evaluation']['query_ids']).size
        ev, ce = arrays['target_evaluation'], arrays['target_certification']
        lab, safe, tails = labels(ev['hits']); lc, sc, _ = labels(ce['hits'])
        for t, build in enumerate(builds):
            head = dict(dataset=ds,target=build)
            keep = safe[t,-1]; nplus = int(keep.sum())
            assert nplus > 0
            sx = summaries(lab,t,builds)
            local_obj = {}
            for subset, kk in [('all', np.ones(1000,dtype=bool)),('endpoint_solvable',keep)]:
                for name, x in sx.items():
                    xx = x[kk]; bb = lab[t,kk]
                    cr = dict(**head,summary=name,subset=subset,**coverage(xx,bb,11))
                    cr['excluded_fraction'] = 1-len(bb)/1000
                    cr['excluded_n'] = 1000-len(bb); cr['query_weight'] = 1/len(bb)
                    cov.append(cr)
                    for criterion, ok in [('actual',safe[t][:,kk]),('stable_tail',tails[t][:,kk])]:
                        rr = objective(xx,ok,ev['ndc'][t][:,kk],name!='vector')
                        row = dict(**head,summary=name,subset=subset,criterion=criterion,n_query=len(bb),
                                   metric='native_hnswlib_ndc',**rr)
                        obj.append(row); local_obj[(subset,criterion,name)] = rr
                        if rr['information_gap'] is not None: assert rr['information_gap'] >= -1e-8
                        if rr['order_gap'] is not None: assert rr['order_gap'] >= -1e-8
                    if subset == 'endpoint_solvable':
                        cc=cells(xx); mm=np.empty(len(bb),dtype=int)
                        for ii in cc: mm[ii]=bb[ii].max()
                        pp=None
                        if name!='vector':
                            pp=np.empty(len(bb),dtype=int); top=0
                            for ii in cc:
                                top=max(top,int(bb[ii].max())); pp[ii]=top
                        bud.append(dict(**head,summary=name,n_query=len(bb),
                                        mean_individual_budget=float(grid[bb].mean()),mean_common_budget=float(grid[mm].mean()),
                                        mean_ordered_budget=None if pp is None else float(grid[pp].mean()),
                                        mean_rank_gap=float((mm-bb).mean()),
                                        mean_order_rank_gap=None if pp is None else float((pp-mm).mean())))
            for criterion in ['actual','stable_tail']:
                jj={name:local_obj[('endpoint_solvable',criterion,name)]['J_summary'] for name in sx}
                assert jj['vector'] <= jj['max']+1e-8 <= jj['action']+2e-8
                assert all(jj['vector'] <= val+1e-8 for name,val in jj.items() if name.startswith('single:'))
            ca=sx['action']; lock=next(r for r in locked if r['dataset']==ds and r['target_build']==build)
            assert lock['decision'] in ['TCP','ENDPOINT']
            for name, aa in [('candidate',ca),('locked',ca if lock['decision']=='TCP' else np.full(1000,10))]:
                ix=np.arange(1000); fail=~safe[t,aa,ix]; violation=aa<lab[t]
                assert np.all(fail <= violation)
                pol.append(dict(**head,policy=name,n_query=1000,decision=lock['decision'],failure_n=int(fail.sum()),
                                risk=float(fail.mean()),tail_violation_n=int(violation.sum()),
                                mean_budget=float(grid[aa].mean()),mean_ndc=float(ev['ndc'][t,aa,ix].mean()),
                                actual_zero_failure_admissible=not bool(fail.any()),tail_zero_failure_admissible=not bool(violation.any())))
            candc=np.minimum(np.delete(lc,t,axis=0).max(axis=0),10)
            for method in ['TCP','TG1000','TG500','fixed1600','endpoint2400']:
                old=next(r for r in baselines if r['dataset']==ds and r['target']==build and r['method']==method)
                n=250 if method=='TG500' else 500
                caction=candc[:n] if method=='TCP' else np.full(n,old['candidate_index'])
                eaction=ca if method=='TCP' else np.full(1000,old['candidate_index'])
                raw=~sc[t,caction,np.arange(n)]; endpoint=~sc[t,-1,:n]; union=raw|endpoint
                if method=='TCP':
                    assert np.array_equal(raw,union)
                    assert int(union.sum())==lock['cert_tcp_failures'] and int(endpoint.sum())==lock['cert_endpoint_failures']
                for event in ['raw','union']:
                    for alpha in [.05,.025]:
                        fc=int((raw if event=='raw' else union).sum()); fe=int(endpoint.sum())
                        dec,uc,ue=qualified(fc,fe,n,alpha)
                        original='CANDIDATE' if old['decision'] in ['TCP','REFERENCE'] else old['decision']
                        if (method=='TCP' and event=='union' and alpha==.05) or (method not in ['TCP','endpoint2400'] and event=='raw' and alpha==.025):
                            assert dec==original
                        aa=eaction if dec=='CANDIDATE' else np.full(1000,10)
                        sens.append(dict(**head,method=method,event=event,alpha=alpha,qualification_n=n,
                                         candidate_failures=fc,endpoint_failures=fe,raw_union_extra=int(union.sum()-raw.sum()),
                                         candidate_ucb=uc,endpoint_ucb=ue,decision=dec,original_decision=original,
                                         changed_from_original=dec!=original,deployable=dec!='UNDEPLOYABLE',
                                         evaluation_n=0 if dec=='UNDEPLOYABLE' else 1000,
                                         risk=None if dec=='UNDEPLOYABLE' else float((~safe[t,aa,np.arange(1000)]).mean()),
                                         mean_ndc=None if dec=='UNDEPLOYABLE' else float(ev['ndc'][t,aa,np.arange(1000)].mean())))
            qchecks.append(dict(**head,endpoint_failed_n=1000-nplus,endpoint_solvable_n=nplus,
                                actual_individual_infeasible_n=int((~safe[t].any(axis=0)).sum())))
    for name, rows in [('coverage',cov),('objectives',obj),('budgets',bud),('policy_bridge',pol),('qualification_sensitivity',sens),('target_feasibility',qchecks)]:
        table(out/(name+'.csv'),rows)
    # Every target is equally weighted; query weights already normalized within its subset.
    aggregates=[]
    for ds in policy['datasets']:
        for subset in ['all','endpoint_solvable']:
            for name in ['vector','max','action']:
                cv=[r for r in cov if r['dataset']==ds and r['subset']==subset and r['summary']==name]
                for criterion in ['actual','stable_tail']:
                    oo=[r for r in obj if r['dataset']==ds and r['subset']==subset and r['summary']==name and r['criterion']==criterion]
                    assert len(cv)==len(oo)==8
                    ag=dict(dataset=ds,subset=subset,summary=name,criterion=criterion,targets=8,
                            feasible_targets=sum(r['J_summary'] is not None for r in oo))
                    for key in ['non_singleton_fraction','mixed_query_fraction','finite_mixed_fraction','finite_bot_mixed_fraction','excluded_fraction']:
                        ag[key]=float(np.mean([r[key] for r in cv]))
                    for key in ['J_identity','J_summary','J_order','information_gap','order_gap']:
                        ag[key]=float(np.mean([r[key] for r in oo])) if all(r[key] is not None for r in oo) else None
                    aggregates.append(ag)
    table(out/'summary_aggregate.csv',aggregates)
    sa=[]
    for ds,method,event,alpha in itertools.product(policy['datasets'],['TCP','TG1000','TG500','fixed1600','endpoint2400'],['raw','union'],[.05,.025]):
        rows=[r for r in sens if (r['dataset'],r['method'],r['event'],r['alpha'])==(ds,method,event,alpha)]
        dep=[r for r in rows if r['deployable']]
        sa.append(dict(dataset=ds,method=method,event=event,alpha=alpha,targets=8,deployed_targets=len(dep),
                       candidate_targets=sum(r['decision']=='CANDIDATE' for r in rows),
                       endpoint_targets=sum(r['decision']=='ENDPOINT' for r in rows),
                       changed_targets=sum(r['changed_from_original'] for r in rows),
                       risk=None if not dep else float(np.mean([r['risk'] for r in dep])),
                       mean_ndc=None if not dep else float(np.mean([r['mean_ndc'] for r in dep]))))
    table(out/'qualification_aggregate.csv',sa)
    life=json.load(open(p['lifecycle'])); ledger=list(csv.DictReader(open(p['ledger'])))
    costrows=[]
    for d in life['datasets']:
        ds=d['dataset']; parts={k:d[k] for k in ['design_selection_cert_profile_ns','design_selection_cert_truth_ns','exact_base_acquisition_ns','certification_decision_compute_ns_allocated_half']}
        parts['role_firewall_ns_allocated_half']=d['role_firewall_wall_seconds_allocated_half']*1e9
        fixed=d['shared_eight_target_upfront_ns']-d['eight_graph_build_ns_operational_interfered']-d['eight_graph_median_fresh_reload_ns']
        assert math.isclose(sum(parts.values()),fixed,rel_tol=1e-12,abs_tol=.001)
        costrows.extend(dict(dataset=ds,component=k,seconds=v/1e9) for k,v in parts.items())
        costrows.append(dict(dataset=ds,component='fixed_net_setup_total',seconds=fixed/1e9))
    table(out/'fixed_cost_components.csv',costrows)
    return {'status':'COMPLETE_DERIVED_ANALYSIS_PENDING_SEPARATE_CHECK','datasets':2,'targets':16,
            'objective_rows':len(obj),'sensitivity_rows':len(sens),'new_ann_runs':0,'new_bootstrap_runs':0,
            'identity':'retrospective saved-response diagnostic, not deployable training or prospective validation',
            'conditional_cost_scope':'endpoint-solvable queries; equal target weights; per-target query weights renormalized',
            'ledger_rows_read':len(ledger),'full_safe_infeasible_not_replaced_by_conditional':True}

