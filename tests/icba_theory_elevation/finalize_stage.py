#!/usr/bin/env python3
import csv,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'results/icba_theory_elevation'; D=ROOT/'docs/icba_theory_elevation'; F=ROOT/'figures/icba_theory_elevation'
required=[D/'final_report.md',D/'executive_brief.md',D/'general_problem_definition.md',D/'tow1_theorem.md',D/'tow1_proof.md',D/'sample_complexity.md',D/'z1_information_model.md',R/'theorem_status.csv',R/'m_n_k_requirements.csv',R/'z1_field_audit.csv',R/'unified_gate_table.csv',R/'z1_pilot.csv',R/'z1_response_relation.csv',F/'z1_vs_budget_response.png']
assert all(p.exists() and p.stat().st_size for p in required)
pilot=list(csv.DictReader((R/'z1_pilot.csv').open())); assert len(pilot)==3 and all(x['gate_z1_c']=='FAIL' for x in pilot)
manifest={
 'schema_version':'1.0','stage':'ICBA_THEORY_ELEVATION','conditional_base':'a9f88bbcfd9b2c2f3e8a27e1471e16628b60cdb0',
 'branch':'exp/icba_theory_elevation','baseline_exactly_reproduced':False,'baseline_limitation':'INVALID_FULL_SEAL_BASELINE',
 'manual_override':'USER_DIRECTED_CONTINUE_2026-08-28','current_full_seal_checksums':'59/59',
 'legacy_microclosure_checksums':{'entries':123,'matching':111,'mismatching':8,'absent':4},
 'graphs':81,'query_budget_rows':972000,'directed_pairs':648,'unordered_pairs':324,'directed_collisions':94,'unordered_collisions':47,
 'tow1a':'FORMAL_PROOF_COMPLETE','tow1b':'FORMAL_PROOF_COMPLETE','multienvironment_extension_needed':False,
 'tow2':'FORMAL_PROOF_COMPLETE','tow3':'RESTRICTED_PROPOSITION','tow5':'PROOF_SKETCH',
 'z1_existing':True,'pilot_executed':True,'pilot_label':'Z1_PILOT_FAILED_RESPONSE_CONTROL',
 'decision':'GENERAL_THEORY_STRENGTHENED_NO_RECOVERY_CHANNEL','algorithm_design_authorized':False,'server_rental_needed':False,
 'validation_dev_accessed':False,'formal_test_accessed':False,'seed':991,'bootstrap_reps':5000}
m=ROOT/'manifests/icba_theory_elevation_decision.json'; m.write_text(json.dumps(manifest,indent=2)+'\n')
files=sorted(list(D.glob('*'))+list(R.glob('*'))+list(F.glob('*'))+list((ROOT/'tests/icba_theory_elevation').glob('*'))+[m])
files=[p for p in files if p.name!='checksums.sha256' and p.is_file() and '__pycache__' not in p.parts]
with (R/'checksums.sha256').open('w') as out:
 for p in files:out.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT))+'\n')
print(json.dumps({'artifacts':len(files),'decision':manifest['decision']}))
