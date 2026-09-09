# E4 Confirmatory HNSWlib Rebuild Matrix — Final Report

Final label: `E4_STRONG_CONFIRMATION_TWO_DATASETS`.

1. Completed within the registered operational timebox.
2. Frozen starting commit: `6829bbc377ca113fd8f8a94499a4af753dd95aa3`.
3. Branch: `exp/graph_anns_e4_confirmatory_rebuild_matrix`; final commit is recorded after seal.
4. Tracked E4 tree is clean after seal; unrelated pre-existing untracked paths were preserved.
5. The 48 builds mean 24 per dataset: eight new seeds crossed with three frozen insertion histories.
6. Actual builds: SIFT 24; Arxiv 24.
7. Build outcome: 48 successful, zero failed.
8. Confirmatory queries: 1,000 per dataset; 250 fixed sentinel and 750 disjoint evaluation queries.
9. All forbidden role intersections are zero.
10. The complete grid `{10,20,40,80,120,200}` was evaluated for every build and query.
11. Native and instrumented top-k results were checked for equality on every query-budget cell by the runner.
12. SIFT nonzero safe-budget change fraction: 0.892; mean diameter: 43.13 ef units.
13. Arxiv nonzero safe-budget change fraction: 0.759; mean diameter: 29.729 ef units.
14. Mean pairwise rank inversion: SIFT 0.1900; Arxiv 0.1546, over 276 build pairs per dataset.
15. Endpoint conversion fractions are 0.026 (SIFT) and 0.025 (Arxiv); endpoint failures remain absolute failures rather than ef=200 successes.
16. Historical source reuse at ef=120 has absolute risk 0.03239 on SIFT and 0.03322 on Arxiv.
17. Build-cluster 95% risk CIs are [0.02983,0.03489] for SIFT and [0.02994,0.03639] for Arxiv.
18. The safe-transfer NDC tax versus the per-target safe oracle is 1.7833 (178.3%) on SIFT and 2.4383 (243.8%) on Arxiv.
19. Its build-cluster 95% CIs are [1.7388,1.8303] and [2.3835,2.4970], respectively.
20. Same-build, source reuse, target recalibration, fixed-safe and nondeployable oracle are reported in `per_build_summary.csv`; target recalibration selected mean ef 173.33 on SIFT and 163.33 on Arxiv.
21. Every leave-one-build-out safe-regret estimate remains above the preregistered 1% threshold.
22. Removing the largest contributing build leaves effects 1.7742 (SIFT) and 2.4286 (Arxiv).
23. Removing the highest-gain 1% of queries preserves direction: 1.8046 and 2.4660.
24. For source reuse, mean/p50/p95/p99 NDC are 1517.84/1569.44/1912.89/2012.20 (SIFT) and 1654.73/1638.48/2166.25/2346.84 (Arxiv).
25. Source-reuse mean/p50/p95/p99 kernel latency in ns are 183903/189543/227319/238897 (SIFT) and 1153670/1139950/1519057/1652807 (Arxiv).
26. NDC and wall-clock directions agree against fixed-safe: mean runtime gains are 35.65% and 34.62%, with p95 changes -35.52% and -37.21%.
27. Offline build time totals 578.02 s for SIFT and 3361.30 s for Arxiv; all index, truth and result artifacts are checksummed.
28. A deployment break-even claim is not made because target truth/control pricing was not independently measured; source reuse itself adds no target profiling cost.
29. SIFT Dataset-Level Gate: `STRONG_SUPPORT`, through the preregistered safe-regret route.
30. Arxiv Dataset-Level Gate: `STRONG_SUPPORT`, through the preregistered safe-regret route.
31. Cross-dataset decision: `E4_STRONG_CONFIRMATION_TWO_DATASETS`.
32. The evidence supports a strong fixed-target hnswlib rebuild-portability claim, not a universal Graph-ANNS or SOTA claim.
33. The conclusion is not restricted to dataset-conditioned support because both datasets passed strongly.
34. Runtime direction agrees with NDC, but deployment evidence remains scientific-only because mean Recall differences versus fixed-safe are -0.00271 and -0.00244, outside the -0.001 deployment margin.
35. Independent results agree with the historical core phenomenon while using new builds and new queries.
36. `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123` remains isolated and is not promoted by E4.
37. validation-dev access: false.
38. formal-test access: false.
39. future-replication access: false.
40. Paper main-result writing is allowed within the fixed-target hnswlib evidence scope.
41. A later independent replication remains allowed and sealed.
42. The Graph-ANNS A-track core claim does not need to stop, but deployment-efficiency wording must remain excluded.
43. Final report: `docs/graph_anns_e4/final_report.md`.
44. Decision manifest: `manifests/graph_anns_e4_confirmatory_decision.json`.
45. Checksum status: complete and test-verified in `results/graph_anns_e4/checksums.sha256`.
46. Bundle: not required because the branch was pushed successfully; authoritative remote branch is the GitHub branch recorded in the seal.

The primary inference unit is the independent build. Query bootstrap is supplementary. The per-target oracle is a nondeployable reference. The main confirmation is scientific evidence of rebuild-sensitive safe-budget response and a safe-but-conservative portability barrier; it is not evidence that ef=120 satisfies the separate deployment Recall margin.
