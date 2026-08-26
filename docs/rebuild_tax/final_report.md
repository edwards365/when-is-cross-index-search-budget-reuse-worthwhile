# Adaptive ANN Has a Rebuild Tax — final report

## Decision

The frozen decision is **KEEP_BOUNDARY_STUDY_CERTIFICATION_IS_COSTLY**. Gate M and Gate T pass, and independent validation shows that conformal rebuilding can certify budget sufficiency and Recall non-inferiority. It does not preserve enough Oracle efficiency to qualify as an adaptive ANN method.

## Mechanism evidence

The source comprises 45 graphs and 540,000 frozen query-ef records. Realistic-history strict PIB is 13.593% on Arxiv, 34.084% on GloVe, and 22.894% on SIFT; the bootstrap lower bounds remain positive and removing the top 1% contributions does not reverse direction. Rank reshaping persists beyond graph-level scaling. Frozen query geometry has weak out-of-fold explanatory power, graph-global features explain graph means but not query-by-history interaction, and trace attribution is unavailable.

## Independent confirmation

Validation membership was frozen before vector access. The confirmation contains 27 graphs and 648,000 rows over three datasets, three seeds, three realistic histories, 2,000 independent queries, and 12 ef values. All native/instrumented cells match, all graphs have checksums, and every temporary index was deleted.

All 14 finite-sample-feasible `(n, delta)` candidates satisfy the frozen Wilson coverage and aggregate Recall non-inferiority rules. None satisfies Oracle-headroom retention, p95 NDC, cross-history/seed efficiency direction, or net-benefit requirements. For example, `(n=32, delta=.05)` has under-budget rates 1.45%/3.58%/1.33% and Recall deltas +.01869/+.00493/+.01732 on Arxiv/GloVe/SIFT, but retention is -150.7%/+27.4%/-199.6%; online p95 NDC is 1879/10135/2723 versus fixed 807/7996/968. Including calibration, its mean relative cost at N=100,000 is +45.8%/-14.3%/+64.6%, and the cross-dataset mean remains +31.4% even at N=10,000,000. At `(n=1000, delta=.001)`, safety tightens further but retention is negative on all three datasets.

The result supports the boundary claim: query hardness is construction-history dependent and safe index-blind transfer has a measurable price; a global conformal multiplier can buy safety, but on this matrix certification over-allocation and sentinel cost consume the deployable gain. No second implementation, formal-test access, or adaptive algorithm extension is authorized.

## Reproducibility

Branch: `exp/rebuild_tax_cross_mechanism`. Frozen source: `4f49c02121b0321e5ed0b2d4a0846a22e1bad910`. Gate M: `c92d8b3`; Gate T: `80f3e57`; validation membership: `052395c`; validation raw matrix: `e1b3c29`; Gate C analyzer/fix: `86314dc`/`8347605`. Formal-test remained sealed throughout.
