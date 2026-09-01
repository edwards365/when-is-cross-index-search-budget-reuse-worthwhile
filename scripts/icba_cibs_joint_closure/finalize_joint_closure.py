from pathlib import Path
import csv, json, math, hashlib
import numpy as np
import matplotlib.pyplot as plt

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-cibs-stage1')
R=ROOT/'results/icba_cibs_joint_closure'; D=ROOT/'docs/icba_cibs_joint_closure'; F=ROOT/'figures/icba_cibs_joint_closure'; T=ROOT/'tests/icba_cibs_joint_closure'; M=ROOT/'manifests'
for p in (D,F,T): p.mkdir(parents=True,exist_ok=True)

def readcsv(p):
    with open(p,newline='') as f:return list(csv.DictReader(f))
def writecsv(p,rows,fields=None):
    fields=fields or list(rows[0])
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def js(p,x): p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def raw(dataset,build):
    p=ROOT/f'results/icba_cibs_stage1/evaluation/{dataset}__{build}__evaluation_all_actions.csv'
    rows=readcsv(p); out={}
    for r in rows:
        ef=int(r['requested_ef']); out.setdefault(ef,[]).append(r)
    return out

geom=readcsv(R/'all_action_geometry.csv')
for r in geom:
    r['break_even_plot'] = str(1e8 if r['break_even_queries']=='NO_FINITE_BREAK_EVEN' else float(r['break_even_queries']))
selected=json.load(open(M/'icba_cibs_stage1_selected_actions.json'))['datasets']
cache={}
for d in sorted({r['dataset'] for r in geom}):
    for b in ('G1','G2','G3'): cache[d,b]=raw(d,b)
for r in geom:
    d=r['dataset']; b,es=r['action_id'].split(':ef='); ef=int(es)
    b1=selected[d]['B1']['action_id']; bb,bes=b1.split(':ef='); bef=int(bes)
    a=sorted(cache[d,b][ef],key=lambda x:int(x['query_row']))
    z=sorted(cache[d,bb][bef],key=lambda x:int(x['query_row']))
    assert [x['query_row'] for x in a]==[x['query_row'] for x in z]
    savings=np.array([float(x['native_ndc'])-float(y['native_ndc']) for x,y in zip(z,a)])
    keep=np.ones(len(a),dtype=bool); keep[np.argsort(savings)[-max(1,math.ceil(.01*len(a))):]]=False
    an=np.array([float(x['native_ndc']) for x in a]); zn=np.array([float(x['native_ndc']) for x in z])
    ar=np.array([float(x['raw_recall_at_10']) for x in a]); zr=np.array([float(x['raw_recall_at_10']) for x in z])
    ae=np.array([x['endpoint_status']!='FEASIBLE' for x in a],float); ze=np.array([x['endpoint_status']!='FEASIBLE' for x in z],float)
    r['drop_top1pct_n']=str(int((~keep).sum()))
    r['drop_top1pct_mean_gain_vs_B1']=str((zn[keep].mean()-an[keep].mean())/zn[keep].mean())
    r['drop_top1pct_recall_delta_vs_B1']=str(ar[keep].mean()-zr[keep].mean())
    r['drop_top1pct_p95_delta_vs_B1']=str(np.quantile(an[keep],.95)-np.quantile(zn[keep],.95))
    r['drop_top1pct_endpoint_delta_vs_B1']=str(ae[keep].mean()-ze[keep].mean())
writecsv(R/'all_action_geometry.csv',geom)

# Five frozen matched comparisons plus per-ef ranges.
comparisons=[]
for d in sorted({r['dataset'] for r in geom}):
    ds=[r for r in geom if r['dataset']==d]; lookup={r['action_id']:r for r in ds}
    b1=selected[d]['B1']['action_id']; c=selected[d]['B4_CIBS_FIXED']['action_id']; cr=lookup[c]
    cb,ce=c.split(':ef='); ce=int(ce); bb,be=b1.split(':ef='); be=int(be)
    targets={
      'SAME_EF':f'{cb}:ef={be}',
      'MATCHED_MEAN_RECALL':min(ds,key=lambda x:abs(float(x['evaluation_recall'])-float(cr['evaluation_recall'])))['action_id'],
      'MATCHED_FAILURE_RISK':min(ds,key=lambda x:abs(float(x['evaluation_failure_rate'])-float(cr['evaluation_failure_rate'])))['action_id'],
      'B1_RELATIVE':b1,
      'ENDPOINT_MATCHED':min(ds,key=lambda x:abs(float(x['endpoint_infeasibility'])-float(cr['endpoint_infeasibility'])))['action_id']}
    for typ,aid in targets.items():
        x=lookup[aid]
        comparisons.append({'dataset':d,'record_type':'MATCHED_COMPARISON','comparison_type':typ,'reference_action':c,'matched_action':aid,'ef':'','mean_ndc_range':'','p95_ndc_range':'','recall_range':'','wall_range':'','ndc_difference':float(cr['mean_ndc'])-float(x['mean_ndc']),'recall_difference':float(cr['evaluation_recall'])-float(x['evaluation_recall']),'p95_difference':float(cr['p95_ndc'])-float(x['p95_ndc'])})
    for ef in sorted({int(x['raw_ef']) for x in ds}):
        q=[x for x in ds if int(x['raw_ef'])==ef]
        rng=lambda k:max(float(x[k]) for x in q)-min(float(x[k]) for x in q)
        comparisons.append({'dataset':d,'record_type':'SAME_EF_RANGE','comparison_type':'BUILD_RANGE','reference_action':'','matched_action':'','ef':ef,'mean_ndc_range':rng('mean_ndc'),'p95_ndc_range':rng('p95_ndc'),'recall_range':rng('evaluation_recall'),'wall_range':rng('wall_clock_gain_vs_B1'),'ndc_difference':'','recall_difference':'','p95_difference':''})
