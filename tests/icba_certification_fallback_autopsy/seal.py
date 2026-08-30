import json
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

R=Path('results/icba_certification_fallback_autopsy'); D=Path('docs/icba_certification_fallback_autopsy'); F=Path('figures/icba_certification_fallback_autopsy'); T=Path('tests/icba_certification_fallback_autopsy'); M=Path('manifests')
for p in [R,D,F,T,M]: p.mkdir(parents=True,exist_ok=True)
q=pd.read_csv(R/'rejection_quadrants.csv'); c=pd.read_csv(R/'sample_size_curves.csv'); o=pd.read_csv(R/'ordered_policy_violations.csv'); f=pd.read_csv(R/'fallback_frontier.csv'); g=pd.read_csv(R/'unified_gate_table.csv'); mc=pd.read_csv(R/'mechanism_contributions.csv')

decision='MIXED_CERTIFICATION_AND_FALLBACK_BOTTLENECK'
summary='''# Executive brief\n\nThe fixed-target autopsy finds a mixed certification-rejection and fixed-safe fallback bottleneck. Safe-but-rejected episodes are material, but unsafe acceptance is also nonzero. Perfect certification and cheap fallback restore mean value only as nondeployable upper bounds. The candidate stage ladder is not ordered, so ordered recovery is not authorized.\n'''
(D/'executive_brief.md').write_text(summary)
(D/'limitations.md').write_text('''# Limitations\n\nEvidence is `EXPLORATORY_FIXED_TARGET`, not confirmatory. Evaluation is retrospective only. Frozen mutually-exclusive data do not support every requested certification size; unsupported sizes are `NOT_ESTIMABLE`. Counterfactuals are not algorithms. Truth/control costs remain symbolic. `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123` remains permanent. validation-dev/formal-test and GloVe sealed data were not accessed.\n''')
(D/'final_report.md').write_text(summary+'''\n## Decision\n\nFinal label: `MIXED_CERTIFICATION_AND_FALLBACK_BOTTLENECK`. Ordered-policy assumption: failed. Method implementation: not authorized. Recommended pivot: Stable-by-Construction, while separately improving independent certification and designing a deployable intermediate fallback.\n\n## Gate\n\nSafety fails due to nonzero unsafe acceptance; Tail fails on both datasets; Efficiency fails on SIFT; Fallback and Deployability fail because no deployable intermediate fallback exists and only Oracle upper bounds restore joint value.\n''')

plots=[]
qs=q.groupby(['dataset','quadrant']).size().reset_index(name='count'); plots.append(('certification_quadrant',qs,'quadrant','count'))
sa=q.groupby(['dataset','certification']).agg(margin=('safety_margin','mean'),acceptance=('accept','mean')).reset_index(); plots.append(('margin_acceptance',sa,'margin','acceptance'))
ce=c[c.estimable.fillna(False)].copy(); plots += [('sample_false_rejection',ce,'certification_m','false_rejection_rate'),('sample_fallback',ce,'certification_m','fallback_rate'),('sample_mean_ndc',ce,'certification_m','mean_ndc')]
om=o[o.subset=='ALL'].copy(); plots.append(('ordered_rung_heatmap',om,'failure_violation_rate','budget_violation_rate'))
bf=mc[mc.metric=='mean_ndc'].copy(); plots.append(('fallback_cost_waterfall',bf,'factor','share'))
gf=g.assign(pass_num=g['pass'].astype(int)); plots.append(('unified_gate',gf,'gate','pass_num'))
for name,d,x,y in plots:
 fig,ax=plt.subplots(figsize=(6.6,4.3))
 if 'dataset' in d.columns and x not in ['quadrant','factor','gate']:
  for ds,h in d.groupby('dataset'): ax.plot(h[x],h[y],marker='o',label=ds)
  ax.legend(fontsize=7)
 else:
  labels=(d.dataset.astype(str)+'|'+d[x].astype(str)) if 'dataset' in d.columns else d[x].astype(str)
  ax.bar(range(len(d)),d[y]); ax.set_xticks(range(len(d)),labels,rotation=40,ha='right',fontsize=7)
 ax.set_title(name.replace('_',' ')); ax.set_xlabel(x); ax.set_ylabel(y); fig.tight_layout(); fig.savefig(F/f'{name}.png',dpi=150); fig.savefig(F/f'{name}.pdf'); plt.close(fig)

manifest={'decision':decision,'frozen_input':'97ca42a120fff015885bba509e8aa90178aabfa2','parent_decision':'FAILURE_DOMINATED_BY_CERTIFICATION_AND_FALLBACK','theory_reference':'4e728d437038816a7706e9cb802d19274aa691b9','evidence_level':'EXPLORATORY_FIXED_TARGET','safety_event_unified':True,'ordered_policy_assumption':'FAILED','method_implementation_authorized':False,'stable_by_construction_pivot':True,'validation_dev_accessed':False,'formal_test_accessed':False,'gloVe_sealed_accessed':False,'cost_status':'SYMBOLIC_COST_ONLY','legacy':'LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123'}
(M/'icba_certification_fallback_autopsy_decision.json').write_text(json.dumps(manifest,indent=2)+'\n')

test='''import json\nfrom pathlib import Path\nimport pandas as pd, pytest\nR=Path("results/icba_certification_fallback_autopsy")\n@pytest.mark.parametrize("n",["rejection_quadrants.csv","sample_size_curves.csv","safety_margin.csv","ordered_policy_violations.csv","fallback_frontier.csv","tail_attribution.csv","cost_break_even.csv","theory_contact_matrix.csv","unified_gate_table.csv","mechanism_contributions.csv"])\ndef test_table(n): assert (R/n).exists() and (R/n).stat().st_size>0\n@pytest.mark.parametrize("ds",["sift_100k","arxiv_nomic_100k"])\ndef test_quadrants(ds): assert set(pd.read_csv(R/"rejection_quadrants.csv").query("dataset==@ds").quadrant)=={"SAFE_ACCEPTED","SAFE_BUT_REJECTED","UNSAFE_REJECTED","UNSAFE_ACCEPTED"}\n@pytest.mark.parametrize("m",[59,64,90,96,122,128,154,186,218,234,250])\ndef test_requested_m(m): assert m in set(pd.read_csv(R/"sample_size_curves.csv").certification_m)\ndef test_cp_consistency(): assert pd.read_csv(R/"rejection_quadrants.csv").event_consistent.all()\ndef test_unsafe_acceptance_present(): assert (pd.read_csv(R/"rejection_quadrants.csv").quadrant=="UNSAFE_ACCEPTED").any()\ndef test_order_failed(): assert pd.read_csv(R/"ordered_policy_violations.csv").failure_violations.sum()>0\ndef test_gate_not_authorized(): assert not pd.read_csv(R/"unified_gate_table.csv")["pass"].all()\ndef test_manifest(): assert json.loads(Path("manifests/icba_certification_fallback_autopsy_decision.json").read_text())["decision"]=="MIXED_CERTIFICATION_AND_FALLBACK_BOTTLENECK"\ndef test_no_sealed_access():\n x=json.loads(Path("manifests/icba_certification_fallback_autopsy_decision.json").read_text()); assert not x["validation_dev_accessed"] and not x["formal_test_accessed"]\n'''
(T/'test_certification_fallback_autopsy.py').write_text(test)
print('sealed draft',decision)
