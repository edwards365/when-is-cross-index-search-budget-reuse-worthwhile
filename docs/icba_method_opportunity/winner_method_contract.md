# Winner method contract: CIBS

1. **Name:** Certified Index-Build Selection (CIBS).
2. **Problem:** choose one serialized Graph-ANNS build and ordered budget using shared target sentinels.
3. **Input:** preregistered K builds, budget grid, sentinel queries/truth, service size N, delta=alpha=.05.
4. **Output:** build ID, budget, simultaneous certificate, or fixed-safe fallback.
5. **Information model:** paired full-information sentinel responses; no source Oracle or evaluation truth.
6. **Objective:** minimize common-unit total cost among certified actions.
7. **Safety:** LTT/FWER-valid simultaneous risk control after selection.
8. **Cost:** online + amortized build/truth/certification/selection + fallback.
9. **Pseudocode:** preregister candidates; collect shared sentinel truth once; evaluate each build-budget action; compute simultaneous bounds; delete uncertified/endpoint-infeasible actions; select minimum measured total cost; otherwise fallback; freeze; evaluate independently.
10. **Theory interface:** finite-action simultaneous testing plus paired full-information efficiency and nested build/query uncertainty.
11. **Closest priors:** LTT/RCPS, SafeBAI, Track-and-Stop, algorithm configuration, ANN autotuning.
12. **Independent point:** Graph-ANNS build×ordered-budget action with shared truth, endpoint censoring and amortized build cost; not generic safe selection.
13. **Baselines:** certified single build, random build, fixed-safe, full profiling, Oracle portfolio, LTT/RCPS, SafeBAI-style allocation.
14. **Minimum implementation:** K=2 and K=3 serialized hnswlib builds; no new model.
15. **Minimum pilot:** SIFT and Arxiv, new design/cert/eval queries, 3 histories, fixed seeds.
16. **Query split:** design only for preregistration; sentinel certification and evaluation mutually exclusive.
17. **Build split:** candidate builds fixed before responses; held-out build histories for robustness.
18. **Metrics:** risk UCB, unsafe selection, fallback, mean/p95 NDC, Recall, censoring, build/search/truth costs and break-even.
19. **Success Gate:** both datasets risk<=5%, gain>=1%, p95 not worse, top1 deletion and LOBO positive, finite break-even.
20. **Stop:** any leakage, simultaneous safety failure, no two-dataset gain, p95 harm, or no finite break-even.
21. **Time:** 7-14 days for minimum implementation and pilot.
22. **Storage:** target 10-20 GiB with >=5 GiB reserve.
23. **Compute:** CPU only; no GPU.
24. **Paper story:** hidden build variability -> source-only impossibility -> shared target evidence -> certified build-budget selection.
25. **Allowed claim:** feasibility of certified fixed-target selection conditional on preregistered finite candidates.
26. **Forbidden claim:** first safe selection, cross-build generalization, Oracle gain as deployed gain, or confirmatory performance.
