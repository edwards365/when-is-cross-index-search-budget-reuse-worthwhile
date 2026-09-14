# DARTH versus TCP M3: 5% data refresh

The preregistered 5% fixed-size delete/insert refresh cell completed on ten independently permuted Faiss HNSW builds. All safety decisions use 500 target certification queries and a one-sided 95% Clopper--Pearson upper bound at the 5% risk threshold; evaluation uses a disjoint 1,000-query role.

Both raw DARTH policies failed certification on every build. The frozen pre-refresh model had 16.26% mean certification risk, a maximum UCB of 23.17%, and 16.56% evaluation risk. Retraining DARTH on the refreshed target did not repair the failure: 16.32% certification risk, 22.12% maximum UCB, and 16.73% evaluation risk. Audit-before-deploy therefore sent both policies to the certified fixed fallback.

The refreshed TCP pool passed all ten target certificates. Its evaluation risk was 2.43%, mean distance computations were 480.71 versus 942.87 for the fixed certified baseline, and the paired nested-bootstrap difference was -462.16 with 95% CI [-468.21, -456.15]. Its mean per-build p95 was also lower (1238.05 versus 1269.77). The old TCP pool passed only three raw certificates; after audited fallback it remained safe but its mean advantage CI touched zero.

This cell supports a conditional, not universal, claim: at 5% refresh, rebuilding the TCP source pool restores a safe and material computation advantage, whereas target retraining of DARTH does not fix its within-build risk calibration. TCP's 5% safety claim comes solely from independent target-query certification; nine source builds cannot supply a formal 5% exchangeable-build conformal certificate because their resolution floor is 10%.

