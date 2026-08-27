# ICBA paper theory v2

## 1. Problem definition

An ANN execution environment I maps query q and ordered budget e to quality and cost. Stable target demand is the least frozen action whose full upper grid tail reaches Recall@10 0.9. A demand beyond the maximum is right-censored. Policies are compared by the information they observe and by pointwise, marginal, conditional, empirical, or certified risk—never by an unnamed mixture.

## 2. Information-constrained adaptation

A source-summary policy acts on `X_s=phi(q,I_s)`. Its minimum zero-risk action is the conditional essential supremum of target demand. This identifies the exact information loss caused when multiple target demands share one source summary.

## 3. Zero-tax characterization

Under strict increasing integrable cost, information tax is zero if and only if target demand is measurable from the source summary. Flat costs weaken the converse. In 648 frozen pairs, only 36 are exact and ≤1%-approximate zero-tax pairs; 594 contain empirical source-summary aliasing.

## 4. Exact monotone barrier decomposition

For source stable budget, the safe monotone action is the prefix maximum of tied-cell target maxima. Its exact query cost is the sum of query-specific incremental NDC at every barrier forced between target and allocated action. This separates aliasing, order, barrier mass, and cost jump. The older inversion matching result is demoted to a restricted proposition rather than presented as the center of the paper.

## 5. Risk-matched adaptation

Marginal delta-risk becomes a finite allocation problem across source-information cells. Censored units are mandatory failures unless above-grid actions are modeled. The frozen risk table contains 1,632 exact cells, 424 cells feasible with mandatory censored failures, and 536 infeasible cells.

## 6. Certification-aware deployment

Certification is random. A frozen policy deploys only when its independent calibration sample passes the exact multiplicity-adjusted binomial test; otherwise it fails closed to a fixed policy. Expected cost combines certification probability, online/fallback cost, and amortized calibration. GloVe's 16 policies had 32–181 failures out of 256, including 32 for zero early stopping, so all failed even as single candidates; this is empirical unsafety, not chiefly Bonferroni power.

## 7. Cost-adjusted sequential information

Target-native state lies outside source-only lower bounds. Yet the work needed to acquire state must be added. Frozen perfect-label trace Oracles show large statistical headroom, but GloVe has roughly 28%–30% no-safe-checkpoint censoring and measured controller latency is absent. These are method-design upper bounds, not performance claims.

## 8. Empirical contact

The contact matrix comprises 81 builds, 972,000 records, and 648 directed pairs across hnswlib, Faiss HNSW, and Vamana. Build-pair cluster sensitivity preserves positive cross-order tax directions, while leave-one-history changes can be large. This supports a mechanism boundary, not 648 independent build replications.

## 9. Scope and limitations

The mathematical framework is broader than the evidence. Actionable empirical effects remain hnswlib-specific; NDC is implementation-local; T4 is restricted; censoring can leave conservative cost unbounded; no validation-dev/formal-test evidence exists.

## 10. Theory-to-method interface

A future method must obtain cheap, resumable target state that refines source aliases, retain a risk-valid fallback, account for complete cost, and freeze/certify one complete policy. Theory is locked for method derivation, but a separate preregistration is required before execution.
