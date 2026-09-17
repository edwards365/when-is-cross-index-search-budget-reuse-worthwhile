"""Read frozen refresh95 responses; write only this paper's derived review audit.

No index construction, search, raw truth access, selection retuning or old output
overwrite. Joint-alpha replay is explicitly post-hoc, not preregistered evidence.
"""
from pathlib import Path
import argparse, csv, importlib.util, json
import numpy as np
from scipy.stats import beta

def write(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def cp(x,n,alpha):
    return 1.0 if x==n else float(beta.ppf(1-alpha,x+1,n-x))

def boot(arrays, reps=5000):
    """Crossed product bootstrap: same query weights for all sampled targets.

    Conditions on the stored source histories and frozen selected shifts.
    Does not re-fit policies, resample the source history, or certify new builds.
    """
    rng=np.random.default_rng(991);b,q=next(iter(arrays.values())).shape
    out={k:np.empty(reps) for k in arrays}
    for start in range(0,reps,100):
        n=min(100,reps-start)
        bw=rng.multinomial(b,np.ones(b)/b,size=n)/b
        qw=rng.multinomial(q,np.ones(q)/q,size=n)/q
        for k,a in arrays.items():out[k][start:start+n]=np.einsum('ij,ij->i',bw@a,qw)
    return out

def ci(x):return [float(v) for v in np.quantile(x,[.025,.975])]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--replay',type=Path,required=True);a=ap.parse_args()
    out=Path(__file__).parent/'w6_audit';out.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('frozen',a.repo/'scripts/graph_anns_phase3_ea85/analyze_phase2_refresh95.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    summary=[];buildrows=[];costrows=[];horizons=[];role_checks=[];tests=[]
    frozen=list(csv.DictReader((a.repo/'results/graph_anns_phase3_ea85/refresh95/per_build.csv').open()))
    fdict={(r['dataset'],int(r['seed']),r['method']):r for r in frozen}
    for ds in m.DATASETS:
        old={};target={};ids={};mins={role:{} for role in m.ROLES}
        for role in m.ROLES:
            for seed in m.SEEDS:
                qi,r,d=m.load_tensor(a.replay,ds,'old',seed,role);old[seed,role]=(r,d);mins[role][seed]=m.minimal_action_indices(r)
                tq,tr,td=m.load_tensor(a.replay,ds,'target_refresh05',seed,role)
                assert np.array_equal(qi,tq)
                if role in ids:assert np.array_equal(ids[role],qi)
                ids[role]=qi;target[seed,role]=(tr,td)
        # Replay IDs may be role-local; content isolation belongs to frozen role manifest.
        role_checks.append({'dataset':ds,'cross_build_ids_aligned':True,'within_file_ids_unique':all(len(set(v))==len(v) for v in ids.values()),'role_isolation_source':'refresh95_inputs/input_manifest and content-hash audit; row IDs can be local'})
        arrays={k:[] for k in ['end','end_risk','source','source_risk','old_source_risk','refresh_risk_increment','legacy','legacy_risk','joint','joint_risk']}
        dsbuild=[]
        for seed in m.SEEDS:
            base={role:m.source_pool_indices(mins[role],seed) for role in m.ROLES}
            sr,sd=target[seed,'selection'];cr,cd=target[seed,'certification'];er,ed=target[seed,'cold_evaluation']
            shift,_,_=m.choose_shift(sr,base['selection'])
            cidx=m.shift_indices(base['certification'],shift);eidx=m.shift_indices(base['cold_evaluation'],shift)
            cer,ced=m.outcomes(cr,cd,cidx);evr,evd=m.outcomes(er,ed,eidx)
            sourcer,sourced=m.outcomes(er,ed,base['cold_evaluation'])
            oldr,_=m.outcomes(*old[seed,'cold_evaluation'],base['cold_evaluation'])
            oldcr,_=m.outcomes(*old[seed,'certification'],base['certification'])
            sourcecr,_=m.outcomes(cr,cd,base['certification'])
            x=int(np.sum(cer<.95));xe=int(np.sum(cr[-1]<.95));n=cr.shape[1]
            row={'dataset':ds,'seed':seed,'shift':shift,'candidate_cert_failures':x,'endpoint_cert_failures':xe,'cert_n':n,'candidate_ucb_05':cp(x,n,.05),'candidate_ucb_025':cp(x,n,.025),'endpoint_ucb_025':cp(xe,n,.025)}
            row.update({'old_source_eval_risk':float(np.mean(oldr<.95)),'old_source_cp':cp(int(np.sum(oldcr<.95)),n,.05),'target_source_cp':cp(int(np.sum(sourcecr<.95)),n,.05)})
            arrays['old_source_risk'].append(oldr<.95);arrays['refresh_risk_increment'].append((sourcer<.95).astype(float)-(oldr<.95).astype(float))
            arrays['end'].append(ed[-1]);arrays['end_risk'].append(er[-1]<.95);arrays['source'].append(sourced);arrays['source_risk'].append(sourcer<.95)
            for lane,alpha in [('legacy',.05),('joint',.025)]:
                accept=cp(x,n,alpha)<=.05;epass=cp(xe,n,alpha)<=.05
                d=evd if accept else ed[-1];r=evr if accept else er[-1]
                arrays[lane].append(d);arrays[lane+'_risk'].append(r<.95)
                row.update({lane+'_accept':int(accept),lane+'_qualified':int(accept or epass),lane+'_risk':float(np.mean(r<.95)),lane+'_gain':float(1-d.mean()/ed[-1].mean()),lane+'_p95':float(np.quantile(d,.95)),lane+'_p99':float(np.quantile(d,.99))})
            row.update({'source_risk':float(np.mean(sourcer<.95)),'endpoint_risk':float(np.mean(er[-1]<.95)),'endpoint_p95':float(np.quantile(ed[-1],.95)),'endpoint_p99':float(np.quantile(ed[-1],.99))})
            fr=fdict[ds,seed,'TARGET_SELECTION_TCP_RECALIBRATION']
            assert shift==int(fr['selection_shift'])
            assert np.isclose(row['legacy_risk'],float(fr['evaluation_risk']))
            assert np.isclose(np.mean(arrays['legacy'][-1]),float(fr['mean_dists']))
            buildrows.append(row);dsbuild.append(row)
            profiles={role:sum(m.sequential_profile_cost(old[s,role][1],mins[role][s]) for s in m.SEEDS if s!=seed) for role in m.ROLES}
            # Only distinct candidate/endpoint search calls are charged on cert IDs.
            endpoint_extra=float(cd[-1,cidx!=len(m.EFS)-1].sum())
            target_acq=float(sd.sum()+ced.sum()+endpoint_extra+100000*1000)
            old_profile=float(sum(profiles.values()))
            old_truth=float(100000*sum(len(v) for v in ids.values()))
            # Old base membership is common across source builds: exact truth reused.
            for lane in ['legacy','joint']:
                saving=float(ed[-1].mean()-arrays[lane][-1].mean())
                for scenario,overhead in [('cached_history',target_acq),('cold_complete_history',target_acq+old_profile+old_truth)]:
                    costrows.append({'dataset':ds,'seed':seed,'lane':lane,'scenario':scenario,'target_truth':100000*1000,'selection_search':float(sd.sum()),'candidate_cert_search':float(ced.sum()),'endpoint_cert_extra_search':endpoint_extra,'old_all_role_profile_search':old_profile if scenario.startswith('cold') else 0,'old_truth_shared_across_builds':old_truth if scenario.startswith('cold') else 0,'overhead_ndc':overhead,'saving_per_query':saving,'break_even':overhead/saving if saving>0 else 'INF'})
        arrays={k:np.stack(v) for k,v in arrays.items()};draws=boot(arrays)
        tests.append({'test':ds+'_matched_source_diagnostic','old_source_risk':float(arrays['old_source_risk'].mean()),'refresh_increment':float(arrays['refresh_risk_increment'].mean()),'increment_ci':ci(draws['refresh_risk_increment']),'old_source_qualified':sum(r['old_source_cp']<=.05 for r in dsbuild),'source_qualified_target_rejected':sum(r['old_source_cp']<=.05 and r['target_source_cp']>.05 for r in dsbuild)})
        for lane in ['end','source','legacy','joint']:
            d=arrays[lane];r=arrays[lane+'_risk'];gain=1-d.mean()/arrays['end'].mean();gc=ci(1-draws[lane]/draws['end']);rc=ci(draws[lane+'_risk'])
            lobo=[float(1-np.delete(d,i,axis=0).mean()/np.delete(arrays['end'],i,axis=0).mean()) for i in range(len(m.SEEDS))]
            rel=1-d.mean(1)/arrays['end'].mean(1);drop=int(np.argmax(rel))
            # One common query resample and a target-only resample: sensitivity axes.
            rng=np.random.default_rng(991);bw=rng.multinomial(10,np.ones(10)/10,5000)/10;qw=rng.multinomial(d.shape[1],np.ones(d.shape[1])/d.shape[1],5000)/d.shape[1]
            bci=ci(1-(bw@d.mean(1))/(bw@arrays['end'].mean(1)));qci=ci(1-(qw@d.mean(0))/(qw@arrays['end'].mean(0)))
            summary.append({'dataset':ds,'lane':lane,'risk':float(r.mean()),'risk_ci_low':rc[0],'risk_ci_high':rc[1],'gain':float(gain),'gain_ci_low':gc[0],'gain_ci_high':gc[1],'mean_ndc':float(d.mean()),'p95_ndc':float(np.quantile(d,.95)),'p99_ndc':float(np.quantile(d,.99)),'min_loto_gain':min(lobo),'delete_max_gain':lobo[drop],'build_only_gain_ci_low':bci[0],'build_only_gain_ci_high':bci[1],'query_only_gain_ci_low':qci[0],'query_only_gain_ci_high':qci[1],'p95_worse_builds':int(sum(np.quantile(d[i],.95)>np.quantile(arrays['end'][i],.95) for i in range(10))),'p99_worse_builds':int(sum(np.quantile(d[i],.99)>np.quantile(arrays['end'][i],.99) for i in range(10)))})
        np.savez_compressed(out/(ds+'_paired_arrays.npz'),**arrays)
        for lane in ['legacy','joint']:
            for scenario in ['cached_history','cold_complete_history']:
                rows=[r for r in costrows if r['dataset']==ds and r['lane']==lane and r['scenario']==scenario];oh=np.array([r['overhead_ndc'] for r in rows]);save=np.array([r['saving_per_query'] for r in rows])
                rng=np.random.default_rng(991);idx=rng.integers(0,10,(5000,10));rat=oh[idx].mean(1)/save[idx].mean(1);ratci=ci(rat)
                for N in [1000,10000,100000,1000000,10000000]:
                    net=N*save-oh;netci=ci(net[idx].mean(1))
                    horizons.append({'dataset':ds,'lane':lane,'scenario':scenario,'N':N,'break_even_ratio_of_means':float(oh.mean()/save.mean()),'break_even_ci_low':ratci[0],'break_even_ci_high':ratci[1],'nonamortizing_builds':int(np.sum(save<=0)),'net_ndc':float(net.mean()),'net_ci_low':netci[0],'net_ci_high':netci[1],'min_loto_net':float(min(np.delete(net,i).mean() for i in range(10)))})
        tests.append({'test':ds+'_legacy_reproduction_all_builds','passed':True})
    write(out/'crossed_summary.csv',summary);write(out/'certification_per_build.csv',buildrows);write(out/'cost_components.csv',costrows);write(out/'cost_horizons.csv',horizons);write(out/'id_alignment.csv',role_checks)
    tests += [{'test':'cp_zero_failure_identity','passed':bool(np.isclose(cp(0,59,.05),1-.05**(1/59)))},{'test':'joint_all_qualified','passed':all(r['joint_qualified']==1 for r in buildrows)},{'test':'tightening_never_adds_acceptance','passed':all(r['joint_accept']<=r['legacy_accept'] for r in buildrows)}]
    (out/'audit_status.json').write_text(json.dumps({'tests':tests,'analysis_status':'POST_HOC_FROZEN_RESPONSE_REANALYSIS','bootstrap':'crossed target-build x shared-query product resampling; 5000; seed991; conditional on histories and selected shifts','certification':'two policies alpha=.025 each; per fixed target union <=.05, not campaign simultaneous','cost':'NDC arithmetic, not wallclock; cached and cold; old truth shared across builds; overhead conservatively charged in full'},indent=2)+'\n')
    print(json.dumps({'tests':tests,'summary':summary,'acceptance':{lane:sum(r[lane+'_accept'] for r in buildrows) for lane in ['legacy','joint']}},indent=2))

if __name__=='__main__':main()
