# DARTH versus TCP M3: 1% data-refresh result

Status: **1% refresh supports audited TCP recovery value; M3 remains open for 5% and 10%.**

After a seeded 1% equal-size delete/insert refresh and ten independent Faiss HNSW rebuilds, neither the old DARTH model nor a freshly retrained per-build DARTH model passed any of the ten independent target certificates. Their raw evaluation risks were 18.09% and 17.98%, respectively. Auditing therefore routed both to the certified fixed fallback, eliminating their raw computation advantage. This again shows that target retraining alone does not repair the registered query-level safety failure.

The old-snapshot TCP pool passed its raw target certificate on 4/10 builds; the refreshed-snapshot pool passed on 6/10. With the preregistered audit-and-fallback rule, both deployed policies were certified on all ten builds. Old-pool audited TCP achieved 1.86% evaluation risk and 791.3 mean distance computations versus 1.00% and 964.6 for fixed-certified; the paired reduction was 173.3 computations with 95% CI [43.2, 304.9]. Refreshed-pool audited TCP achieved 1.92% risk and 708.7 computations, a reduction of 255.9 with CI [126.7, 384.5]. Mean per-build p95 was slightly worse than fixed (1287.0 old pool and 1295.0 refreshed versus 1275.8), so the result is a mean-efficiency gain with a small tail tradeoff rather than universal dominance.

Because nine source builds only provide a 10% exchangeable-build alpha floor, the 5% safety statement is supplied by independent 500-query target certification plus fixed fallback. It is not presented as a 5% build-exchangeability theorem.
