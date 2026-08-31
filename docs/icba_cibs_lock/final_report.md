# Final CIBS closure report

## Audit identity

- Task: ICBA CIBS THEORY, PRIOR-ART AND SEMANTIC LOCK
- Frozen base: `3918d415afb6076b9b42a9ed2aac3c00ed1ddde9`
- Isolated branch target: `exp/icba_cibs_theory_semantic_lock`
- Server paths: not mounted; no claim of direct server-state inspection
- Real CIBS experiment: not run
- Sealed truth: not accessed

## Final decision

`CIBS_FIXED_THEORY_AND_SEMANTICS_LOCKED`

The decision means the fixed-family safety theorem, exact finite-sample instance, restricted cost proposition, action semantics, endpoint treatment, build/query preregistration, deployable output, and falsifiable pilot contract are closed. It does not mean that CIBS improves NDC, p95, or deployment cost.

Secondary state: `CIBS_RACE_THEORY_TEMPLATE_AUTHORIZED`, theory interface only. CIBS-Race implementation is not authorized until the Stage-I fixed pilot passes.

## Literature verdict

Twelve Level-A full texts were read at the relevant theorem/proof level. The most threatening modules are Learn-Then-Test, RCPS, SafeBAI, Track-and-Stop, LUCB, Hyperband, confidence sequences, correlated-arm BAI, ANNiE, and ConANN. No checked paper met all seven direct-method conditions. QBAT remained `FULLTEXT_UNVERIFIED` this round and prevents a universal “first” assertion.

## Theorem ledger

| Theorem | Status | Main conclusion |
|---|---|---|
| T-CIBS1 | `FORMAL_PROOF_COMPLETE` | any cost-based selection inside a simultaneously certified fixed set is (1-\alpha) safe |
| T-CIBS2 | `FORMAL_PROOF_COMPLETE` | exact Bonferroni-CP instance; maxima 3 and 0 failures |
| T-CIBS3 | `FORMAL_PROOF_RESTRICTED` | (2\eta_{\max}) cost regret to best certified action; needs optimum certification for oracle comparison |
| T-CIBS4 | `CLASSICAL_APPLICATION` | paired variance depends on covariance; no unconditional dominance |
| T-CIBS5 | `FORMAL_PROOF_COMPLETE` | finite break-even iff realized per-query gain is positive |
| T-CIBS6 | `FORMAL_PROOF_RESTRICTED` | classical gap-dependent testing/BAI lower bound under CIBS observations |
| T-CIBS7 | `FORMAL_PROOF_COMPLETE` | named-portfolio fixed-target safety cannot imply open-world safety |

## Exact certification thresholds

- Main (K=3,L=12,n=256): maximum 3 failures; (U(3)=0.0484701181), (U(4)=0.0549482108).
- Low-cost (K=2,L=12,n=128): maximum 0 failures; (U(0)=0.0470879851), (U(1)=0.0638799000).
- If (n=250): maximum 3 failures; (U(3)=0.0496109868).

## Semantic lock

CIBS-Fixed deploys one named serialized hnswlib build and one raw global fixed-`ef`. Each build-budget pair is its own action. `ef` is not an expansion/NDC cap, raw recall is not assumed monotone, and no budget envelope reduces multiplicity. Endpoint-infeasible/right-censored queries are failures or preregistered abstentions, never imputed maximum-budget successes.

One exact truth is shared across action evaluations; action-specific searches are charged. Query roles are disjoint and immutable. Builds vary only by preregistered legal seed/insertion order with all other construction and toolchain fields fixed.

## Prior empirical evidence

The frozen (K=3,n=256) and (K=2,n=128) budget-proxy numbers remain `EXPLORATORY_OFFLINE_SIMULATION`. They are neither algorithm gains nor deployment gains and were not used as proof of NDC/p95 benefit.

## Pilot authorization

CIBS-Fixed pilot: **authorized**, conditional on preregistered build and query-role manifests. CIBS-Race implementation: **not authorized**. Both SIFT-100K and Arxiv-Nomic-100K must pass recall non-inferiority, at least 1% net mean-NDC gain, p95 non-inferiority, unsafe-control, endpoint, finite-break-even, top-1%-deletion, and artifact-replay gates.

## Novelty and venue

Maximum current novelty is `NEW_COMBINATION_OF_CLASSICAL_RESULTS`, with a potential Graph-ANNS-specific systems contribution in the joint action and cost/endpoint contract. The work is not currently a NeurIPS-level theory contribution. A database/ANN systems submission becomes plausible only after the fixed pilot and independent portfolio confirmation.

## Verification

Fourteen finite counterexamples are implemented and pass. Exact CP thresholds are recomputed by test. The decision manifest is machine-readable, all tabular contracts are CSV, and the final manifest excludes caches and temporary files.

