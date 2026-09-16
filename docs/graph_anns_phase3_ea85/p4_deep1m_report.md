# Phase 4 Deep1M native-count scale report

Decision: **DEEP1M_PORTABILITY_FAILURE_CONFIRMED_WITH_NATIVE_TAILS**.

Eight independent registered hnswlib builds and 1,000 fresh queries produced 56 directed source→target build pairs. The native/counter equivalence Gate passed 60/60 cases. Transport risk was 0.2886 (target-build bootstrap 95% CI [0.2666, 0.3105]); target-own endpoint-aware reference risk was 0.0882; incremental risk was 0.2004 ([0.1729, 0.2277]).

Transport NDC mean/p95/p99 were 1315.3/3633.0/3931.0; target-own reference values were 1318.1/3636.0/3937.0. Source/target right-censoring rates were 0.0882/0.0882. Minimum LOTO incremental risk was 0.1942; deleting the largest-risk target build left 0.1942.

Exact truth required 17.6s; registered builds required 1611.4s in total and 3.97 GiB. This phase establishes scale portability and native tail evidence only; it does not establish TCP deployment value or universal Graph-ANNS behavior.
