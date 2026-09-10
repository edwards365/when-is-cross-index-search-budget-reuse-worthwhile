# Phase 1B profiling and break-even seal

Evidence role: `profiling_cost_only`; runtime/resource measurement only. No values in this phase select scientific thresholds or actions.

## Findings

- sift_100k / hnswlib (100K): n=59 resident profiling median 0.117234s (truth 0.102985s, six-action replay 0.013666s, control 0.000584s).
- sift_100k / faiss (30K_FROZEN_FAISS_BASE): n=59 resident profiling median 0.016826s (truth 0.008923s, six-action replay 0.007320s, control 0.000584s).
- arxiv_nomic_100k / hnswlib (100K): n=59 resident profiling median 0.993616s (truth 0.880984s, six-action replay 0.112035s, control 0.000597s).
- arxiv_nomic_100k / faiss (30K_FROZEN_FAISS_BASE): n=59 resident profiling median 0.247530s (truth 0.182002s, six-action replay 0.064931s, control 0.000597s).

The registered economic label is **PROFILING_COST_OPERATOR_DEPENDENT**. On the directly measured hnswlib and Faiss cells, certification control is negligible and total profiling is seconds or less at the registered sizes. The old blanket claim that profiling is expensive is not supported at this scale. Faiss must be described as a 30K-base external-validity cell despite its historical dataset label; Vamana direct cost-only replay remains NOT_ESTIMABLE because the frozen binary/config interface couples replay to materialized evaluation query/truth files.

Break-even is point-estimable only for hnswlib, where a frozen per-target certified action ledger exists. Faiss and Vamana are explicitly NOT_ESTIMABLE rather than assigned optimistic actions.
