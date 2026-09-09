#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
R=ROOT/'results/graph_anns_e4_patch'; D=ROOT/'docs/graph_anns_e4_patch'; D.mkdir(parents=True,exist_ok=True)
h1=pd.read_csv(R/'h1_censoring_aware_estimands.csv'); h2=pd.read_csv(R/'h2_registered_family_query_ci.csv'); rob=pd.read_csv(R/'h2_two_endpoint_robustness.csv'); comp=pd.read_csv(R/'transport_event_composition_corrected.csv'); cert=pd.read_csv(R/'certification_multiplicity_audit.csv')
def w(n,s): (D/n).write_text(s.strip()+'\n')
def s(ds,e): return h1[(h1.dataset==ds)&(h1.estimand_id==e)&(h1.scope=='summary')].iloc[0]
def r(ds): return h2[h2.dataset==ds].iloc[0]
w('executive_summary.md',f'''# E4.1 executive summary

The parent E4 code/statistical seal was replayed from frozen raw records and its core CSVs were byte-identical. This patch performs no index build, ANN search, training, or new truth access. `⊥` is retained as a categorical right-censored state, H1/H2 inference is conditional on the registered 48-build family, and certification multiplicity is separated.

Final decision: `E4_TRANSPORT_CONFIRMED_NO_CERTIFIED_ACTION`. Scientific label: `E4_H1_H2_TRANSPORT_CONFIRMED_REGISTERED_HNSWLIB_FAMILY`. Deployment label: `NO_DEPLOYABLE_VALUE`.''')
w('inference_scope_note.md','''# Inference scope

Primary confidence intervals are registered-build-family query-distribution intervals: 5000 resamples of 750 evaluation query IDs with all 552 directed source→target pairs retained for every sampled query. Pair rows are dependent and are never IID-resampled. This is conditional finite-environment inference, not an unseen-build or open-world certificate. Leave-one-seed, leave-one-order, random-only, source-only and target-only deletion are sensitivity analyses.''')
w('censoring_semantic_patch.md',f'''# Censoring semantic patch

Finite budgets are 10,20,40,80,120,200; no infeasible budget is encoded as 240. H1-A1 categorical coverage is SIFT {s('sift_100k','H1-A1').categorical_disagreement:.6f} and Arxiv {s('arxiv_nomic_100k','H1-A1').categorical_disagreement:.6f}. H1-A2 all-build-feasible numeric diameter uses {int(s('sift_100k','H1-A2').effective_query_count)} SIFT and {int(s('arxiv_nomic_100k','H1-A2').effective_query_count)} Arxiv queries, with means {s('sift_100k','H1-A2').feasible_absolute_difference:.3f} and {s('arxiv_nomic_100k','H1-A2').feasible_absolute_difference:.3f}. H1-A3 feasible-subset means are {s('sift_100k','H1-A3').feasible_absolute_difference:.3f} and {s('arxiv_nomic_100k','H1-A3').feasible_absolute_difference:.3f}. Endpoint-state mismatch is {s('sift_100k','H1-A4').categorical_disagreement:.6f} and {s('arxiv_nomic_100k','H1-A4').categorical_disagreement:.6f}.''')
w('h1_h2_logical_crosswalk.md','''# H1/H2 logical crosswalk

H1 is the rebuild-response phenomenon; H2 quantifies its transport consequence and is not an independent phenomenon. On the finite suffix-safe grid, Bs(q)<Bt(q) creates an under-budget possibility and Bs(q)>Bt(q) an over-budget conservative possibility. Raw Recall nonmonotonicity is retained, so suffix-safe under-budget and observed-safe nonmonotone cases are distinct. No open-world theorem is claimed.''')
w('certification_scope_patch.md','''# Certification scope patch

Per-target action selection uses alpha=0.05/6. Fixed ef=120 across the 48 registered targets uses alpha=0.05/48. The all-target/all-action family uses alpha=0.05/(48×6). The selected action distribution remains SIFT 24/24 ef=200 and Arxiv 23/24 ef=200 plus 1/24 ef=120. Some ef=200 fallback sentinel certificates fail, so no universally certified fallback exists; the correct status is `ABSTAIN_NO_CERTIFIED_ACTION`, preserving deployment label `NO_DEPLOYABLE_VALUE`.''')
w('full_patch_report.md',f'''# Full E4.1 patch report

Parent `c976b48be6e0d78e7a0ed27afaf1f5448d44a567` replayed byte-identically. H1-A1: SIFT {s('sift_100k','H1-A1').categorical_disagreement:.6f}, Arxiv {s('arxiv_nomic_100k','H1-A1').categorical_disagreement:.6f}. H1-A2 means: SIFT {s('sift_100k','H1-A2').feasible_absolute_difference:.3f} on {int(s('sift_100k','H1-A2').effective_query_count)} queries; Arxiv {s('arxiv_nomic_100k','H1-A2').feasible_absolute_difference:.3f} on {int(s('arxiv_nomic_100k','H1-A2').effective_query_count)}. H2 query-primary CI: SIFT risk increment {r('sift_100k').risk_increment:.6f} [{r('sift_100k').risk_ci_low:.6f},{r('sift_100k').risk_ci_high:.6f}], safe ROM {r('sift_100k').safe_rom_tax:.6f} [{r('sift_100k').safe_rom_ci_low:.6f},{r('sift_100k').safe_rom_ci_high:.6f}]; Arxiv risk increment {r('arxiv_nomic_100k').risk_increment:.6f} [{r('arxiv_nomic_100k').risk_ci_low:.6f},{r('arxiv_nomic_100k').risk_ci_high:.6f}], safe ROM {r('arxiv_nomic_100k').safe_rom_tax:.6f} [{r('arxiv_nomic_100k').safe_rom_ci_low:.6f},{r('arxiv_nomic_100k').safe_rom_ci_high:.6f}]. The event composition is mutually exclusive and complete per pair. Endpoint and grid right-censoring remain not separately identifiable. Random-only and two-sided deletion remain positive. Full economic cost remains NOT_ESTIMABLE.''')
w('paper_claim_patch.md','''# Paper claim patch

Allowed: registered hnswlib rebuilds induce categorical and pairwise budget heterogeneity; seed/order contribute; frozen source-oracle transport creates positive finite-family risk and safe-adjusted cost; simultaneous certification can remove economic value. Forbidden: unseen-build guarantees, universal Graph-ANNS impossibility, all source policies failing, deployable method success, IID treatment of 552 pairs, or treating 178%/244% as transport tax.''')
manifest={'schema_version':1,'parent':'c976b48be6e0d78e7a0ed27afaf1f5448d44a567','final_label':'E4_TRANSPORT_CONFIRMED_NO_CERTIFIED_ACTION','scientific_label':'E4_H1_H2_TRANSPORT_CONFIRMED_REGISTERED_HNSWLIB_FAMILY','deployment_label':'NO_DEPLOYABLE_VALUE','evidence_level':'POST_CONFIRMATORY_INFERENCE_AND_CENSORING_SEMANTIC_PATCH','parent_replay':'BYTE_IDENTICAL','builds':48,'pairs_per_dataset':552,'queries_per_pair':750,'seed':991,'bootstrap':5000,'budget_grid':[10,20,40,80,120,200],'endpoint_semantics':'ENDPOINT_AND_RIGHT_CENSORING_NOT_SEPARATELY_IDENTIFIABLE','fallback_status':'ABSTAIN_NO_CERTIFIED_ACTION','future_replication_accessed':False,'validation_dev_accessed':False,'formal_test_accessed':False,'new_ann_search':False,'new_index_build':False}
(ROOT/'manifests/graph_anns_e4_patch_decision.json').write_text(json.dumps(manifest,indent=2)+'\n')
