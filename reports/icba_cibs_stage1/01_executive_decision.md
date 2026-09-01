# ICBA CIBS-Fixed Stage-I final decision

Final label: **CIBS_FIXED_STAGE1_FAILED_MINIMUM_GATE**. Evidence: `EXPLORATORY_FIXED_TARGET_STAGE_I`; scope: `CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO`.

| Dataset | Minimum Gate | Failed checks |
|---|---|---|
| ArXiv-Nomic-100K | FAIL | recall_delta_ge_minus_0_001 |
| SIFT-100K | FAIL | finite_break_even, p95_ndc_delta_le_0, recall_delta_ge_minus_0_001, relative_B1_mean_ndc_gain_ge_0_01 |

## 32-point closure

1. Frozen base retained at b0190169cdb758aa5311c7d13fbfd4fd724020f0.
2. Pre-truth amendment committed before Phase 1.
3. Tau fixed at Recall@10 >= 0.90.
4. Raw ef grid fixed to 12 values.
5. G1 ef=100000 fallback independently proved.
6. Evidence level is EXPLORATORY_FIXED_TARGET_STAGE_I.
7. Query semantics are a frozen finite pool.
8. Role overlap is zero.
9. Historical source-ID overlap is zero.
10. Future-confirm was never opened.
11. K=3 build portfolio was frozen.
12. All six indexes passed connectivity and replay.
13. Scalar compiler/SIMD mode replayed.
14. Native/tracer top-k equivalence passed.
15. Native/tracer exact-NDC equivalence passed.
16. Sentinel n=256 completed for both datasets.
17. All 36 actions were charged separately.
18. Exact CP alpha/36 certification replayed.
19. Selected actions were frozen before evaluation.
20. Evaluation used 500 queries per dataset.
21. Evaluation performed no reselection.
22. B0 through B5 were reported.
23. Paired bootstrap used 5000 replicates, seed 991.
24. Top-1% gain deletion was reported.
25. Build effects and LOBO were reported.
26. Selection stability was reported.
27. Complete wall-cost ledger includes two truth channels.
28. Workloads N=1e3..1e7 were reported.
29. K=2 ablation ran only after main completion.
30. K=2 did not replace main K=3.
31. Minimum Gate failed on both datasets.
32. No independent confirmation or CIBS-Race is authorized.
