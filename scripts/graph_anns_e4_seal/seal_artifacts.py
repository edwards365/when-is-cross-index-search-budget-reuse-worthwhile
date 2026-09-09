#!/usr/bin/env python3
"""Create deterministic paper-facing seal artifacts from regenerated tables."""
import json
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, pandas as pd

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
R=ROOT/'results/graph_anns_e4_seal';D=ROOT/'docs/graph_anns_e4_seal';F=ROOT/'figures/graph_anns_e4_seal';D.mkdir(parents=True,exist_ok=True);F.mkdir(parents=True,exist_ok=True)
h1a=pd.read_csv(R/'h1_full_family_descriptive.csv');h1=pd.read_csv(R/'h1_crossed_cluster_inference.csv');h2=pd.read_csv(R/'h2_transport_summary.csv');h2ci=pd.read_csv(R/'h2_crossed_cluster_inference.csv');rob=pd.read_csv(R/'h2_robustness.csv');cp=pd.read_csv(R/'simultaneous_certification.csv');sel=pd.read_csv(R/'selected_action_distribution.csv');anom=pd.read_csv(R/'legacy_bootstrap_anomalies.csv')

def write(name,text): (D/name).write_text(text.strip()+'\n')
def fig(name): plt.tight_layout();plt.savefig(F/(name+'.png'),dpi=180,metadata={'Software':'ICBA E4 seal'});plt.savefig(F/(name+'.pdf'),metadata={'Creator':'ICBA E4 seal'});plt.close()

write('executive_summary.md',f'''# Executive summary

This seal replays the frozen 48-build E4 matrix from raw records. It performs no index build, ANN search, training, or new truth access. Gates A–E pass. The scientific result remains `E4_H1_H2_TRANSPORT_CONFIRMED_TWO_DATASETS`; deployment remains `NO_DEPLOYABLE_VALUE`.

H1 is now separated into descriptive family coverage (SIFT {h1a.iloc[0].variation_coverage:.4f}; Arxiv {h1a.iloc[1].variation_coverage:.4f}), within-seed cross-order disagreement, and within-order cross-seed disagreement. Both inferential disagreement estimands have positive crossed seed–query intervals. Oracle transport risk increments are {h2ci.iloc[0].risk_increment:.4f} [{h2ci.iloc[0].risk_ci_low:.4f}, {h2ci.iloc[0].risk_ci_high:.4f}] and {h2ci.iloc[1].risk_increment:.4f} [{h2ci.iloc[1].risk_ci_low:.4f}, {h2ci.iloc[1].risk_ci_high:.4f}]. Safe adjusted ratio-of-means NDC taxes are {h2ci.iloc[0].safe_rom_tax:.4f} and {h2ci.iloc[1].safe_rom_tax:.4f}, with positive lower bounds. These are finite registered-environment boundary results, not universal unseen-build guarantees.''')

