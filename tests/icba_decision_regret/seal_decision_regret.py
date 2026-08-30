import os,glob,hashlib
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));out=ROOT+'/results/icba_decision_regret/checksums.sha256'
paths=[]
for rel in ['docs/icba_decision_regret','results/icba_decision_regret','figures/icba_decision_regret','tests/icba_decision_regret','theory/icba_decision_regret']:
 paths += [p for p in glob.glob(ROOT+'/'+rel+'/**',recursive=True) if os.path.isfile(p) and p!=out]
paths += [ROOT+'/manifests/icba_decision_regret_decision.json']
with open(out,'w') as f:
 for p in sorted(paths):f.write(hashlib.sha256(open(p,'rb').read()).hexdigest()+'  '+os.path.relpath(p,ROOT)+'\n')
print(len(paths),out)
