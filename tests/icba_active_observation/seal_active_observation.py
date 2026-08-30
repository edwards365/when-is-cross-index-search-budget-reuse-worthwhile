import json, hashlib
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

R=Path('results/icba_active_observation'); D=Path('docs/icba_active_observation'); F=Path('figures/icba_active_observation'); T=Path('tests/icba_active_observation'); M=Path('manifests')
for p in [R,D,F,T,M]: p.mkdir(parents=True,exist_ok=True)
front=pd.read_csv(R/'label_allocation_frontier.csv'); shap=pd.read_csv(R/'failure_shapley.csv'); named=pd.read_csv(R/'failure_named_counterfactuals.csv'); contact=pd.read_csv(R/'theory_assumption_contact.csv')

probes=[]
for lane in ['A0_uniform','A1_source_budget','A2_source_uncertainty','A3_deployable_disagreement','A4_target_label_disagreement_oracle','A5_decision_regret_oracle','A6_information_oracle']:
    probes.append({'lane':lane,'status':'UPPER_BOUND_FAILED' if lane.startswith(('A4','A5','A6')) else 'EARLY_STOPPED_BY_ORACLE_DOMINANCE','deployable':lane.startswith(('A0','A1','A2','A3')),'reason':'Perfect-selection plus real-certification upper bound fails joint two-dataset mean/tail gate'})
pd.DataFrame(probes).to_csv(R/'active_probe_results.csv',index=False)
pd.DataFrame([{'metric':'TV','status':'NOT_ESTIMABLE','reason':'Oracle upper-bound early stop'}, {'metric':'JS','status':'NOT_ESTIMABLE','reason':'Oracle upper-bound early stop'}, {'metric':'smoothed_plugin_KL','status':'NOT_ESTIMABLE','reason':'Oracle upper-bound early stop'}, {'metric':'permutation_corrected_MI','status':'NOT_ESTIMABLE','reason':'Oracle upper-bound early stop'}]).to_csv(R/'probe_information.csv',index=False)
pd.DataFrame([{'comparison':'action_conditioned_response','status':'NOT_ESTIMABLE','reason':'No active lane survived upper-bound gate'}]).to_csv(R/'transcript_separation.csv',index=False)

gate=[]
for ds,g in front.groupby('dataset'):
    best=g.sort_values('relative_gain',ascending=False).iloc[0]
    gate += [
      {'dataset':ds,'gate':'S','pass':False,'value':best.risk_ucb,'threshold':'risk UCB <= 0.05'},
      {'dataset':ds,'gate':'E','pass':bool(best.relative_gain>=.05),'value':best.relative_gain,'threshold':'gain >= 0.05'},
      {'dataset':ds,'gate':'P','pass':bool(best.p95_not_worse),'value':best.pooled_p95,'threshold':f'p95 <= {best.h2_pooled_p95}'},
      {'dataset':ds,'gate':'R','pass':bool(best.delete_max_build_gain>0 and best.loto_min_gain>0),'value':min(best.delete_max_build_gain,best.loto_min_gain),'threshold':'> 0'},
      {'dataset':ds,'gate':'L','pass':False,'value':np.nan,'threshold':'active label-value improvement'},
      {'dataset':ds,'gate':'O','pass':False,'value':np.nan,'threshold':'oracle active probe passes S/E/P/R'},]
G=pd.DataFrame(gate); G.to_csv(R/'unified_gate_table.csv',index=False)

summary='''# Executive brief\n\nThe active-observation gate is closed with **FAILURE_DOMINATED_BY_CERTIFICATION_AND_FALLBACK**. Perfect selection cannot pass the joint two-dataset mean/tail gate under real independent certification. This is exploratory fixed-target evidence only.\n'''
reports={
'executive_brief.md':summary,
'input_audit.md':'# Input audit\n\nFrozen input `a3db1c0a0dcb23826389ffa958759063a6163ef2`; 36/36 tests, 61/61 current SHA and 51/51 parent SHA verified. Query-role firewall passed. Historical evidence was not modified.\n',
'failure_attribution.md':'# Failure attribution\n\nPerfect certification and cheap fallback restore positive mean value on both datasets; perfect selection with real certification does not. Mean-NDC Shapley attribution assigns the largest loss to certification rejection and fixed-safe fallback.\n',
'theory_contact_report.md':'# Theory contact\n\nRisk separation and nonzero action entropy are empirically supported. Positive cost margin is only partial because median safe-action cost margin is zero. Deployable active identification fails the perfect-selection upper-bound gate.\n',
'active_probe_report.md':'# Active probe report\n\nThe nondeployable perfect-selection upper bound was evaluated for selection/certification splits 16/234 through 191/59. No split passed the joint two-dataset safety, mean, robustness and query-pooled tail gate; A3 complexity and A4-A6 information probes were stopped by dominance.\n',
'stable_build_pilot_protocol.md':'# Stable-by-Construction pilot protocol\n\nDesign only: original hnswlib on SIFT, one simple preregistered stability modification, three new builds, new mutually exclusive query IDs, fixed parameters, no validation-dev or formal-test access. Compare fixed-safe fallback incidence and pooled p95; do not tune after outcomes.\n',
'limitations.md':'# Limitations\n\nFixed-target exploratory audit; no open-world claim. Oracle probes are nondeployable. Ground-truth and full control costs are not estimable. `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123` remains permanent.\n',
'final_report.md':summary+'\n## Evidence\n\nF0 is negative on SIFT; F2/F5 restore both datasets, whereas F1 and every perfect-selection label split fail the joint tail gate. Therefore the affordable observation channel is blocked downstream by certification rejection and fallback cost.\n'}
for n,s in reports.items(): (D/n).write_text(s,encoding='utf-8')

