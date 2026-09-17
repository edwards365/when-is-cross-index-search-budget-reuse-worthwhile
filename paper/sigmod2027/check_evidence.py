"""Independent arithmetic/CP checks for the compact manuscript evidence.

No SciPy, searches, raw truth, or experiment execution. CP is inverted from the
binomial CDF independently of the Beta quantile used in the reanalysis.
"""
from pathlib import Path
import csv, json, math, hashlib
import numpy as np

ROOT = Path(__file__).resolve().parent
D = ROOT / 'evidence' / 'w6_audit'
checks = []

def read(name):
    with (D/name).open(encoding='utf-8') as f:
        return list(csv.DictReader(f))

def check(name, ok):
    checks.append({'check': name, 'passed': bool(ok)})
    if not ok:
        raise AssertionError(name)

def close(a, b):
    return np.isclose(float(a), float(b), rtol=1e-10, atol=1e-10)

def cp(x, n, alpha):
    if x == n:
        return 1.0
    lo, hi = 0.0, 1.0
    coefficients = [math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1) for k in range(x+1)]
    for _ in range(70):
        p = (lo+hi)/2
        cdf = sum(math.exp(c+k*math.log(p)+(n-k)*math.log1p(-p)) for k,c in enumerate(coefficients))
        if cdf > alpha:
            lo = p
        else:
            hi = p
    return (lo+hi)/2

S, B, C, H = [read(f) for f in ['crossed_summary.csv','certification_per_build.csv','cost_components.csv','cost_horizons.csv']]
check('20 distinct dataset-target certificates', len(B)==20 and len({(b['dataset'],b['seed']) for b in B})==20)
check('original acceptance 19/20', sum(int(b['legacy_accept']) for b in B)==19)
check('joint acceptance 16/20', sum(int(b['joint_accept']) for b in B)==16)
check('joint decisions never add acceptance', all(int(b['joint_accept'])<=int(b['legacy_accept']) for b in B))
check('both single-policy zero-failure identities', all(close(cp(0,500,a),1-a**(1/500)) for a in [.05,.025]))
check('59-query minimum at zero failures', cp(0,58,.05)>.05 and cp(0,59,.05)<=.05)
check('Recall@10 threshold .95 means ten hits', math.ceil(10*.95)==10)
for b in B:
    ds, seed = b['dataset'], b['seed']
    x, xe, n = [int(b[k]) for k in ['candidate_cert_failures','endpoint_cert_failures','cert_n']]
    check(f'{ds}/{seed}: independently inverted candidate CP', close(cp(x,n,.05),b['candidate_ucb_05']) and close(cp(x,n,.025),b['candidate_ucb_025']))
    check(f'{ds}/{seed}: independently inverted endpoint CP', close(cp(xe,n,.025),b['endpoint_ucb_025']))
    check(f'{ds}/{seed}: qualified joint endpoint', float(b['endpoint_ucb_025'])<=.05)
    check(f'{ds}/{seed}: acceptance uses certification only', int(b['joint_accept'])==int(float(b['candidate_ucb_025'])<=.05))
for ds in ['sift100k','arxiv_nomic_100k']:
    a = np.load(D/f'{ds}_paired_arrays.npz')
    check(ds+': paired shapes', all(a[k].shape==(10,1000) for k in a.files))
    check(ds+': matched source risk arithmetic', np.allclose(a['refresh_risk_increment'],a['source_risk'].astype(float)-a['old_source_risk'].astype(float)))
    for lane in ['end','source','legacy','joint']:
        s = next(r for r in S if r['dataset']==ds and r['lane']==lane)
        d, r = a[lane], a[lane+'_risk']
        check(ds+'/'+lane+': risk, mean and ratio-of-means gain', close(r.mean(),s['risk']) and close(d.mean(),s['mean_ndc']) and close(1-d.mean()/a['end'].mean(),s['gain']))
        check(ds+'/'+lane+': pooled quantiles', close(np.quantile(d,.95),s['p95_ndc']) and close(np.quantile(d,.99),s['p99_ndc']))
        lobo = [1-np.delete(d,i,0).mean()/np.delete(a['end'],i,0).mean() for i in range(10)]
        check(ds+'/'+lane+': leave-one-target-out', close(min(lobo),s['min_loto_gain']))
    # Reproduce crossed sampling without importing the original implementation.
    rng = np.random.default_rng(991)
    draws = {k: [] for k in ['end','legacy','joint','legacy_risk','joint_risk']}
    for start in range(0,5000,100):
        wb = rng.multinomial(10,[.1]*10,size=100)/10
        wq = rng.multinomial(1000,np.full(1000,.001),size=100)/1000
        for k in draws:
            draws[k].extend(np.sum((wb @ a[k])*wq,axis=1))
    for lane in ['legacy','joint']:
        s = next(r for r in S if r['dataset']==ds and r['lane']==lane)
        gi = np.quantile(1-np.array(draws[lane])/np.array(draws['end']),[.025,.975])
        ri = np.quantile(draws[lane+'_risk'],[.025,.975])
        check(ds+'/'+lane+': 5000 crossed-bootstrap intervals', np.allclose(gi,[float(s['gain_ci_low']),float(s['gain_ci_high'])]) and np.allclose(ri,[float(s['risk_ci_low']),float(s['risk_ci_high'])]))
for c in C:
    total = sum(float(c[k]) for k in ['target_truth','selection_search','candidate_cert_search','endpoint_cert_extra_search','old_all_role_profile_search','old_truth_shared_across_builds'])
    check('/'.join(c[k] for k in ['dataset','seed','lane','scenario'])+': overhead identity', close(total,c['overhead_ndc']))
for h in H:
    group = [c for c in C if all(c[k]==h[k] for k in ['dataset','lane','scenario'])]
    overhead = np.mean([float(c['overhead_ndc']) for c in group])
    saving = np.mean([float(c['saving_per_query']) for c in group])
    check('/'.join(h[k] for k in ['dataset','lane','scenario','N'])+': cost identities', close(overhead/saving,h['break_even_ratio_of_means']) and close(int(h['N'])*saving-overhead,h['net_ndc']) and int(h['nonamortizing_builds'])==sum(float(c['saving_per_query'])<=0 for c in group))
check('all prior explicit reanalysis assertions passed', all(r['passed'] for r in json.loads((D/'audit_status.json').read_text())['tests'] if 'passed' in r))
frozen_hashes = {
    'darth_dataset_summary.csv':'124bd6ab81f31c1f21c2f127b67dd2eac7e8fb550ede94d4ff391c9d2a9a9ebf',
    'adaef_aggregate.json':'e4f0b3494df45e20105fb79e46a21a7e28a3ca944c60960281d516d46599bf62',
    'vamana_summary.csv':'a603f31593c2eb2db1e366989d6edb554107b8820aef67b8a0ef7ec1689d6182',
    'deep1m_summary.csv':'c42ec20fbadad95cc0cb80df7b18fae94fc69db8c61b8d9a673732d4f2f1c9ca'
}
# Git's frozen blob uses LF; two working-tree CSV snapshots use CRLF.
for name, expected in frozen_hashes.items():
    raw=(ROOT/'evidence'/'extensions'/name).read_bytes()
    check(name+': frozen Git content (LF-normalized)', hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()==expected)
report = {'status':'PASS','count':len(checks),'scope':'Compact derived evidence only; no claim of independent native-search replication.','checks':checks}
(D/'independent_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','checks':len(checks)}))
