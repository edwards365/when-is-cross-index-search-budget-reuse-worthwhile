# RCRS Signal Pilot final report

## Result

Final label: **STOP_RCRS_NO_CERTIFIED_STOPPING_SIGNAL**.

SIFT design-only grouped cross-fitting showed a strong learnable signal (AUROC 0.907046, AUPRC 0.981033); its empirical design point had under-target risk 0.028 and gross NDC gain 65.836%. This was not a certified held-out result.

The GloVe minimal pilot reused three frozen Original indexes. Each seed passed 768/768 native/prefix equality checks. With fixed L2 logistic regression (C=1, seed 991), 16 complete policies, n=256 calibration and Bonferroni correction, **0/16 policies certified**. Protocol therefore selected fixed-e0 fallback. Calibration under-target rate was 12.500% (corrected upper bound 19.133%); design-evaluation under-target rate was 17.578% (corrected upper bound 24.934%). Fallback Recall difference was 0.000000, stop coverage 0.0%, and gross NDC gain 0.0%.

Gate R passed. Gate S failed because no learned policy certified; consequently Gate E and minimal Gate G could not support promotion. Gate P is trivially non-worse under fixed fallback. Because only rebuild seeds of one history were available, this is `MINIMAL_CROSS_REBUILD_SEED_PILOT`, not cross-history confirmation.

## Conclusion

Checkpoint state is predictive on SIFT design data, but the frozen GloVe experiment provides no certifiable stopping policy under the prescribed finite-sample guarantee. The project must stop this RCRS algorithm route rather than add thresholds, features, histories or calibration samples after seeing the result.
