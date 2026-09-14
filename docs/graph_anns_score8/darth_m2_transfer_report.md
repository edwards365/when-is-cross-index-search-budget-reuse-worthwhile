# DARTH M2 frozen-source transfer report

Status: **WITHIN_BUILD_CALIBRATION_FAILURE_DOMINATES_TRANSFER**

The 11-feature DARTH model frozen on the unpermuted source index was replayed without adaptation on all ten independent insertion-order rebuilds. It passed zero of ten independent 500-query target certificates: mean certification risk was 17.46% and the worst one-sided 95% upper bound was 23.38%. Its mean evaluation risk was 18.02%, mean Recall@10 was 0.92891, mean distance computations were 375.6, and mean per-build p95 distance computations were 680.1.

Fresh target-trained DARTH also passed zero of ten certificates. Its mean evaluation risk was likewise 18.02%, with source-minus-target risk difference 0.000 and nested 95% bootstrap CI [-0.0091, 0.0091]. Target retraining did not improve computation either: source-minus-target mean distance difference was -13.45 with CI [-28.66, 0.18]. Frozen-source LOBO mean-risk range was [17.82%, 18.21%].

Accordingly, these data do not identify rebuild transfer as DARTH's primary failure mechanism: the same registered stopping rule is already unsafe when trained and evaluated within each target build. ICBA correctly rejects both frozen and retrained versions. The conclusion is scoped to the registered SIFT-100K configuration and primary per-query Recall@10>=0.90 event; it is not a general negative result about DARTH.
