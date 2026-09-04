# Conflict resolution report

The conflict ledger is authoritative for current wording. Earlier claims that depended on raw `ef` monotonicity, structural similarity, paired query reuse, oracle selection, or query-only bootstrap are either restricted or superseded.

## Key resolutions

1. Raw `ef` remains an independent action parameter. It is not an expansion bound and does not inherit expansion-prefix monotonicity.
2. (B_G^{ef}) and (B_G^{exp}) are different estimands. They can be connected only under a fixed implementation and an explicit mapping from `ef` to a deterministic or controlled expansion prefix; no such mapping is assumed here.
3. Native fixed-`ef` Recall is not guaranteed query-wise monotone. GSC certifies each build×`ef` action separately.
4. Expansion-prefix upward closure is a restricted statement about an observed search trace. It cannot be transferred to raw-`ef` actions without a new proof.
5. Stage and NDC are not automatically an ordered budget ladder. Stage can be a candidate index; NDC is a measured cost, not a control parameter.
6. High AUROC is an association statistic, not a safety threshold or stopping certificate.
7. Paired B2 gains are efficiency evidence only when query roles and sampling are valid; they do not replace disjoint confirmation.
8. CIBS budget-proxy gains do not establish a feasible certified candidate pool or deployment benefit; the latest closure found no two-dataset CI-supported joint-feasible action.
9. Stable-by-Construction is a conditional design direction. Failure of one operator family does not refute the entire design space, but it removes any empirical bridge claim not directly measured.
10. Active-RACS/BAI comparisons are classical structural neighbors; they do not supply Graph-ANNS build semantics.
11. Query bootstrap estimates within-portfolio query variability. It does not quantify build-cluster or open-world uncertainty.
12. Oracle headroom is an upper bound, not observable algorithm gain.
13. Correct selection conditional on a feasible candidate pool is distinct from proving that the generated pool contains a feasible action.

## Current rule

GSC may claim a conditional fixed-target certificate if its final candidate family is frozen before independent certification. It may claim a behavioral-stability association only if (D_Z), (D_C), endpoint changes, and rank reversals are measured separately. It may not claim open-world portability or guaranteed candidate generation.

