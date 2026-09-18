# S3 independent target-certification result

## Decision

`S3_GATE_PASS_INDEPENDENT_TARGET_CERTIFICATION`

The S4-frozen Faiss `source_selected_plus_1` policy was evaluated without
retuning on the S2-frozen query roles. Each dataset used 500 target-certification
and 500 mutually exclusive target-evaluation queries across 24 registered builds
and 552 directed source-to-target pairs. All 48 indexes matched their frozen
hashes; no index was built or modified.

## Results

| Dataset | Candidate / fallback / no action | Evaluation risk (95% build-cluster CI) | Mean NDC saving (95% build-cluster CI) | Pooled p95 ratio | Worst target p95 ratio | LOBO minimum saving |
|---|---:|---:|---:|---:|---:|---:|
| SIFT-100K | 552 / 0 / 0 | 0.126% [0.087%, 0.167%] | 8.283% [7.923%, 8.554%] | 0.9964 | 0.9987 | 8.267% |
| Arxiv-Nomic-100K | 552 / 0 / 0 | 0.530% [0.458%, 0.606%] | 29.083% [28.632%, 29.535%] | 0.9797 | 0.9828 | 29.027% |

The maximum candidate certification UCB was 2.318% on SIFT and 2.593% on
Arxiv; maximum endpoint UCBs were 1.743% and 2.036%. Thus every executed
candidate passed its independent target certificate. SIFT used the below-endpoint
action for 92/552 directions; Arxiv used it for 322/552 directions. The remaining
directions executed the endpoint and therefore contributed safety but no action
reduction.

Interleaved single-thread timing showed mean wall-clock savings of 9.273%
[8.867%, 9.592%] on SIFT and 26.572% [26.131%, 27.034%] on Arxiv. These timing
figures remain `EXPLORATORY_FIXED_MACHINE_INTERLEAVED`; NDC is the primary
efficiency endpoint until the lifecycle/timing phase is sealed.

## Gate interpretation

Both datasets pass independent certification, evaluation risk, positive mean-NDC
confidence bound, pooled p95 non-inferiority, and leave-one-target-build-out
robustness. This closes the S3 question for the registered Faiss builds and query
distribution. It does not establish cross-implementation recovery or net
lifecycle economics; those remain separate evidence questions.

## Integrity

- Preregistration commit: `ba9cd70` before any S3 vector or truth access.
- Raw evidence: 48 compressed files and 288,000 query-action rows.
- Integrity checks: 15/15 passed.
- New query roles accessed: target-certification and target-evaluation only.
- `validation-dev`, `formal-test`, and reserved truth: not accessed.
- Next status: `S4_LIFECYCLE_AND_WALL_CLOCK_ELIGIBLE_NOT_STARTED`.
