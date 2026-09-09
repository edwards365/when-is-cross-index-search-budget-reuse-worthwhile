#!/usr/bin/env python3
import csv, hashlib, json, os, platform, shutil, subprocess
from pathlib import Path
import numpy as np

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
DATA=Path('/home/wlk/data500/graph_anns_e4')
PARENT='6829bbc377ca113fd8f8a94499a4af753dd95aa3'
HIST='6a8cbcf7cf9f8f2f6734b05132e13d0f21e476bb'
SEEDS=[83,97,109,127,149,163,181,197]
ORDERS=['random','lid_ascending','lid_descending']
DATASETS=['sift_100k','arxiv_nomic_100k']
EFS=[10,20,40,80,120,200]
FINAL_LABELS=['E4_STRONG_CONFIRMATION_TWO_DATASETS','E4_DATASET_CONDITIONED_CONFIRMATION','E4_NDC_CONFIRMED_RUNTIME_NOT_CONFIRMED','E4_WEAK_EFFECT_EXPLORATORY_ONLY','E4_CORE_PHENOMENON_NOT_CONFIRMED','E4_BLOCKED_PREFLIGHT_CONTRACT_OR_RESOURCE_FAILURE','E4_INVALID_CONFIRMATORY_PROTOCOL']

def sha_bytes(x): return hashlib.sha256(x).hexdigest()
def sha_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def write_json(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def write_csv(p,fields,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==PARENT
    for d in ['docs/graph_anns_e4','results/graph_anns_e4','tests/graph_anns_e4','manifests']:(ROOT/d).mkdir(parents=True,exist_ok=True)
    DATA.mkdir(parents=True,exist_ok=True)
    # IDs only: no vector or truth access. PCG64 and disjoint train-member ranges are frozen here.
    roles={}
    for j,ds in enumerate(DATASETS):
        rng=np.random.default_rng(991+1009*j)
        conf=np.sort(rng.choice(np.arange(200000,300000,dtype=np.int64),1000,replace=False))
        future=np.sort(rng.choice(np.arange(300000,400000,dtype=np.int64),1000,replace=False))
        sentinel=conf[:250];evaluation=conf[250:]
        roles[ds]={'historical_design_range':[100000,199999],'confirmatory_ids':conf.tolist(),'target_sentinel_ids':sentinel.tolist(),'confirmatory_evaluation_ids':evaluation.tolist(),'future_replication_ids':future.tolist()}
        for name,a in [('confirmatory',conf),('sentinel',sentinel),('evaluation',evaluation),('future',future)]:
            p=ROOT/f'manifests/graph_anns_e4_{ds}_{name}_ids.npy';np.save(p,a,allow_pickle=False)
    role_rows=[]
    for ds in DATASETS:
        sets={'historical_design':set(range(100000,200000)),'confirmatory_query':set(roles[ds]['confirmatory_ids']),'target_sentinel':set(roles[ds]['target_sentinel_ids']),'confirmatory_evaluation':set(roles[ds]['confirmatory_evaluation_ids']),'future_replication':set(roles[ds]['future_replication_ids'])}
        for a,A in sets.items():
            for b,B in sets.items():role_rows.append({'dataset':ds,'role_a':a,'role_b':b,'overlap':len(A&B),'allowed':a==b or {a,b}<={'confirmatory_query','target_sentinel','confirmatory_evaluation'}})
    write_csv(ROOT/'results/graph_anns_e4/role_overlap.csv',['dataset','role_a','role_b','overlap','allowed'],role_rows)
    builds=[]
    for ds in DATASETS:
        for seed in SEEDS:
            for order in ORDERS:
                builds.append({'dataset':ds,'build_id':f'{ds}__seed{seed}__{order}','seed':seed,'insertion_order':order,'M':16,'ef_construction':100,'threads':1,'status':'PREREGISTERED'})
    write_csv(ROOT/'results/graph_anns_e4/build_manifest.csv',list(builds[0]),builds)
    lid_src=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-cibs-stage1/results/hardness_portability_100k/lid_orders')
    lid_expected={'sift_100k':'68902a231481acb67601c492a82019921f136fa623c69b00c6ca360c2fce5cfa','arxiv_nomic_100k':'ee882bfa029deeac3c5f25842caf17911649b81f107bd65ad88aa94364d26c42'}
    lid={ds:{'path':str(lid_src/f'{ds}_order.npy'),'sha256':sha_file(lid_src/f'{ds}_order.npy'),'expected_sha256':lid_expected[ds]} for ds in DATASETS}
    baseline={
      'B0':{'name':'Always Fixed-Safe','ef':200,'status':'IMPLEMENTABLE'},
      'B1':{'name':'Same-Build Tuned','definition':'per-query monotone-safe budget on same build; descriptive nondeployable reference','status':'IMPLEMENTABLE'},
      'B2':{'name':'Source Policy Reuse','definition':'six frozen historical source policies, all ef=120; report all, no confirmatory selection','status':'IMPLEMENTABLE'},
      'B3':{'name':'Worst-Build Conservative','ef':200,'definition':'historical-build safe majorant','status':'IMPLEMENTABLE'},
      'B4':{'name':'Target Profiling/Recalibration','definition':'smallest ef with sentinel absolute risk one-sided CP UCB<=0.05, else 200; sentinel=250/evaluation=750','status':'IMPLEMENTABLE'},
      'B5':{'name':'Per-Target Safe Oracle','definition':'per-query monotone-safe budget from evaluation outcomes','status':'NON_DEPLOYABLE_UPPER_BOUND'},
      'B6':{'name':'Fixed Nominal ef','ef':120,'status':'IMPLEMENTABLE'}}
    config={'schema_version':1,'status':'FROZEN_BEFORE_CONFIRMATORY_QUERY_ACCESS','parent_commit':PARENT,'historical_variance_commit':HIST,'branch':'exp/graph_anns_e4_confirmatory_rebuild_matrix','scope':{'implementation':'hnswlib','version_commit':'3f3429661187e4c24a490a0f148fc6bc89042b3d','datasets':DATASETS,'base_size':100000,'confirmatory_queries_per_dataset':1000,'target_sentinel':250,'evaluation':750},'build_factorization':{'total':48,'per_dataset':24,'seeds':SEEDS,'orders':ORDERS,'independent_unit':'build','directed_pairs_per_dataset':552},'search':{'ef_grid':EFS,'k':10,'quality':'Recall@10','threshold':0.95,'warmup_queries':100,'latency_rounds':5,'cpu_affinity':[0],'threads':1,'interleave_seed':991},'risk':{'event':'Recall@10 < 0.95 OR endpoint infeasible','delta':0.05,'cp_alpha':0.05,'endpoint':200,'right_censored_is_failure':True,'raw_nonmonotone_preserved':True,'safe_majorant':'success at e and all registered larger e'},'roles':roles,'baselines':baseline,'statistics':{'build_cluster_bootstrap':{'replicates':5000,'seed':991},'query_paired_bootstrap':{'replicates':5000,'seed':991},'primary':['H1','H2'],'secondary':['H3','H4'],'dataset_primary_multiplicity':'Holm','robustness':['LOBO','leave-one-seed-out','leave-one-order-out','drop_max_contribution_build','drop_top_gain_1pct_query','drop_top_cost_1pct_query']},'final_labels':FINAL_LABELS,'large_output_root':str(DATA),'forbidden':['GloVe','Faiss','Vamana','Early Exit','CIBS','CALS','ASRC','validation-dev','formal-test','future-replication-access','post-confirmatory-tuning']}
    write_json(ROOT/'manifests/graph_anns_e4_preregistration.json',config)
    write_json(ROOT/'manifests/graph_anns_e4_role_manifest.json',{'status':'IDS_FROZEN_VECTORS_UNACCESSED','roles':roles})
    # Synthetic tests of event semantics and cluster-resampling invariants.
    raw=np.array([[0,1,0,1,1,1],[0,0,0,0,0,0]],dtype=bool)
    major=np.logical_and.accumulate(raw[:,::-1],axis=1)[:,::-1]
    assert major[0].tolist()==[False,False,False,True,True,True]
    assert not major[1].any()
    assert len(builds)==48 and all(sum(x['dataset']==d for x in builds)==24 for d in DATASETS)
    assert all(lid[d]['sha256']==lid[d]['expected_sha256'] for d in DATASETS)
    forbidden=[r for r in role_rows if not r['allowed'] and r['overlap']]
    assert not forbidden
    st=shutil.disk_usage(DATA)
    budget={'raw_vectors_gib':0.43,'exact_truth_gib':0.01,'serialized_indices_gib':15.0,'raw_search_records_gib':4.0,'runtime_repeats_gib':2.0,'trace_gib':0.0,'bootstrap_intermediate_gib':0.1,'figures_reports_gib':0.2,'temporary_peak_gib':20.0,'mandatory_reserve_gib':5.0,'stress_envelope_gib':651.672,'free_gib':st.free/2**30,'passes_stress_envelope':st.free/2**30>=651.672}
    write_json(ROOT/'results/graph_anns_e4/preflight_resource_budget.json',budget)
    audit={'head':PARENT,'python':platform.python_version(),'lid_orders':lid,'builds':len(builds),'forbidden_role_overlaps':len(forbidden),'free_gib':st.free/2**30,'resource_gate':budget['passes_stress_envelope'],'confirmatory_vectors_accessed':False,'future_replication_accessed':False,'validation_dev_accessed':False,'formal_test_accessed':False}
    write_json(ROOT/'results/graph_anns_e4/preflight_audit.json',audit)
    dev='''# E4 protocol deviation report\n\nThe frozen contract specifies 18--24 builds per dataset and calls the 48-build matrix preferred. E4 resolves this as 24 builds per dataset (48 total): eight new construction seeds crossed with the three historically registered insertion histories. The prompt grid `{10,20,40,80,120,200}` is used. Target recalibration is frozen to 250 sentinel queries and evaluated on a disjoint 750-query subset. No confirmatory vectors or truth were accessed while making these resolutions.\n'''
    (ROOT/'docs/graph_anns_e4/protocol_deviation_report.md').write_text(dev)
    (ROOT/'docs/graph_anns_e4/preregistered_protocol.md').write_text('# E4 preregistered protocol\n\nMachine-readable authority: `manifests/graph_anns_e4_preregistration.json`. This file and all query-role IDs are frozen before vector/truth access. Large artifacts are isolated under `/home/wlk/data500/graph_anns_e4`. Primary inference unit is the independent build.\n')
    (ROOT/'tests/graph_anns_e4/test_preflight.py').write_text('''import json, pathlib\nr=pathlib.Path(__file__).resolve().parents[2]\nx=json.loads((r/'manifests/graph_anns_e4_preregistration.json').read_text())\ndef test_frozen_contract():\n assert x['build_factorization']['total']==48\n assert x['search']['ef_grid']==[10,20,40,80,120,200]\n assert x['risk']['right_censored_is_failure']\n''')
    checks=[]
    for p in sorted(list((ROOT/'docs/graph_anns_e4').glob('*'))+list((ROOT/'results/graph_anns_e4').glob('*'))+list((ROOT/'tests/graph_anns_e4').glob('*'))+list((ROOT/'manifests').glob('graph_anns_e4*'))):
        if p.is_file(): checks.append(f'{sha_file(p)}  {p.relative_to(ROOT)}')
    (ROOT/'results/graph_anns_e4/preflight_checksums.sha256').write_text('\n'.join(checks)+'\n')
    print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
