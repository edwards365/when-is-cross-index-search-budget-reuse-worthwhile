# Stage I discrete-risk semantic report

Recall@10 is discrete. The registered `tau=0.95` and `tau=0.99` events are checked at the per-query hit-count level and are identical for both hnswlib and historical Faiss cells. `h=10` is the frozen primary estimand; `h=9` is the tau=0.90 sensitivity; `h=8` is post-lock sensitivity. Vamana pair-level events do not contain per-query hit counts, so h=8/9/10 are explicitly NOT_ESTIMABLE there.

Stage I label: **DISCRETE_WORKPOINT_EFFECT_CONDITIONAL**. The label is conditional because the Vamana hit-count sensitivity cannot be reconstructed without inventing per-query information.
