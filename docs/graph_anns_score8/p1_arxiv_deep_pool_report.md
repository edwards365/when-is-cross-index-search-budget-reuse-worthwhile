# Arxiv-10K deep conformal pool re-audit

This is a pure-code derivative of the frozen 100-build hit tensors; no ANN search or graph build was run.
The old Arxiv farm summary is preserved. Its k=9 risk used `(boolean_success < 10)`, which is always true; the corrected audit evaluates raw hit counts.

| arm | k | alpha | risk | target-cluster 95% CI | abstain | budget/oracle | point | CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| A_single_thread | 9 | 0.10 | 0.023280 | [0.022313, 0.024260] | 0.006771 | 2.0111 | True | True |
| A_single_thread | 19 | 0.05 | 0.009782 | [0.009188, 0.010409] | 0.011884 | 2.2443 | True | True |
| A_single_thread | 25 | 0.05 | 0.007081 | [0.006561, 0.007619] | 0.014043 | 2.3236 | True | True |
| A_single_thread | 49 | 0.05 | 0.007335 | [0.006709, 0.007972] | 0.010062 | 2.2498 | True | True |
| B_8thread | 9 | 0.10 | 0.023586 | [0.022611, 0.024559] | 0.006501 | 2.0122 | True | True |
| B_8thread | 19 | 0.05 | 0.009938 | [0.009304, 0.010573] | 0.011151 | 2.2515 | True | True |
| B_8thread | 25 | 0.05 | 0.007251 | [0.006751, 0.007767] | 0.013327 | 2.3331 | True | True |
| B_8thread | 49 | 0.05 | 0.007230 | [0.006633, 0.007851] | 0.009174 | 2.2442 | True | True |

Final label: `ARXIV_DEEP_POOL_VALIDATED`.
