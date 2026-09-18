# Grid and risk sensitivity: decision report

## Status

`POST_HOC_FROZEN_RESPONSE_GRID_AND_RISK_SENSITIVITY`

The registered primary condition exactly reproduces the equal-information
audit.  Every condition reuses the same frozen response cube and query roles;
none is an independent confirmation.

| Condition | Dataset | TCP gain vs target-global [95% crossed CI] | p95 ratio | TCP/target accepted | Qualified endpoints |
|---|---|---:|---:|---:|---:|
| Primary | SIFT | 27.60% [17.92, 36.72] | 1.009 | 10/7 | 10/10 |
| Primary | Arxiv | 10.78% [-8.48, 29.43] | 1.109 | 6/8 | 10/10 |
| Coarse grid | SIFT | 21.08% [9.38, 30.30] | 1.062 | 8/7 | 10/10 |
| Coarse grid | Arxiv | 33.18% [31.07, 35.27] | 1.118 | 10/10 | 10/10 |
| Upper grid | SIFT | 27.88% [1.77, 46.95] | 1.024 | 8/7 | 10/10 |
| Upper grid | Arxiv | -16.88% [-38.96, 4.51] | 1.143 | 2/8 | 10/10 |
| Recall event 0.90 | SIFT | 34.33% [14.21, 51.17] | 0.909 | 8/4 | 10/10 |
| Recall event 0.90 | Arxiv | 35.75% [26.80, 46.94] | 0.837 | 10/9 | 10/10 |
| Risk limit 2.5% | SIFT | 2.68% [-3.70, 10.20] | 1.012 | 2/2 | 10/10 |
| Risk limit 2.5% | Arxiv | 0.00% [0.00, 0.00] | 1.000 | 1/7 | 7/10 |

## Decision

The SIFT mean advantage is not tied to one exact grid: it remains positive on
both nested subgrids, although the coarse grid misses the 5% p95
noninferiority threshold.  Arxiv is materially grid-sensitive: the mean result
ranges from positive on the coarse grid to negative on the upper grid, and the
p95 comparison is blocked in every Recall@10=.95 grid condition.

The Recall@10=.90 condition is positive on both datasets, but it changes the
failure event and cannot be used to rescue a Recall@10=.95 claim.  Tightening
the risk limit to 2.5% removes the SIFT mean conclusion and makes three Arxiv
endpoints unqualified.  TCP's incremental value must therefore remain
conditional on the registered grid, failure event, and SLA.  This sensitivity
strengthens the audit framing but does not authorize a universal algorithmic
superiority claim.