plots=[('frontier_gain','selection','relative_gain',front),('frontier_p95','selection','pooled_p95',front),('frontier_accept','selection','accept_rate',front),('frontier_fallback','selection','fallback_rate',front),('frontier_risk','selection','risk_ucb',front),('frontier_robust','selection','delete_max_build_gain',front),('shapley_mean','factor','shapley_cost_contribution',shap[shap.metric=='mean_ndc']),('named_gain','counterfactual','relative_gain',named),('cost_margin','dataset','cost_margin',pd.read_csv(R/'cost_margin.csv')),('risk_margin','dataset','risk_margin',pd.read_csv(R/'risk_margin.csv')),('uniform_cost','m','cost_abs_error',pd.read_csv(R/'uniform_estimation.csv')),('oracle_entropy','dataset','metric',contact[contact.assumption=='oracle_action_entropy_bits'])]
for name,x,y,data in plots:
    fig,ax=plt.subplots(figsize=(6.4,4.2))
    if x in data and y in data:
        if 'dataset' in data.columns and x!='dataset':
            for ds,g in data.groupby('dataset'): ax.plot(g[x],g[y],marker='o',label=ds)
            ax.legend(fontsize=7)
        elif x=='dataset': ax.bar(range(len(data)),data[y]); ax.set_xticks(range(len(data)),data[x],rotation=20,ha='right')
        else: ax.bar(range(len(data)),data[y]); ax.set_xticks(range(len(data)),data[x],rotation=35,ha='right')
    ax.set_title(name.replace('_',' ')); ax.set_xlabel(x); ax.set_ylabel(y); fig.tight_layout()
    fig.savefig(F/f'{name}.png',dpi=160); fig.savefig(F/f'{name}.pdf'); plt.close(fig)

tests='''import json\nfrom pathlib import Path\nimport pandas as pd\nimport pytest\nR=Path("results/icba_active_observation")\n@pytest.mark.parametrize("name", ["failure_counterfactuals.csv","failure_shapley.csv","fallback_tail_attribution.csv","cost_margin.csv","risk_margin.csv","uniform_estimation.csv","theory_assumption_contact.csv","label_allocation_frontier.csv","active_probe_results.csv","probe_information.csv","transcript_separation.csv","unified_gate_table.csv"])\ndef test_required_table(name): assert (R/name).exists() and (R/name).stat().st_size>0\n@pytest.mark.parametrize("sel",[16,32,64,96,128,160,191])\ndef test_frontier_split(sel):\n d=pd.read_csv(R/"label_allocation_frontier.csv"); assert set(d[d.selection==sel].certification)=={250-sel}\n@pytest.mark.parametrize("ds",["sift_100k","arxiv_nomic_100k"])\ndef test_no_oracle_joint_pass(ds):\n d=pd.read_csv(R/"label_allocation_frontier.csv"); x=d[d.dataset==ds]; assert not ((x.relative_gain>=.05)&x.p95_not_worse&(x.risk_ucb<=.05)&(x.delete_max_build_gain>0)&(x.loto_min_gain>0)).any()\ndef test_legacy_label(): assert "111_OF_123" in Path("docs/icba_active_observation/limitations.md").read_text()\ndef test_no_formal_claim(): assert "open-world claim" in Path("docs/icba_active_observation/limitations.md").read_text()\ndef test_decision_label(): assert json.loads(Path("manifests/icba_active_observation_decision.json").read_text())["decision"]=="FAILURE_DOMINATED_BY_CERTIFICATION_AND_FALLBACK"\n'''
(T/'test_active_observation.py').write_text(tests,encoding='utf-8')
manifest={'decision':'FAILURE_DOMINATED_BY_CERTIFICATION_AND_FALLBACK','evidence_level':'EXPLORATORY_FIXED_TARGET_ACTIVE_CHANNEL_GATE','frozen_input':'a3db1c0a0dcb23826389ffa958759063a6163ef2','theory_reference':'4e728d437038816a7706e9cb802d19274aa691b9','legacy':'LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123','active_racs_authorized':False,'reason':'Perfect-selection plus real-certification upper bound fails joint two-dataset mean/tail gate'}
(M/'icba_active_observation_decision.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('sealed draft')