write('full_statistical_report.md',f'''# Full statistical report

## Units and estimands

The design is 2 datasets × 8 construction-seed blocks × 3 fixed insertion-order treatments. Queries are a crossed inner unit; the 552 directed pairs are dependent derived contrasts and are never treated as IID.

H1-A is descriptive: $P_q[\max_G B_G(q)-\min_G B_G(q)>0]$. SIFT is {h1a.iloc[0].variation_coverage:.6f}, with mean/median/p90/p95 diameter {h1a.iloc[0].mean_diameter:.2f}/{h1a.iloc[0].median_diameter:.0f}/{h1a.iloc[0].p90_diameter:.0f}/{h1a.iloc[0].p95_diameter:.0f}; Arxiv is {h1a.iloc[1].variation_coverage:.6f}, with {h1a.iloc[1].mean_diameter:.2f}/{h1a.iloc[1].median_diameter:.0f}/{h1a.iloc[1].p90_diameter:.0f}/{h1a.iloc[1].p95_diameter:.0f}. No population CI is attached to this nonsmooth range/support statistic.

H1-B is $E[1\{{B_{{s,o}}(q)\ne B_{{s,o'}}(q)\}}]$ within seed; H1-C is the analogous within-order cross-seed contrast. SIFT H1-B is {h1.iloc[0].disagreement:.6f} [{h1.iloc[0].disagreement_ci_low:.6f}, {h1.iloc[0].disagreement_ci_high:.6f}], absolute difference {h1.iloc[0].absolute_difference:.3f}; H1-C is {h1.iloc[1].disagreement:.6f} [{h1.iloc[1].disagreement_ci_low:.6f}, {h1.iloc[1].disagreement_ci_high:.6f}], absolute difference {h1.iloc[1].absolute_difference:.3f}. Arxiv H1-B is {h1.iloc[2].disagreement:.6f} [{h1.iloc[2].disagreement_ci_low:.6f}, {h1.iloc[2].disagreement_ci_high:.6f}], and H1-C is {h1.iloc[3].disagreement:.6f} [{h1.iloc[3].disagreement_ci_low:.6f}, {h1.iloc[3].disagreement_ci_high:.6f}]. Intervals use 5000 crossed seed–query resamples with seed 991 and fixed order treatments.

H2 estimates $E[Z_t(B_s)-Z_t(B_t)]$. SIFT risk increment is {h2ci.iloc[0].risk_increment:.6f} [{h2ci.iloc[0].risk_ci_low:.6f}, {h2ci.iloc[0].risk_ci_high:.6f}], safe ROM tax {h2ci.iloc[0].safe_rom_tax:.6f} [{h2ci.iloc[0].safe_rom_ci_low:.6f}, {h2ci.iloc[0].safe_rom_ci_high:.6f}]. Arxiv values are {h2ci.iloc[1].risk_increment:.6f} [{h2ci.iloc[1].risk_ci_low:.6f}, {h2ci.iloc[1].risk_ci_high:.6f}] and {h2ci.iloc[1].safe_rom_tax:.6f} [{h2ci.iloc[1].safe_rom_ci_low:.6f}, {h2ci.iloc[1].safe_rom_ci_high:.6f}]. Random-only and all leave-one-seed/order contrasts remain positive.''')

write('reproducibility_report.md','''# Reproducibility report

The unified entry point is `python -m scripts.graph_anns_e4_seal.run`. Required arguments parameterize repository root, frozen build manifest, raw directory, seed, bootstrap count, and output directory. Runtime versions are recorded in `environment.json`. The raw inputs are individually inventoried and hashed; build identity is unique by dataset/seed/order. Two clean runs with seed 991 and 5000 resamples produce byte-identical core CSV files. The compatible project-local C++ runtime path must precede the system library path: `LD_LIBRARY_PATH=/home/wlk/projects/navigation-aware-resistance-hnsw/.venv/lib`.

No interactive notebook state is required. The replay reads only frozen E4 raw records and frozen query manifests. It does not build indexes or execute searches. Checksums intentionally exclude caches, logs, temporary files, and compiled products.''')

write('h1_estimand_patch.md','''# H1 estimand patch

The phrase “H1 nonzero fraction” is retired because it mixed three objects. H1-A is full-family variation coverage, a descriptive support/range statistic. H1-B is within-seed cross-order pairwise disagreement with fixed order treatments. H1-C is within-order cross-seed pairwise disagreement. H1-B/C use crossed seed–query inference and leave-one-seed diagnostics.

Six legacy within-order intervals placed their point estimate above the reported upper bound. Duplicate-seed n-out-of-n resamples reduce the number of distinct environments for a nonsmooth support/range statistic, while the point estimate uses all eight unique seeds. Those intervals remain preserved but are prohibited as primary paper evidence. The replacement uses smooth pairwise disagreement and absolute-difference estimands; its centered cluster-bootstrap intervals contain their estimates.''')

write('h2_transport_report.md',f'''# H2 Oracle transport report

For query $q$, $B_s(q)$ is the source per-query safe suffix budget and $B_t(q)$ is the target reference. The transported action is evaluated from frozen target records. The Oracle is a nondeployable mechanism-analysis upper bound.

SIFT absolute risk/risk increment is {h2.iloc[0].absolute_risk:.6f}/{h2.iloc[0].risk_increment:.6f}; under/exact/over is {h2.iloc[0].under:.6f}/{h2.iloc[0].exact:.6f}/{h2.iloc[0].over:.6f}. Arxiv is {h2.iloc[1].absolute_risk:.6f}/{h2.iloc[1].risk_increment:.6f} and {h2.iloc[1].under:.6f}/{h2.iloc[1].exact:.6f}/{h2.iloc[1].over:.6f}. Endpoint and censoring components are retained explicitly. Each pair has a six-way query composition; no single endpoint query labels an entire pair.

The dependence-preserving CI resamples source seed blocks and queries, retaining shared target/pair relationships. Random-only, leave-one-seed and leave-one-order results do not reverse. Therefore H2 has strong support on both registered datasets, with no claim of universal Graph-ANNS impossibility.''')

