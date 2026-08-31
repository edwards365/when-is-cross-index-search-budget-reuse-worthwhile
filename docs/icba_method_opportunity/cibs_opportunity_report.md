# CIBS opportunity report

CIBS is the only route with a complete frozen opportunity input: nine real builds and 1000 shared open queries for both SIFT-100K and Arxiv-Nomic-100K. Five hundred seed-991 splits were run for K={2,3,5}, n={32,64,128,256}. Per-action CP was retained only as a diagnostic because selection inflates error. The primary sensitivity analysis used Bonferroni family-wise control over build-budget actions and the same correction for the certified single-build baseline.

At K=3,n=256 the online budget proxy improved 17.60% on Arxiv and 9.73% on SIFT; unsafe-selection replicate rates were 0% and 0.2%. At K=2,n=128 gains were 23.13% and 24.00%, both with 0% unsafe replicates. n<=64 always fell back; K>=3,n=128 can lose to the single-build baseline because multiplicity destroys power. This is paired full-information evidence for a K-n safety/power frontier, not an algorithm win.

Gate H passes as exploratory non-Oracle headroom. Gate S passes only for the simultaneous-control formulation. Real NDC/p95, LOBO and common-unit break-even remain one combined measurement gap for a feasibility pilot. Route label: `PROMOTE_TO_FEASIBILITY_PILOT`.
