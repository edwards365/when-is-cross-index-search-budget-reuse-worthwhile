# Equal-information baseline audit: decision report

## Status

`POST_HOC_FROZEN_RESPONSE_EQUAL_INFORMATION_BASELINE_AUDIT`

The analysis read the complete registered five-percent-refresh response cube;
it built no index and issued no search.  Before computing a new comparison it
exactly reproduced the paper's compact TCP joint-decision and endpoint arrays
for both SIFT-100K and Arxiv-Nomic-100K.

## Result

All policies use the same Recall@10 `< .95` event, native action grid, 500
selection queries, 500 independent certification queries, and 1,000 held-out
evaluation queries.  Candidate and endpoint checks split the confidence-error
budget as `.025 + .025`.

| Dataset | TCP mean gain vs target-global | 95% crossed CI | p95 ratio | Evaluation risk, TCP / target-global | Accepted targets, TCP / target-global |
|---|---:|---:|---:|---:|---:|
| SIFT-100K | 27.60% | [17.92%, 36.72%] | 1.009 | 1.79% / 2.01% | 10 / 7 |
| Arxiv-Nomic-100K | 10.78% | [-8.48%, 29.43%] | 1.109 | 1.68% / 2.17% | 6 / 8 |

SIFT supplies positive evidence that query-conditional TCP adds mean-work
value beyond a target-only global action under the same target information;
the direction survives every leave-one-target-out deletion and deletion of the
largest-gain target.  Arxiv does not close that claim: its mean interval crosses
zero and its p95 is 10.9% higher than target-global.  The correct conclusion is
therefore dataset-conditional mean value with an explicit Arxiv tail boundary,
not universal superiority over simple target recalibration.

The source-global comparator is also informative but answers a different
question.  It reduces mean NDC relative to the endpoint by 33.12% on SIFT and
16.02% on Arxiv, while TCP reduces it by 44.39% and 29.86%, respectively.  TCP
has lower mean work but higher pooled p95 than source-global on both datasets;
this reinforces the need to report mean and tail estimands separately.

## Claim boundary

This is a post-hoc attribution analysis on already-observed frozen responses.
It may close the paper's missing simple-baseline comparison, but it cannot be
called prospective validation, an unseen-build certificate, a runtime result,
or a universal ranking.  The parent paper's endpoint-relative recovery result
remains unchanged.
