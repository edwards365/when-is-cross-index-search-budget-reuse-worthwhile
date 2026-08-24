# GB-MPCC Graph Gate E0 final report

Decision: **STOP_REJECT_E0_NO_E1**. E1 remains unauthorized.

All 117 preregistered graphs completed. Original reproduction was exact in 9/9 runs; all graph invariants, weak-connectivity checks, and within-run upper-layer checksums passed; every temporary index was evaluated and deleted.

## Primary R4 outcome

| Dataset | Navigation seeds | Recall-NI | Mean NDC reduction vs Original | Worst fixed-ef recall difference |
|---|---:|:---:|---:|---:|
| sift_10k | 1/3 | FAIL | 4.694% | -0.017667 |
| glove100_10k | 2/3 | FAIL | 4.824% | -0.010200 |
| arxiv_nomic_10k | 1/3 | FAIL | 8.962% | -0.005733 |

GB-MPCC R4 reduces mean NDC on all three datasets, including effects that remain positive against both backbone-matched controls. That mechanism signal is not enough for the preregistered gate: only one dataset has at least two positive navigation seeds, and no dataset satisfies recall noninferiority at every fixed `ef` against all primary comparators. R1/R2 are ablations and cannot rescue the failed R4 gate.

The carried-forward label `PROXY_DISTRIBUTION_MISMATCH` remains applicable. No validation-dev or formal-test member was accessed, and no adaptive tuning occurred. The server-side unabridged artifacts are under `results/gb_mpcc/e0/derived_final`; their checksums are frozen in `manifests/gb_mpcc_e0_decision.json`.
