# DARTH versus TCP on Arxiv-Nomic-100K: M3 refresh

The preregistered 1%, 5%, and 10% fixed-size delete/insert refresh cells each used ten paired insertion-order builds, 2,000 training queries, 500 disjoint certification queries, and 1,000 disjoint evaluation queries. All exact truth and large artifacts remained on data500.

DARTH failed every raw certificate in all six old/retrained strategy cells. Across refresh levels, raw evaluation risk ranged from 14.79% to 16.98%; target retraining changed point estimates but never made a build admissible. Audit-before-deploy therefore used fixed-safe for every DARTH build.

Both old and refreshed TCP pools passed all target certificates at every refresh level. However, the max-of-nine source action was the fixed-safe endpoint on every query/build: at 1%, 5%, and 10%, audited TCP and fixed-safe had exactly the same mean distance computations and p95, with paired differences and intervals equal to zero.

Arxiv consequently provides a clean negative-headroom result. ICBA/TCP remains safe, but neither old nor refreshed pools recover efficiency. This does not invalidate the SIFT gain; it limits the claim to dataset/scenario cells where a non-endpoint safe action exists.

