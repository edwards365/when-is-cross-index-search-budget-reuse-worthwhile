# Theory applicability report

## Unified model

For a registered implementation define

\[
E=(X,\mathcal Q,A,\Xi,\mathcal A,Z,C),\qquad G_\xi=A(X,\xi),
\]

where `Xi` and `A` are finite, `Z` is endpoint-aware recall failure, and `C` is an implementation-local cost vector. For each query,

\[
B_{G_\xi}(q)=\min\{a\in\mathcal A:Z_{G_\xi}(q,a)=0\},
\]

with `B=bottom` when the set is empty. `bottom` is not numeric and is never imputed to the largest action.

## Applicability results

### T-V1 — algorithm-independent instantiation

For every finite registered `Xi` and `A`, measurable `Z` and `C` induce a finite table indexed by `(xi,q,a)`. Budget response, source-to-target transport events and fixed-target risks are measurable functions of that table. Nothing in the construction uses HNSW layers. Status: `FORMAL_PROOF_COMPLETE / ABSTRACTION_OR_DEFINITION`.

### T-V2 — no raw parameter equivalence

Without an explicit coupling assumption there is no universal map from HNSW `efSearch` to DiskANN `l_value` that preserves both `Z` and `C`. A two-action counterexample assigns equal HNSW outcomes but swaps Vamana risks or costs across two allowed worlds; any fixed map fails in one world. Status: `FORMAL_PROOF_COMPLETE / RESTRICTED_DOMAIN_PROPOSITION`.

### T-V3 — complete-pair symmetry

On jointly finite `B_s,B_t`, every unordered pair with unequal budgets contributes exactly one `B_s<B_t` direction and one `B_s>B_t` direction when both directions are included. Hence

\[
P(under)=P(over)=\tfrac12P(B_s\ne B_t)
\]

for the uniform complete directed-pair design. It fails under censoring, missing reverse directions, or a different weighting measure. Status: `FORMAL_PROOF_COMPLETE / RESTRICTED_DOMAIN_PROPOSITION`.

### T-V4 — asymmetric transport estimand

Freeze disjoint source and target build sets before query outcomes. The main estimand averages only over `S x T`; reverse pairs are not inserted. This removes the algebraic symmetry but does not by itself establish causal or open-world transport. Status: `FORMAL_PROOF_COMPLETE / PROTOCOL_DEFINITION`.

### T-V5 — data-by-operator interaction

Let `theta[d,o]` be the preregistered effect statistic for dataset `d` and operator `o`. The external-validity target is an interaction table, not equality of effects. At least one non-HNSW operator with a passed detection and materiality gate supports existence beyond HNSW; two datasets support the strong label. Status: `FORMAL_PROOF_COMPLETE / RESTRICTED_DOMAIN_PROPOSITION`.

### T-V6 — transport-event partition

The originally requested label set is false as an exhaustive mutually exclusive partition under nonmonotone raw response. The corrected raw-minimum partition is defined in the proof appendix. `RAW_NONMONOTONE` is an overlay. Status: `FORMAL_PROOF_RESTRICTED`; original form `COUNTEREXAMPLE_FOUND`, corrected form complete.

### T-V7 — structural similarity is insufficient

Any finite list of graph summaries is non-injective. Two graphs can share those summaries while differing on a query-relevant edge or neighbor order, producing different greedy trajectories and minimal safe actions. Status: `FORMAL_PROOF_COMPLETE / RESTRICTED_DOMAIN_PROPOSITION`.

### T-V8 — claim hierarchy

Existence on registered units, conditional universality over stated support, family-level replication, and Graph-ANNS universality are different quantifier statements. The pilot can at most establish family-level replication within its registered support. Status: `FORMAL_PROOF_COMPLETE / ABSTRACTION_OR_DEFINITION`.

## Transferable and nontransferable theory

Transferable: finite action definitions, `bottom` censoring, fixed-target binomial/query risk, asymmetric source/target design, cost-tax accounting, and data-by-operator effect tables.

Not transferable without new proof: any HNSW-layer argument, efSearch numerical thresholds, HNSW entry/degree semantics, cross-implementation NDC equality, event nesting, monotonic raw recall, fixed-safe endpoint, or open-world guarantees.