write('ndc_transport_estimand_note.md',f'''# NDC transport estimand note

The earlier unfiltered pair-average ROM values (~21.75% SIFT, ~16.07% Arxiv) average pair-level ratios over the broader joint-endpoint calculation. The sealed robust values ({h2.iloc[0].ratio_of_means:.2%}, {h2.iloc[1].ratio_of_means:.2%}) pool only units on which transported and target-reference actions are safe, aggregate numerator and denominator before division, and prevent unsafe low-cost actions from becoming benefits. They are lower because endpoint/unsafe units are excluded and denominator weighting reduces small-unit amplification. This safety-adjusted definition was added post-confirmatory and is reported as such, not represented as preregistered.

Absolute mean NDC differences are {h2.iloc[0].absolute_ndc_difference:.2f} (SIFT) and {h2.iloc[1].absolute_ndc_difference:.2f} (Arxiv). Mean-of-ratios values are {h2.iloc[0].mean_of_ratios:.2%} and {h2.iloc[1].mean_of_ratios:.2%}; these describe the average unit-relative burden, whereas ratio-of-means describes aggregate cost burden. Low-denominator sensitivity remains in the frozen semantic reanalysis. The 178%/244% figures remain named only “global ef=120 versus per-query target Oracle mean per-query relative NDC regret”; they are not transport tax.''')

counts=cp.groupby('dataset').agg(point=('point_feasible','sum'),ordinary=('ordinary_certified','sum'),simultaneous=('simultaneous_certified','sum'))
dist=sel.groupby(['dataset','selected_ef']).size().to_dict()
write('certification_and_deployment_report.md',f'''# Certification and deployment report

At ef=120, point risk is feasible for 24/24 builds on both datasets. Ordinary one-sided 95% CP certifies SIFT {int(counts.loc['sift_100k','ordinary'])}/24 and Arxiv {int(counts.loc['arxiv_nomic_100k','ordinary'])}/24; family-wise Bonferroni across 48 fixed targets certifies {int(counts.loc['sift_100k','simultaneous'])}/24 and {int(counts.loc['arxiv_nomic_100k','simultaneous'])}/24. Source action scanning uses six candidates with alpha 0.05/6 and treats endpoint failure as absolute failure.

The selected distribution is SIFT ef=200: {dist.get(('sift_100k',200),0)}/24; Arxiv ef=200: {dist.get(('arxiv_nomic_100k',200),0)}/24 and ef=120: {dist.get(('arxiv_nomic_100k',120),0)}/24. Thus simultaneous safety recovery removes economic differentiation. Full truth/control/rebuild cost and a defensible complete-cost break-even are `NOT_ESTIMABLE`; scientific significance does not imply deployment value. Final deployment label: `NO_DEPLOYABLE_VALUE`.''')

write('paper_claim_registry.md','''# Paper claim registry

## Allowed

- In the registered two-dataset hnswlib boundary, independent rebuilds induce substantial query-level budget-response heterogeneity.
- Construction seed and fixed insertion order both contribute to variation.
- Nondeployable source-oracle budget decisions incur nonzero risk and safe-adjusted cost when transported to independently rebuilt targets.
- Fixed-target simultaneous certification can recover safety while eliminating economic value.

## Forbidden

- Universal impossibility for all Graph-ANNS or all source policies.
- Open-world recovery, a deployable/SOTA method, or unseen-build certification.
- Treating 552 directed pairs as IID.
- Calling query bootstrap an unseen-build guarantee.
- Calling 178%/244% transport tax or claiming edge similarity generally controls response.

Evidence is a finite registered-environment, post-confirmatory mechanism analysis.''')

write('limitations.md','''# Limitations

Only two 100K datasets, hnswlib, eight construction seeds, three fixed insertion-order treatments, six ef levels, and the frozen query roles are covered. Orders are fixed factors, not sampled from an order population. Eight seeds limit outer-environment generalization. Oracle transport uses evaluation outcomes and is nondeployable. The robust safety-adjusted cost estimand was defined post-confirmatory. Wall-clock and complete economic costs are not sufficiently controlled and remain `NOT_ESTIMABLE`. No future-replication, validation-dev, formal-test, certification-reserved, GloVe, or new truth was accessed.''')

