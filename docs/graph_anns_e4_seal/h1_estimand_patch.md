# H1 estimand patch

The phrase “H1 nonzero fraction” is retired because it mixed three objects. H1-A is full-family variation coverage, a descriptive support/range statistic. H1-B is within-seed cross-order pairwise disagreement with fixed order treatments. H1-C is within-order cross-seed pairwise disagreement. H1-B/C use crossed seed–query inference and leave-one-seed diagnostics.

Six legacy within-order intervals placed their point estimate above the reported upper bound. Duplicate-seed n-out-of-n resamples reduce the number of distinct environments for a nonsmooth support/range statistic, while the point estimate uses all eight unique seeds. Those intervals remain preserved but are prohibited as primary paper evidence. The replacement uses smooth pairwise disagreement and absolute-difference estimands; its centered cluster-bootstrap intervals contain their estimates.
