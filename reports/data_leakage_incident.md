# Data leakage incident: base-identity perturbation holdout

## Incident

The preliminary controlled-swap evaluation generated holdout queries by adding independent noise to existing base points. The noise seed differed from the selection-query seed, but query templates retained base-point identities that were represented in the trace-attribution workload. This violated the intended independence of the performance holdout.

## Invalid result

The contaminated design showed an apparent `ef=10` Trace+Resistance Recall@10 gain of `0.001855`. This number is invalid. It appears only in the experiment log and leakage warnings, never in the formal `controlled_swap_eval_s7` summary or paired-comparison files.

## Detection and response

The overlap was detected during the holdout audit before Phase I conclusion. The preliminary result directory was moved outside the frozen formal result path. No threshold, edge subset, or metric was changed in response to its performance. A new holdout was generated with seed 101 by independently sampling 1,024 balanced two-cloud Gaussian queries, not by perturbing base points. The complete controlled evaluation was rerun on that holdout.

## Valid replacement result

The independent holdout showed no Trace+Resistance recall improvement. This valid negative result controls all Phase I conclusions.

## Prevention

Phase II uses explicit build/development/test roles, a test firewall, query-file checksums, and a rule that the formal test is not generated or read until the preregistration commit and checksum are frozen. Test queries, traces, nearest-neighbor labels, and failure identities cannot enter GGR construction or parameter selection.
