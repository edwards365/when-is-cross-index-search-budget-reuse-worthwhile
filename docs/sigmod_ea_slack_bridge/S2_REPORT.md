# S2 — Stable-Tail Semantics and Certificate Closure

## Definitions and scope

For a build `b`, query `q`, and registered ordered action grid `a_0 < ... < a_J`, let `Z_b(q,j)=1` denote failure (`Recall@10 < 0.95`). The first-passing index is the least `j` with `Z_b(q,j)=0`. The stable-tail index is the least `j` such that `Z_b(q,l)=0` for every observed `l>=j`; it is unresolved when no such index exists. These are finite-grid response labels, not universal guarantees about native `ef` or unseen actions.

## T-S2-1: finite-grid stable-tail implication

For an executed index `A` and target stable-tail index `S_t`,

`Z_t(q,A) <= 1{S_t is unresolved or S_t > A}`.

The statement follows directly from the definition: when `S_t` is finite and `A>=S_t`, every response in that observed suffix passes. Consequently, the target failure probability is bounded by the probability of an unresolved target stable tail or a target stable-tail index above the executed action. This result is `PROVED_UNDER_STATED_ASSUMPTIONS`; the assumptions are the fixed finite action grid and the frozen deterministic response cube.

The machine audit covers four operator–dataset settings, 24 builds, 750 queries, five registered lanes, and all 552 directed source–target pairs per setting. Across 7,463,088 finite antecedent instances, it finds zero implication violations. The exact per-setting antecedent counts are retained in `s2_implication_audit.csv`; no directed pair is treated as an independent build replicate.

## T-S2-2: three-state certification

For `k` failures among `n` certification queries, the analysis computes one-sided exact Clopper–Pearson bounds. It reports:

- `QUALIFIED` only when the upper bound is at most `delta=0.05`;
- `CONFIDENTLY_ABOVE_DELTA` only when the lower bound is greater than `delta`;
- `INDETERMINATE` otherwise.

This is a `CLASSICAL_APPLICATION`. In particular, failure to qualify is not evidence that risk is above 5%. The single-policy view uses `alpha=0.05`. The fixed candidate-plus-endpoint family view uses `alpha_candidate=0.025` and `alpha_endpoint=0.025` for every target, without target-specific tuning.

## Empirical contact

Under the family allocation, the number of qualified directed pairs is:

| Operator | Dataset | +0 | +1 | +2 | Endpoint |
|---|---|---:|---:|---:|---:|
| hnswlib | SIFT-100K | 0/552 | 163/552 | 411/552 | 552/552 |
| hnswlib | Arxiv-Nomic-100K | 0/552 | 160/552 | 543/552 | 552/552 |
| Faiss HNSW | SIFT-100K | 0/552 | 0/552 | 552/552 | 552/552 |
| Faiss HNSW | Arxiv-Nomic-100K | 0/552 | 23/552 | 552/552 | 552/552 |

At +2, none of the remaining hnswlib SIFT pairs is confidently above 5% under the family allocation: 411 qualify and 141 remain indeterminate. Arxiv has 543 qualified and 9 indeterminate. This distinction is scientifically important: +2 sharply improves certifiability, but hnswlib SIFT is not universally certified. Faiss +2 qualifies all frozen directed pairs, while its cumulative NDC cost remains unavailable from the historical cube.

The retrospective source stable-tail lane is nearly identical to first-passing +0 because the stored response curves are almost monotone; it therefore does not solve cross-build portability. The stable-gap relation is retained as mechanistic contact, not promoted to a native runtime guarantee.

## Gate and claim boundary

S2 passes its theory and semantic Gate. The result supports a precise conditional statement: finite registered slack reduces the probability that the target stable requirement lies above the executed action, and the remaining candidates must be separated into qualified, indeterminate, and confidently unsafe states. It does not support universal `ef` monotonicity, prospective validation, independent-build inference from 552 pairs, or automatic deployment of +2. The evidence remains `POST_HOC_FROZEN_RESPONSE_REANALYSIS`.
