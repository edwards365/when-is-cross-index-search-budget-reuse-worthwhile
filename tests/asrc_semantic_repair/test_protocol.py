#!/usr/bin/env python3
import os,json,hashlib,subprocess,pathlib
import numpy as np
from scipy.stats import beta
ROOT=pathlib.Path(__file__).resolve().parents[2]
def ok(x,msg):
 if not x: raise AssertionError(msg)
def main():
 split=json.load(open(ROOT/'manifests/graph_anns_positive_crossfit_split.json'))
 for ds,v in split['datasets'].items():
  folds={k:set(x) for k,x in v['folds'].items()}
  for cyc,roles in v['cycles'].items():
   vals=[folds[roles[r]] for r in ['source_train','source_calibration','target_sentinel','target_evaluation']]
   ok(all(not(vals[i]&vals[j]) for i in range(4) for j in range(i+1,4)),'role disjointness')
 ok(beta.ppf(.95,1,59)<=.05 and beta.ppf(.95,1,58)>.05,'CP zero-failure k_min')
 src=(ROOT/'tests/asrc_semantic_repair/run_repaired_asrc.py').read_text()
 ok('range(11,-1,-1)' in src,'fixed sequence');ok('ALPHA/3' in src,'alpha spending');ok('B6_FALLBACK' in src,'fallback')
 ok('target_evaluation' in src and 'select(raw,y,c,idx)' in src,'eval firewall/common event')
 ok('history' not in src.lower() and 'fingerprint' not in src.lower(),'no history/fingerprint')
 ok('validation-dev' not in src and 'formal-test' not in src,'sealed split non-access')
 # Cluster bootstrap determinism is fixed by seed and target_build unit.
 ok('default_rng(SEED)' in src and "cluster':'target_build'" in src,'cluster bootstrap determinism')
 # Old tracked outputs must be byte-identical to parent.
 p=subprocess.run(['git','diff','--name-only','6a8cbcf','--','results/graph_anns_positive_closure','docs/graph_anns_positive_closure'],cwd=ROOT,text=True,capture_output=True,check=True)
 ok(not p.stdout.strip(),'old outputs unchanged')
 from safety_events import safety_events
 a=np.array([0,11]);y=np.array([1,11]);c=np.array([0,1],bool);za,zr,_=safety_events(a,y,c);ok(za.tolist()==[True,True] and zr.tolist()==[True,False],'censor propagation')
 print('PROTOCOL_TEST_PASS: 12 checks')
if __name__=='__main__':main()
