"""Target-role supplement: complete sealed output equality; source-validated native counts.

Target counts are not independently event-traced; that limitation is explicit.
No original-wheel ndis or timing value is inferred.
"""
import argparse,json
from pathlib import Path
import numpy as np
from audit_e6_faiss_exact_dc_v1 import RESPONSE,load,sha

def run(c):
    if c['role']!='target_evaluation' or c['query_count']!=1000:raise ValueError('target role/count')
    for p,h in c['pins'].items():
        if sha(p)!=h:raise ValueError('pin '+p)
    roles=json.loads(Path(c['roles']).read_text())
    ids=next(x for x in roles['datasets'] if x['name']==c['dataset'])['roles']['target_evaluation']
    if ids!=c['query_ids']:raise ValueError('registered target order')
    for path in c['source_audit_reports']:
        a=json.loads(Path(path).read_text())
        if a['status']!='PASS_EXACT_DC_EVENTS_AND_SEALED_ORDERED_IDS' or a['query_count']!=500:raise ValueError('source validation')
    n,dim=c['query_count'],c['dim'];actions=c['actions']
    r=load(c['prefix']+'.responses.bin',b'E6RS',RESPONSE,n,dim)
    if len(r)!=n*len(actions):raise ValueError('response count')
    with np.load(c['reference'],allow_pickle=False) as f:
        if not np.array_equal(f['query_ids'],ids) or not np.array_equal(f['action_grid'],actions):raise ValueError('sealed reference role/actions')
        refs=f['topk'].copy()
    counts=[]
    for j,row in enumerate(r):
        if (int(row['ef']),int(row['q']))!=(actions[j//n],j%n):raise ValueError('row order')
        if not np.array_equal(row['ids'],refs[j//n,j%n]):raise ValueError('sealed target top10 mismatch')
        if len(np.unique(row['ids']))!=10 or not np.all(np.isfinite(row['dist'])):raise ValueError('returned values')
        value=int(row['scalar'])+4*int(row['batch'])
        if value!=int(row['count']) or value<=0:raise ValueError('count accounting')
        counts.append(value)
    return dict(status='PASS_TARGET_ORDERED_ID_EQUIVALENCE_SOURCE_VALIDATED_NATIVE_COUNTER',
                dataset=c['dataset'],build=c['build'],query_count=n,actions=actions,
                counts_by_action=np.asarray(counts,dtype=np.uint64).reshape(-1,n).tolist(),
                response_sha=sha(c['prefix']+'.responses.bin'),
                native_implementation='Pinned Faiss1.8 GENERIC DistanceComputer delegation; not historical AVX2 wheel ndis',
                target_counts_independently_event_traced=False,not_latency=True,policy_unchanged=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args()
    print(json.dumps(run(json.loads(a.config.read_text())),allow_nan=False),flush=True)
