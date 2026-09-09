# Proof appendix

## A. T-V1

Fix finite sets `Xi={xi_1,...,xi_m}` and `A={a_1,...,a_L}`. For every `xi,q,a`, measurability of `Z` and `C` makes the response array measurable. The minimum over a finite ordered set is measurable on the success event; adjoin an isolated symbol `bottom` otherwise. Every transport category is a finite Boolean combination of measurable comparisons and failure events. Fixed-target risk is the expectation of an indicator. This proves instantiation and shows the result is a definition-level finite construction.

## B. T-V2 counterexample

Let each implementation have actions `{1,2}` and one query. In world W0, HNSW outcomes are `(Z,C)=((1,0),(2,1))` in shorthand risk/cost order, while Vamana action 1 is safe/cheap and action 2 safe/expensive. In W1 keep all HNSW observations fixed and swap Vamana action costs, or make action 1 unsafe and action 2 safe. A deterministic map based only on the HNSW scalar is unchanged across worlds and therefore cannot preserve both risk and cost in both. An equivalence needs extra empirical calibration and is never semantic identity.

## C. T-V3

Let `U` be the set of unordered build pairs with finite unequal minimal safe budgets for a fixed query. Map each `{i,j}` to the two ordered pairs `(i,j)` and `(j,i)`. If `B_i<B_j`, the first contributes one under direction and the reverse one over direction. Summing indicators over `U` gives equal counts and two unequal directions per pair. Division by `2|U|` yields the identity. Equal budgets contribute neither. Censored pairs are outside the theorem.

Counterexamples: retaining only `(i,j)` removes the reverse match; assigning `bottom` the largest numeric value manufactures false comparisons; weighting source builds unequally destroys equality. Raw nonmonotonicity also means budget-order categories alone do not determine transferred-action safety.

## D. T-V6 corrected partition

For source action `a_s=B_s` and target raw minimum `B_t`:

- if both are `bottom`: `BOTH_RIGHT_CENSORED`;
- if only source is `bottom`: `SOURCE_ONLY_RIGHT_CENSORED`;
- if only target is `bottom`: `TARGET_ONLY_RIGHT_CENSORED`;
- if both finite and `a_s<B_t`: `UNDER_BUDGET_UNSAFE` (safety below the raw minimum is impossible);
- if both finite and `a_s=B_t`: `EXACT_BUDGET_SAFE`;
- if both finite, `a_s>B_t` and `Z_t(q,a_s)=0`: `OVER_BUDGET_SAFE`;
- if both finite, `a_s>B_t` and `Z_t(q,a_s)=1`: `OVER_BUDGET_UNSAFE`.

The cases are disjoint and exhaustive by censoring state, trichotomy, and the binary value of `Z`. The proposed `UNDER_BUDGET_OBSERVED_SAFE` is empty under the raw-minimum definition. It is meaningful only relative to a different reference (for example, a monotone-envelope threshold) and must not be mixed with raw `B`. `RAW_NONMONOTONE=1` iff some `a<a'` has `Z(a)=0,Z(a')=1`; it can co-occur with several primary classes and is therefore an overlay.

## E. T-V7 counterexample

Take a directed regular graph and two equal-distance candidate neighbors whose IDs determine tie order. Swap the query-relevant outgoing edges between the tied vertices while preserving every listed unlabeled summary: edge count/Jaccard against a symmetrically relabeled reference, degree multiset, reachability, diameter, prune keep rate and medoid distance. A deterministic tie rule now enters different basins; one graph reaches the true neighbor within list size 2 and the other requires list size 3. Hence equal summaries do not entail equal `B_G(q)`.

## F. Fixed-target boundary

All probabilities are conditional on the named target build(s) and registered query distribution. Replacing a target build by a future random build changes the outer probability space. A query-level confidence interval contains no independent outer-build samples and therefore cannot imply an outer-build statement.
