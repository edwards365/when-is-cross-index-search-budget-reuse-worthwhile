# ICBA/TCP versus DARTH: final comparison seal

The official DARTH implementation was integrated without source modification and evaluated beside TCP and a certified fixed baseline on SIFT-100K and Arxiv-Nomic-100K. Every cell used ten insertion-order builds, fixed query roles, exact truth, CPU Faiss HNSW, and disjoint 500-query target certification plus 1,000-query evaluation. The main event was Recall@10 at least 0.90 with a one-sided 95% risk UCB no greater than 5%.

DARTH's raw early exit was computationally cheap but scientifically inadmissible. Across 160 strategy-build decisions covering target training, frozen-source transfer, and 1%/5%/10% refresh old/retrained policies, zero passed the registered certificate. Typical evaluation risks remained about 15%--19%; target retraining did not close the gap. ICBA audit-before-deploy therefore prevented every unsafe DARTH deployment and chose fixed-safe.

TCP was safe after independent target certification. On SIFT it reduced mean distance computations versus fixed-safe by 44.8% in the rebuild cell, up to 26.5% at 1% refresh, and 49.0% at 5% refresh; the 5% cell also improved p95 by 31.72 computations. At 10% SIFT refresh the advantage became zero. On Arxiv, TCP selected fixed-safe in every cell, so safety held but mean and tail gains were exactly zero.

The final claim is deliberately conditional: ICBA supplies a useful deployment safety layer, and TCP offers material efficiency when the safe action class contains non-endpoint headroom. The comparison does not establish universal or cross-dataset efficiency dominance. Nine source builds have a 10% conformal resolution floor, so all 5% safety statements here come from independent target-query certification rather than a source-build theorem. Wall-clock measurements remain descriptive; distance computations are the primary efficiency estimand.

