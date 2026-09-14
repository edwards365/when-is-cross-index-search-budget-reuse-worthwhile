# DARTH versus TCP M3: 10% data refresh

The preregistered 10% fixed-size delete/insert refresh cell completed on the same ten build seeds and disjoint certification/evaluation roles.

Raw DARTH again failed every target certificate: the frozen model had 15.18% mean certification risk, 21.28% maximum UCB, and 15.82% evaluation risk; refreshed target retraining had 16.68%, 22.96%, and 17.19%, respectively. Both audited deployments therefore reduced to the fixed certified fallback.

Both old and refreshed TCP pools were safe on all ten builds, with 0.04% certification risk, maximum UCB 0.95%, and 0.01% evaluation risk. However, every selected action was the fixed-safe endpoint, so TCP and the fixed baseline were identical: mean distance computations 1952.58, mean per-build p95 2628.75, and paired difference exactly zero.

The 10% cell therefore marks a recovery boundary. TCP preserves safety but has no efficiency advantage because the source-derived pool collapses to the endpoint; DARTH remains efficient only in its rejected, unsafe raw form, and target retraining does not restore admissibility. This is evidence for conditional TCP usefulness at lighter refresh levels, not a claim of universal dominance.

