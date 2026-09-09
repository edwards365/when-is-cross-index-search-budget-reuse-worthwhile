import csv,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2]
X=R/'results/icba_vamana_stage1'
def rows(n):return list(csv.DictReader((X/n).open()))
def test_h1_two():assert len(rows('h1_summary.csv'))==2
def test_h2_two():assert len(rows('h2_summary.csv'))==2
def test_gates():assert all(x['detection_gate']=='True' and x['materiality_gate']=='True' for x in rows('h1_summary.csv'))
def test_event_complete():assert all(abs(sum(float(v) for k,v in x.items() if k!='dataset')-1)<1e-12 for x in rows('event_composition.csv'))
def test_no_leak():assert all(x['content_overlap']=='0' and x['prior_truth_accessed']=='False' for x in rows('query_role_audit.csv'))
def test_builds():assert len(rows('build_manifest.csv'))==24
def test_distinct():
 r=rows('build_manifest.csv');assert all(len({x['index_sha256'] for x in r if x['dataset']==d})==12 for d in {x['dataset'] for x in r})
def test_bootstrap():assert len(rows('bootstrap_summary.csv'))==8 and all(x['replicates']=='5000' and x['seed']=='991' for x in rows('bootstrap_summary.csv'))
def test_lobo():assert sum(x['analysis']=='LOBO' for x in rows('robustness.csv'))==24
def test_decision():assert json.loads((R/'manifests/icba_vamana_stage1_decision.json').read_text())['decision']=='VAMANA_STRONG_EXTERNAL_REPLICATION_TWO_DATASETS'
def test_cost_scope():assert all(float(x['cost_ci_low'])<0<float(x['cost_ci_high']) for x in rows('h2_summary.csv'))
def test_claims():assert {'ALLOW','FORBID'}=={x['status'] for x in rows('claim_registry.csv')}
