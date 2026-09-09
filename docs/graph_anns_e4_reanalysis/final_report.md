# E4 Semantic and Factorial Reanalysis — Final Report

Evidence level: `POST_CONFIRMATORY_SEMANTIC_AND_FACTORIAL_REANALYSIS`  
Scientific label: `E4_H1_H2_TRANSPORT_CONFIRMED_TWO_DATASETS`  
Deployment label: `NO_DEPLOYABLE_VALUE`

This is a read-only, post-confirmatory reanalysis of the frozen E4 matrix at `c676cdd577b1542dcffa9771887d4a768025c009`. It is not a new preregistered primary test and did not build an index, run ANN search, select queries, or access new truth.

## Required 40-item closure

1. **Original E4 zero modification:** Yes. The diff against the frozen commit is empty for every original E4 result, manifest, raw record, and index path; all additions are in the dedicated reanalysis paths.
2. **Query-role mapping:** Valid. Raw `query_id` is the local 0–999 row number and was mapped to the frozen dataset query IDs; 0–249 are sentinel and 250–999 evaluation, with zero overlap.
3. **Artifact completeness:** All 48 distinct build artifacts are readable: 24 SIFT and 24 Arxiv-Nomic.
4. **Factorial design:** Confirmed as two datasets, each with 8 construction seeds crossed with 3 fixed insertion regimes (`random`, `lid_ascending`, `lid_descending`). These are distinct artifacts, not 24 IID insertion-order draws.
5. **Random order semantics:** The random insertion order is a fixed experimental treatment shared across the eight construction seeds; order is a fixed factor and seed is the resampling block.
6. **H1, random only:** Positive on both datasets: nonzero safe-budget-change fraction is 0.3560 on SIFT and 0.3373 on Arxiv.
7. **H1 within all orders:** Positive in every regime. SIFT random/ascending/descending = 0.3560/0.3747/0.3947; Arxiv = 0.3373/0.3733/0.3347. The effect is therefore not an LID-only artifact.
8. **Seed-block bootstrap:** Keeping all three orders together, H1 is 0.76867 [0.76300, 0.77383] for SIFT and 0.62333 [0.61833, 0.62867] for Arxiv. H2 ratio-of-means tax is 0.21749 [0.21568, 0.21924] and 0.16075 [0.15914, 0.16238], respectively. Intervals are 95%, 5000 resamples, seed 991.
9. **Crossed seed–query bootstrap:** H1 is 0.76839 [0.74183, 0.79600] for SIFT and 0.62325 [0.59217, 0.65517] for Arxiv; H2 ratio-of-means tax is 0.21502 [0.20055, 0.22990] and 0.16495 [0.14881, 0.18174]. Both seed blocks and evaluation queries were resampled; fixed orders were retained.
10. **Leave-one-seed:** No sign reversal. Across eight deletions, SIFT H2 ratio-of-means remains 0.21734–0.21948 and Arxiv remains 0.16036–0.16211; all risk increments remain positive.
11. **Leave-one-order:** No sign reversal. SIFT H2 tax after dropping random/ascending/descending is 0.18991/0.17182/0.15805; Arxiv is 0.14904/0.11998/0.12359, all positive.
12. **Directed-pair completeness:** Complete: 24×23 = 552 non-diagonal directed source→target pairs per dataset, each evaluated on the same 750 evaluation queries. The 24 diagonal references are kept separate.
13. **Source-oracle transported risk:** Mean absolute target risk is 0.22373 for SIFT and 0.18376 for Arxiv. This is `NON_DEPLOYABLE_ORACLE_TRANSPORT_MECHANISM_ANALYSIS`.
14. **Risk increment:** Relative to the target diagonal reference, mean increment is 0.21573 for SIFT and 0.17121 for Arxiv.
15. **Budget relation:** Under/over/exact proportions are 0.21875/0.21875/0.56251 for SIFT and 0.17450/0.17450/0.65100 for Arxiv.
16. **Absolute NDC transport cost:** Risk-prioritized robust main estimate is +128.46 NDC for SIFT and +90.79 for Arxiv. Unsafe low-cost actions are never counted as benefits.
17. **Ratio-of-means NDC tax:** 19.45% for SIFT and 14.88% for Arxiv in the robust main summary.
18. **Mean-of-ratios NDC regret:** 23.87% for SIFT and 17.06% for Arxiv; it is reported separately and is not substituted for the ratio of means.
19. **Median relative regret:** 0 on both datasets; the distribution is heavy-tailed (p95 1.3056 on SIFT and 1.0092 on Arxiv).
20. **Low-denominator sensitivity:** After removing denominators below p5, ratio-of-means is 0.19522/0.15009; after removing the lowest-oracle-cost 1%, it is 0.19475/0.14906 (SIFT/Arxiv). The transport result is not explained by tiny denominators.
21. **Source-calibrated policy:** Under Bonferroni one-sided CP across six ef candidates, all 24 SIFT sources abstain/fallback to ef=200; Arxiv selects ef=200 for 23/24 sources and ef=120 for 1/24.
22. **Target calibration:** The same corrected rule yields ef=200 for all 24 SIFT targets; Arxiv yields ef=200 for 23/24 and ef=120 for 1/24.
23. **Source transfer vs target recalibration:** SIFT has no certified source action below fallback, so a meaningful economic transfer delta is unavailable. Arxiv has only one lower action and otherwise matches fallback; no stable, economically useful advantage over target recalibration is identified.
24. **Original vs corrected B4:** Uncorrected B4 mean selected ef was 173.33 on SIFT and 163.33 on Arxiv; simultaneous correction raises these to 200.00 and 196.67. Original B4 is preserved and explicitly relabeled; it is not overwritten.
25. **B2 point-risk audit:** At ef=120, point risk is below 5% for 24/24 builds on each dataset.
26. **Per-target certificate:** Ordinary one-sided 95% CP certifies 15/24 SIFT targets and 12/24 Arxiv targets.
27. **Simultaneous certificate:** Family-wise Bonferroni control certifies only 8/24 targets on each dataset.
28. **Meta vs target safety:** They are not equivalent. Meta-average risks are 0.03239 (SIFT) and 0.03322 (Arxiv), but these averages do not certify every fixed target.
29. **Original 178%/244% statement:** Retained only after renaming it “mean per-query relative NDC regret of global ef=120 versus the per-query oracle.” It is withdrawn as a statement of source→target transport tax.
30. **H1 Gate:** `STRONG_PASS` on both datasets.
31. **H2 Gate:** `STRONG_PASS` on both datasets: positive risk and safe-cost transport barriers survive random-only, crossed bootstrap, leave-one-seed, leave-one-order, and contribution-removal checks.
32. **H3 Gate:** SIFT `NO_CERTIFIED_SOURCE_ACTION`; Arxiv `SAFE_BUT_ECONOMICALLY_DOMINATED`; aggregate deployment label `NO_DEPLOYABLE_VALUE`.
33. **E4 label revision:** Replace the overly broad original wording with `E4_H1_H2_TRANSPORT_CONFIRMED_TWO_DATASETS`, accompanied independently by `NO_DEPLOYABLE_VALUE`.
34. **Strongest permitted paper claim:** Under the frozen 8×3 fixed-factor E4 design, rebuilds change per-query safe-budget responses, and transferring source-oracle budgets to distinct target rebuilds creates a robust risk and/or conservative-compute barrier on both SIFT-100K and Arxiv-Nomic-100K.
35. **Forbidden claims:** Do not claim 48 IID insertion-order samples, a deployable oracle, universal HNSW behavior, independent confirmation outside these frozen targets, per-target safety from meta-average risk, or a demonstrated economically valuable source-transfer policy.
36. **Need to rerun E4:** No. The frozen six-ef records are sufficient for this semantic correction and transport analysis; no new build or ANN matrix is warranted for closure.
37. **Future replication:** Not accessed and not authorized by this reanalysis. It remains sealed for a separately preregistered decision, if any.
38. **Validation-dev/formal-test:** Neither was accessed. The legacy `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123` limitation remains isolated and does not invalidate this independent E4 artifact set.
39. **Final commit:** Recorded after sealing; see the branch head and decision manifest. Repository branch: `exp/graph_anns_e4_semantic_factorial_reanalysis`.
40. **Checksum and bundle:** `results/graph_anns_e4_reanalysis/checksums.sha256` covers the reanalysis deliverables and is verified before commit. The GitHub push is the primary handoff; a bundle is only produced if push is unavailable and must then be reported explicitly.

## Interpretation

The four quantities are now separated: build-response heterogeneity is not the global-versus-adaptive gap; the global-versus-adaptive gap is not source→target transport tax; transport tax is not deployable method value. H1 and H2 are supported for these frozen targets, while H3 fails to show deployable value. This narrows the paper claim without erasing the substantive mechanism result.
