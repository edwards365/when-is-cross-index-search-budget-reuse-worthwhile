#!/usr/bin/env python3
import csv,json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; R=ROOT/'results/icba_open_world'; F=ROOT/'figures/icba_open_world'; D=ROOT/'docs/icba_open_world'; M=ROOT/'manifests'
F.mkdir(exist_ok=True)
fac=list(csv.DictReader(open(R/'factorial_cells.csv'))); sent=list(csv.DictReader(open(R/'sentinel_learning_curve_fast.csv'))); dist=list(csv.DictReader(open(R/'build_observable_distance_fast.csv')))
gates=[
 {'gate':'A','status':'PASS','evidence':'81 graphs; 972000 rows; 648 directed pairs; 123/123 SHA256'},
 {'gate':'B','status':'PASS','evidence':'Feasible-only open-world risk and top-1%-deleted risk exceed 0.05 for all three implementations'},
 {'gate':'C','status':'PASS_STRUCTURAL_FAILURE','evidence':'All six SIFT/Arxiv implementation cells remain above 0.05 at k=256; no decreasing-to-safe trend'},
 {'gate':'D_Z0','status':'FAIL','evidence':'94 empirical Z0-near/response-far collision candidates across frozen directed pairs'},
 {'gate':'D_Z1','status':'NOT_ESTIMABLE','evidence':'No common frozen deployable unlabeled runtime fingerprint across implementations'},
 {'gate':'THEORY_DIRECTION','status':'OPEN_WORLD_IMPOSSIBILITY','evidence':'Endpoint control and more labeled sentinels do not remove risk; deployable observables fail/absent'},
]
with open(R/'fast_gate_table.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(gates[0]));w.writeheader();w.writerows(gates)

import struct,zlib
W,H=720,440
def write_png(path, points, bars=False):
 pix=bytearray([255]*(W*H*3))
 def dot(x,y,c=(20,70,160),rad=3):
  for yy in range(max(0,y-rad),min(H,y+rad+1)):
   for xx in range(max(0,x-rad),min(W,x+rad+1)):
    i=(yy*W+xx)*3; pix[i:i+3]=bytes(c)
 for x in range(55,W-20): dot(x,H-45,(0,0,0),0)
 for y in range(20,H-44): dot(55,y,(0,0,0),0)
 if bars:
  for x,y in points:
   for xx in range(max(56,x-18),min(W-20,x+19)):
    for yy in range(y,H-45):
     i=(yy*W+xx)*3; pix[i:i+3]=bytes((35,110,175))
 else:
  for x,y in points: dot(x,y)
 raw=b''.join(b'\x00'+bytes(pix[y*W*3:(y+1)*W*3]) for y in range(H))
 def ch(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw,9))+ch(b'IEND',b''))
