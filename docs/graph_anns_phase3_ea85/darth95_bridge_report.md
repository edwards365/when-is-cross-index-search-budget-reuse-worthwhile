# DARTH Recall@10=.95 semantic bridge

The official DARTH checkout was evaluated at target recall .95 on ten frozen target builds per dataset. Independent 500-query certification selected either raw DARTH or the pre-registered EF200 fixed-safe endpoint before the 1,000-query evaluation role was read.

| dataset | method | builds | selected_darth_builds | certified_builds | mean_eval_risk | max_eval_risk | mean_recall | mean_dists | mean_p95_dists | mean_p99_dists |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arxiv_nomic_100k | fixed_safe | 10 | 0 | 10 | 0.011000 | 0.015000 | 0.998770 | 2422.633100 | 3290.025000 | 3600.088000 |
| arxiv_nomic_100k | icba_audited | 10 | 0 | 10 | 0.011000 | 0.015000 | 0.998770 | 2422.633100 | 3290.025000 | 3600.088000 |
| arxiv_nomic_100k | raw_darth | 10 | 10 | 0 | 0.231200 | 0.277000 | 0.968370 | 874.086300 | 2697.375000 | 3299.236000 |
| sift_100k | fixed_safe | 10 | 0 | 10 | 0.009700 | 0.014000 | 0.998990 | 1978.369200 | 2638.115000 | 2749.349000 |
| sift_100k | icba_audited | 10 | 0 | 10 | 0.009700 | 0.014000 | 0.998990 | 1978.369200 | 2638.115000 | 2749.349000 |
| sift_100k | raw_darth | 10 | 10 | 0 | 0.225500 | 0.256000 | 0.967330 | 633.804100 | 1736.185000 | 2450.886000 |

## Build-cluster efficiency gain of ICBA-audited deployment versus fixed-safe

- sift_100k: relative mean-distance gain 0.00% (95% build-bootstrap CI 0.00%, 0.00%).
- arxiv_nomic_100k: relative mean-distance gain 0.00% (95% build-bootstrap CI 0.00%, 0.00%).

Wall-clock values are descriptive; distance computations are the primary efficiency currency.
Negative, fallback-only, and zero-gain outcomes are retained.
