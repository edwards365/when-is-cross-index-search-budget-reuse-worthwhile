#!/usr/bin/env python3
import hashlib, json, subprocess
from pathlib import Path

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs')
DOC=ROOT/'docs/theory_generalization'; RES=ROOT/'results/theory_generalization'
DOC.mkdir(parents=True,exist_ok=True); RES.mkdir(parents=True,exist_ok=True)
EXPS={
 'cross_index':('b82abf6bab8aae54b23aee5ccce5cde0ba5a3412','results/cross_index/g1/checksums.sha256'),
 'tournament':('80c505dcc3ec13855c700a0f59df3c042aa281ec','results/rebuild_algorithm/tournament/checksums.sha256'),
 'rcrs_fast':('01c491f712700bd146227c44db18848dd41d356a','results/rcrs_fast/checksums.sha256'),
 'rcrs_signal':('07ffc38187187d7edaf5e7c8165ebf4678ea1003','results/rcrs_signal/checksums.sha256')}

def show(commit,path):
 return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
def tree(commit):
 return subprocess.check_output(['git','ls-tree','-r','--name-only',commit],cwd=ROOT,text=True).splitlines()

audit={}
for name,(commit,checksum_path) in EXPS.items():
 files=tree(commit); checks=[]
 try:
  raw=show(commit,checksum_path).decode()
  for line in raw.splitlines():
   if not line.strip(): continue
   expected,path=line.split(None,1); path=path.strip().lstrip('*')
   try:
    blob=show(commit,path); actual=hashlib.sha256(blob).hexdigest()
    crlf=hashlib.sha256(blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()
    status='OK' if actual==expected else ('LINE_ENDING_NORMALIZATION_EQUIVALENT' if crlf==expected else 'MISMATCH')
   except subprocess.CalledProcessError: actual=None; status='MISSING_AT_FROZEN_COMMIT'
   checks.append({'path':path,'expected':expected,'actual':actual,'status':status})
 except subprocess.CalledProcessError:
  checks=[{'path':checksum_path,'status':'CHECKSUM_MANIFEST_MISSING'}]
 selected=[p for p in files if any(k in p.lower() for k in ('manifest','decision','report','checksum','per_query','trace','prefix','theor','split'))]
 audit[name]={'commit':commit,'tree_files':len(files),'selected_evidence_files':len(selected),
  'checksum_ok':sum(x['status'] in ('OK','LINE_ENDING_NORMALIZATION_EQUIVALENT') for x in checks),'checksum_problem':sum(x['status'] not in ('OK','LINE_ENDING_NORMALIZATION_EQUIVALENT') for x in checks),
  'checksum_detail':checks,'sample_evidence_paths':selected[-40:]}

audit['definition_notes']={
 'quality_target':'Recall@10 threshold tau=0.9 in RCRS signal; other frozen experiments must be read from their own manifests.',
 'budget':'Frozen ordered ef/search-list grid; no interpolation is treated as an observed budget.',
 'minimal_sufficient_budget':'Smallest observed budget attaining target at that point.',
 'minimal_stable_sufficient_budget':'Smallest budget after which every larger frozen budget attains target.',
 'right_censoring':'No stable sufficient budget exists on the frozen grid; record B>e_max.',
 'ndc':'Native distance-computation count; implementation-local and not automatically cross-implementation comparable.',
 'split_rule':'Cross-Index, Tournament, RCRS-fast and RCRS-signal query splits are distinct evidence units; Global/GCC/Oracle numbers are not pooled across splits.',
 'risk_rule':'Pointwise safety, empirical marginal risk and certified population risk remain separate.'}
audit['firewall']={'validation_dev_accessed':False,'formal_test_accessed':False,'new_graphs_built':False}
(RES/'input_audit.json').write_text(json.dumps(audit,indent=2)+'\n')

lines=['# Theory generalization input audit','',
'Phase 0 audits objects at their frozen Git commits rather than the later working-tree copies. This avoids treating expected downstream recomputation as corruption.','',
'| Experiment | Frozen commit | Tree files | Selected evidence | Frozen checksum OK | Problems |','|---|---:|---:|---:|---:|---:|']
for name in EXPS:
 a=audit[name]; lines.append(f"| {name} | `{a['commit'][:12]}` | {a['tree_files']} | {a['selected_evidence_files']} | {a['checksum_ok']} | {a['checksum_problem']} |")
lines += ['','## Frozen decisions','',
'- Cross-Index: `SHRINK_TO_HNSWLIB_IMPLEMENTATION_BOUNDARY`; 81 graphs and 972,000 rows.',
'- Rebuild Algorithm Tournament: `NO_DEPLOYABLE_CANDIDATE_KEEP_BOUNDARY_STUDY`; exploratory design simulation.',
'- RCRS fast feasibility: positive pointwise monotone tax and 500-query prefix equivalence; not a completed algorithm.',
'- RCRS Signal Pilot: `STOP_RCRS_NO_CERTIFIED_STOPPING_SIGNAL`; 0/16 GloVe policies certified.',
'','## Definition and comparability findings','']
for k,v in audit['definition_notes'].items(): lines.append(f'- **{k}:** {v}')
lines += ['','## Data firewall','','No validation-dev or formal-test member was opened by this audit. No graph was built. Existing untracked `logs/` were preserved.','',
'## Open audit items','','Exact source-specific `e0`, budget grids and split membership hashes will be transcribed from each frozen manifest before unified empirical calculations. A missing or mismatched frozen-commit checksum blocks reuse of that artifact but does not justify modifying it.','']
(DOC/'input_audit.md').write_text('\n'.join(lines))
print(json.dumps({k:{x:audit[k][x] for x in ('checksum_ok','checksum_problem')} for k in EXPS},indent=2))
