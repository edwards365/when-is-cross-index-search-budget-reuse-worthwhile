# Phase 2 Recall@10=.95 Data-Refresh Protocol

Phase 2 reuses the already hash-audited 5% mixed delete/insert memberships and ten rebuilt indexes per dataset, but it does not reuse the earlier Recall@10=.90 result labels. The primary question is whether a TCP budget derived from the old snapshot remains deployably safe and useful after refresh plus rebuild under the unified `Recall@10 >= .95` estimand.

The new query roles are selected from rows never used by the earlier refresh studies. Each dataset contributes 500 selection, 500 certification, and 1,000 cold-evaluation queries. Content hashes and pairwise intersections must be recorded before any Recall@10=.95 result is opened. Selection may instantiate the preregistered target-recalibration comparator; certification alone decides acceptance or fixed-safe fallback; cold evaluation is read only after that decision is frozen.

The primary experiment is the 5% refresh. The existing 1% and 10% memberships are retained only for preregistered sensitivity analysis after the 5% cell is sealed. Ten target builds exceed the six-build minimum in the execution plan. Published external adaptive methods are not forced into this phase because neither DARTH nor Ada-ef passed Phase 1's registered cross-rebuild safety integration gate.

The implementation must record implementation-native action, Recall@10, distance computations, latency, fallback, truth cost, certification cost, and rebuild cost. Statistical inference resamples target builds as the outer unit and queries within build as the inner unit, with 5,000 repetitions and seed 991. Evaluation queries are never treated as independent builds.