def write_pdf(path,title,points,bars=False):
 ops=['0.8 w 50 45 m 700 45 l S 50 45 m 50 420 l S']
 for x,y in points:
  py=H-y
  ops.append((f'{x-12} 45 {24} {max(1,py-45)} re f' if bars else f'{x-2} {py-2} 4 4 re f'))
 stream=('\n'.join(ops)).encode(); objs=[]
 objs.append(b'<< /Type /Catalog /Pages 2 0 R >>');objs.append(b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>')
 objs.append(b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 720 440] /Contents 4 0 R >>');objs.append(f'<< /Length {len(stream)} >>\nstream\n'.encode()+stream+b'\nendstream')
 out=bytearray(b'%PDF-1.4\n');offs=[0]
 for i,o in enumerate(objs,1): offs.append(len(out));out+=f'{i} 0 obj\n'.encode()+o+b'\nendobj\n'
 xref=len(out);out+=f'xref\n0 {len(objs)+1}\n0000000000 65535 f \n'.encode()
 for o in offs[1:]:out+=f'{o:010d} 00000 n \n'.encode()
 out+=f'trailer << /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode();path.write_bytes(out)
def chart(name,vals,bars=False,xmax=None,ymax=None):
 xmax=xmax or max(x for x,y in vals) or 1;ymax=ymax or max(y for x,y in vals) or 1
 pts=[(int(60+x/xmax*620),int(H-50-y/ymax*370)) for x,y in vals]
 write_png(F/(name+'.png'),pts,bars);write_pdf(F/(name+'.pdf'),name,pts,bars)
x=[];c=[];o=[]
for j,im in enumerate(('hnswlib','faiss','vamana')):
 a=[r for r in fac if r['implementation']==im and r['endpoint_range']=='FEASIBLE_ONLY'];
 c0=sum(float(r['under_rate'])*int(r['queries']) for r in a if r['environment_range'].startswith('CLOSED'))/sum(int(r['queries']) for r in a if r['environment_range'].startswith('CLOSED'))
 o0=sum(float(r['under_rate'])*int(r['queries']) for r in a if r['environment_range'].startswith('OPEN'))/sum(int(r['queries']) for r in a if r['environment_range'].startswith('OPEN'))
 x.extend([(j*2,c0),(j*2+1,o0)])
chart('fast_feasible_closed_open_risk',x,True,xmax=6,ymax=.30)
chart('fast_sentinel_k_risk',[(int(r['sentinel_k']),float(r['under_rate'])) for r in sent],False,xmax=256,ymax=.26)
chart('fast_observable_response_distance',[(float(r['z0_metadata_distance']),float(r['budget_distance_complete_case'])) for r in dist],False,xmax=1,ymax=.14)
dec=list(csv.DictReader(open(R/'risk_decomposition.csv')));chart('fast_risk_decomposition',[(i,float(r['environment_contrast_feasible'])) for i,r in enumerate(dec)],True,xmax=6,ymax=.13)

brief='''# ICBA open-world Fast Decision\n\nStatus: **FAST DECISION, not final confirmatory seal**.\n\nFrozen-input reproduction passed. After excluding right-censored and no-safe-endpoint graphs, open-world under-budget risk remains above 0.05 for hnswlib, Faiss HNSW, and Vamana on SIFT and Arxiv. Removing the top 1% NDC-saving queries does not change that verdict.\n\nAt labeled-target sentinel k={32,64,128,256}, all six dataset-by-implementation risks remain above 0.05 and do not trend toward safety. The evidence therefore rejects finite sentinel variance as the dominant explanation. Endpoint infeasibility explains GloVe and part of the all-graph problem, but not feasible-only SIFT/Arxiv failure. Environment exclusion is the largest identified contrast. Source-Oracle dependence and target-label dependence are necessary limitations of the successful frozen lane, but their separate numerical contributions are not identifiable because no frozen deployable-policy or unlabeled-target counterfactual exists.\n\nAcross 648 frozen directed build pairs, the preregistered Z0-near/response-far rule yields 94 empirical collision candidates. Z0 metadata does not qualify for structured recovery. A common deployable Z1 runtime fingerprint is absent, so Z1 is NOT_ESTIMABLE rather than failed by imputation. Z2 is labeled target information and is not a deployable unlabeled channel.\n\nFast Decision label: **OPEN_WORLD_IMPOSSIBILITY_SUPPORTED_STRUCTURE_UNRESOLVED**. The next theory priority is the no-structure open-world safety-versus-conservatism lower bound, with support/OOD recovery retained only as a future conditional route. Do not begin algorithm design from this evidence.\n\nTheorem priority status: T-OW0 FORMAL_PROOF_COMPLETE; T-OW1 RESTRICTED_PROPOSITION/PROOF_SKETCH (two environments, finite grid); T-OW2 FORMAL_PROOF_COMPLETE by counterexample; T-OW3 PROOF_SKETCH; T-OW4 CONJECTURE; T-OW5 NOT_ESTIMABLE pending build-level power completion.\n'''
(D/'fast_decision_brief.md').write_text(brief)
paths=[D/'fast_decision_brief.md',D/'theorem_statements_fast.md',R/'fast_gate_table.csv',R/'literature_assumption_matrix_fast.csv']+[F/(x+y) for x in ('fast_feasible_closed_open_risk','fast_sentinel_k_risk','fast_observable_response_distance','fast_risk_decomposition') for y in ('.png','.pdf')]
manifest={'schema_version':'1.0','stage':'FAST_DECISION','confirmatory':False,'seed':991,'bootstrap_reps':1000,'sentinel_subsamples_per_build':300,'frozen_base':'77e0d430bc04b819276b570a96eedb339a66c043','decision':'OPEN_WORLD_IMPOSSIBILITY_SUPPORTED_STRUCTURE_UNRESOLVED','sealed_data_accessed':False,'artifacts':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(M/'icba_open_world_fast_decision.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