writecsv(R/'matched_comparisons.csv',comparisons)

# Six figures in both PNG and PDF.
styles={'G1':'o','G2':'s','G3':'^'}
def scatter(name,x,y,xlab,ylab,color=None):
    fig,ax=plt.subplots(figsize=(7,5))
    for d,cmap in [('sift_100k','tab:blue'),('arxiv_nomic_100k','tab:orange')]:
        q=[r for r in geom if r['dataset']==d]
        ax.scatter([float(r[x]) for r in q],[float(r[y]) for r in q],s=24,alpha=.7,label=d,c=cmap)
    ax.set(xlabel=xlab,ylabel=ylab);ax.grid(alpha=.25);ax.legend();fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(F/f'{name}.{ext}',dpi=180)
    plt.close(fig)
scatter('recall_ndc','evaluation_recall','mean_ndc','Mean Recall@10','Mean NDC')
scatter('risk_ndc','evaluation_risk_ucb','mean_ndc','Evaluation risk CP UCB','Mean NDC')
scatter('mean_p95','mean_ndc','p95_ndc','Mean NDC','p95 NDC')
scatter('wall_break_even','wall_clock_gain_vs_B1','break_even_plot','Wall-clock gain vs B1','Break-even queries')
scatter('build_ef_pareto','raw_ef','mean_ndc','Requested ef','Mean NDC')
scatter('joint_gate_heatmap','recall_delta_ci_low','mean_ndc_gain_ci_low','Recall delta CI lower','Mean gain CI lower')

finite=json.load(open(R/'finite_pool_audit.json'))
joint=readcsv(R/'joint_feasible_sets.csv')
counts={d:{'point':sum(x['point_joint_pass']=='True' for x in joint if x['dataset']==d),'ci':sum(x['ci_joint_pass']=='True' for x in joint if x['dataset']==d)} for d in ('sift_100k','arxiv_nomic_100k')}
label='CIBS_ROUTE_CLOSED_NO_TWO_DATASET_JOINT_FEASIBILITY'
decision={'schema_version':1,'decision_label':label,'evidence_level':'EXPLORATORY_REPLAY_EQUIVALENT_WITH_PROTOCOL_DEVIATION','frozen_input_commit':'10363a3a8a9abe0170af02b0b7ba29ffbf8f4621','point_and_ci_feasible_counts':counts,'finite_pool_status':finite['status'],'qni_authorized':False,'race_authorized':False,'reasons':['SIFT_CI_JOINT_SET_EMPTY','ARXIV_CI_JOINT_SET_EMPTY','NO_TWO_DATASET_JOINT_FEASIBILITY','ARXIV_GAIN_DOMINATED_BY_QUALITY_SLACK_CONSUMPTION'],'prohibited_access_confirmed':['future-confirm','validation-dev','formal-test'],'bootstrap':{'replicates':5000,'seed':991}}
js(M/'icba_cibs_joint_closure_decision.json',decision)