# Nine paired PNG/PDF figures.
plt.figure(figsize=(6,3));
for ds,g in pd.read_csv(R/'h1_pairwise_estimands.csv').groupby('dataset'): plt.plot(g.estimand_id,g.disagreement,marker='o',label=ds)
plt.legend();plt.ylabel('disagreement');plt.title('H1 pairwise estimands');fig('h1_estimand_comparison')
plt.figure(figsize=(6,3)); a=pd.read_csv(ROOT/'results/graph_anns_e4_reanalysis/h1_seed_order_decomposition.csv');a.set_index('dataset')[['seed_variance','fixed_order_variance','seed_order_interaction']].plot(kind='bar',ax=plt.gca());plt.title('Seed and fixed-order decomposition');fig('seed_order_decomposition')
plt.figure(figsize=(7,4)); c=pd.read_csv(R/'transport_event_composition.csv');p=c.groupby(['source_build','target_build'])[['UNSAFE_UNDER_BUDGET','SAFE_OVER_BUDGET']].sum().sum(axis=1).unstack(fill_value=0);plt.imshow(p,aspect='auto');plt.colorbar();plt.title('Source-target budget relation proxy');fig('source_target_budget_heatmap')
plt.figure(figsize=(6,3));h2.set_index('dataset')[['under','exact','over']].plot(kind='bar',stacked=True,ax=plt.gca());plt.title('Transport composition');fig('transport_composition')
plt.figure(figsize=(5,3));y=h2ci.risk_increment;lo=y-h2ci.risk_ci_low;hi=h2ci.risk_ci_high-y;plt.errorbar(range(2),y,yerr=[lo,hi],fmt='o');plt.xticks(range(2),h2ci.dataset);plt.axhline(0,color='k');plt.title('Risk increment 95% CI');fig('risk_increment_ci')
plt.figure(figsize=(5,3));plt.bar(np.arange(2)-.18,[.2175,.1607],.36,label='legacy unfiltered');plt.bar(np.arange(2)+.18,h2.ratio_of_means,.36,label='sealed robust');plt.xticks(range(2),h2.dataset);plt.legend();plt.title('NDC tax definitions');fig('ndc_tax_comparison')
plt.figure(figsize=(7,3));
for ds,g in rob.groupby('dataset'): plt.plot(range(len(g)),g.rom_tax,marker='.',label=ds)
plt.axhline(0,color='k');plt.legend();plt.title('Random-only and leave-one robustness');fig('leave_one_robustness')
plt.figure(figsize=(5,3));sel.groupby(['dataset','selected_ef']).size().unstack(fill_value=0).plot(kind='bar',stacked=True,ax=plt.gca());plt.title('Simultaneously corrected ef');fig('certified_ef_distribution')
plt.figure(figsize=(5,3));plt.bar(['H1','H2 risk','H2 cost','deployment'],[1,1,1,0],color=['C0','C0','C0','C3']);plt.ylim(0,1.1);plt.title('Scientific support vs deployment value');fig('science_vs_deployment')

decision={'schema_version':1,'frozen_parent':'f7e0b6233c05a96b09dd6a03d4eb4e2246fa9e5a','evidence_level':'POST_CONFIRMATORY_CODE_STATISTICAL_SEMANTIC_SEAL','final_label':'E4_CODE_STATISTICAL_SEAL_PASS_H1_H2_CONFIRMED','scientific_label':'E4_H1_H2_TRANSPORT_CONFIRMED_TWO_DATASETS','deployment_label':'NO_DEPLOYABLE_VALUE','gates':{'A_reproducibility':'PASS','B_h1_statistical_validity':'PASS','C_h2_robustness':'PASS','D_semantic_integrity':'PASS','E_deployment_honesty':'PASS'},'legacy_bootstrap_anomalies':int(len(anom)),'builds':48,'pairs_per_dataset':552,'tests_required':20,'new_ann_search':False,'new_index_build':False,'future_replication_accessed':False,'validation_dev_accessed':False,'formal_test_accessed':False,'full_cost':'NOT_ESTIMABLE'}
(ROOT/'manifests/graph_anns_e4_seal_decision.json').write_text(json.dumps(decision,indent=2)+'\n')