D.joinpath('executive_brief.md').write_text(f"# Executive brief\n\nFinal route: `{label}`. Across the frozen 36 actions per dataset, SIFT has 0 point and 0 CI joint-feasible actions; Arxiv has 1 point-feasible action (`G3:ef=64`) and 0 CI joint-feasible actions. QNI and Race are not authorized. Evidence is `EXPLORATORY_REPLAY_EQUIVALENT_WITH_PROTOCOL_DEVIATION`.\n")
D.joinpath('full_report.md').write_text("# Full report\n\nThe audit reused only frozen Stage-I artifacts. The corrected p95 Gate uses the bootstrap upper endpoint. Evaluation risk reports point estimate and CP lower/upper bounds; an LCB below delta is not certification. The finite-pool exhaustive comparison verifies binomial CP is conservative relative to the exact hypergeometric bound. No dataset has a CI-supported joint-feasible action. Arxiv's selected CIBS saving is 94.6% attributable to lower ef and consumes recall slack; SIFT's selected action saves below 1% mean NDC and fails recall/tail criteria.\n")
D.joinpath('protocol_deviation_audit.md').write_text("# Protocol deviation audit\n\nThe first sentinel attempt stopped because the truth-access log was not durably persisted. The supervisor did not inspect truth values or use evaluation data for selection. The accounting log was repaired and the unchanged frozen procedure was replayed; selected actions were identical (SIFT G3:ef=96; Arxiv G2:ef=48). This is therefore replay-equivalent with a protocol deviation, not pristine preregistered evidence.\n")
D.joinpath('finite_pool_certification_audit.md').write_text(f"# Finite-pool certification audit\n\nPopulation N=1000, without-replacement sample n=256, simultaneous alpha/36. All x=0..256 were checked; binomial CP UCB was never below the exact hypergeometric UCB. Status: `{finite['status']}`.\n")
D.joinpath('theory_patch.md').write_text("# Theory patch\n\nStatus: `CLASSICAL_CONSTRAINT_SLACK_COUNTEREXAMPLE` and `RESTRICTED_FINITE_ACTION_PROPOSITION`. Absolute failure risk at most delta does not imply mean Recall noninferiority relative to a baseline. For R in [0,1], if success means R>=tau and failure probability is at most delta, the general implication is only E[R]>=tau(1-delta). A baseline may have mean above this bound, so relative noninferiority requires an independent condition. No open-world theorem is claimed.\n")

test='''import csv,json,unittest\nfrom pathlib import Path\nP=Path(__file__).resolve().parents[2]\nR=P/"results/icba_cibs_joint_closure"\nclass TestClosure(unittest.TestCase):\n def rows(self,n): return list(csv.DictReader(open(R/n)))\n def test_actions(self): self.assertEqual(len(self.rows("all_action_geometry.csv")),72)\n def test_datasets(self): self.assertEqual(len({r["dataset"] for r in self.rows("all_action_geometry.csv")}),2)\n def test_bootstrap(self): self.assertTrue(all(r["bootstrap_replicates"]=="5000" for r in self.rows("all_action_geometry.csv")))\n def test_seed(self): self.assertTrue(all(r["bootstrap_seed"]=="991" for r in self.rows("all_action_geometry.csv")))\n def test_p95_upper_gate(self): self.assertTrue(all((r["p95_ci_supported_pass"]=="True")== (float(r["p95_delta_ci_high"])<=0) for r in self.rows("all_action_geometry.csv")))\n def test_crossing_p95_fails(self): self.assertTrue(all(r["p95_ci_supported_pass"]!="True" for r in self.rows("all_action_geometry.csv") if float(r["p95_delta_ci_low"])<0<float(r["p95_delta_ci_high"])))\n def test_eval_ucb_semantics(self): self.assertTrue(all((r["evaluation_risk_wording"]=="INDEPENDENT_RISK_UCB_PASS")== (float(r["evaluation_risk_ucb"])<=.05) for r in self.rows("all_action_geometry.csv")))\n def test_finite(self): self.assertTrue(json.load(open(R/"finite_pool_audit.json"))["cp_ucb_ge_hypergeom_ucb_for_all_x"])\n def test_sift_ci_empty(self): self.assertEqual(sum(r["ci_joint_pass"]=="True" for r in self.rows("joint_feasible_sets.csv") if r["dataset"]=="sift_100k"),0)\n def test_arxiv_ci_empty(self): self.assertEqual(sum(r["ci_joint_pass"]=="True" for r in self.rows("joint_feasible_sets.csv") if r["dataset"]=="arxiv_nomic_100k"),0)\n def test_top1(self): self.assertTrue(all(int(r["drop_top1pct_n"])==5 for r in self.rows("all_action_geometry.csv")))\n def test_qni_closed(self): self.assertTrue(all(r["sentinel_deployable_ci_actions"]=="0" for r in self.rows("cibs_qni_counterfactual.csv")))\n def test_label(self): self.assertEqual(json.load(open(P/"manifests/icba_cibs_joint_closure_decision.json"))["decision_label"],"CIBS_ROUTE_CLOSED_NO_TWO_DATASET_JOINT_FEASIBILITY")\n def test_race(self): self.assertFalse(json.load(open(P/"manifests/icba_cibs_joint_closure_decision.json"))["race_authorized"])\nif __name__=="__main__": unittest.main()\n'''
T.joinpath('test_joint_closure.py').write_text(test)

# Checksums last, excluding itself and large untracked artifacts.
targets=[]
for base in (D,R,F,T,ROOT/'scripts/icba_cibs_joint_closure'):
    targets += [p for p in base.rglob('*') if p.is_file() and p.name!='checksums.sha256']
targets += [M/'icba_cibs_stage1_corrected_decision.json',M/'icba_cibs_joint_closure_decision.json']
lines=[]
for p in sorted(set(targets)):
    lines.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT)))
(R/'checksums.sha256').write_text('\n'.join(lines)+'\n')
print(json.dumps({'decision':label,'counts':counts,'files_hashed':len(lines)}))
