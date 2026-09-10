# Unified problem definition

## Registered finite environment–action model

Let \(\mathcal E\) be a preregistered finite set of build environments. An environment \(E\in\mathcal E\) is a serialized index together with the implementation, build configuration, input permutation, seed when meaningful, toolchain, and search semantics needed to replay it. Each implementation has its own finite native action set \(\mathcal A_E\). A query \(q\sim P_Q\) is drawn from a frozen query distribution.

For action \(a\in\mathcal A_E\), define the absolute endpoint-aware failure indicator

\[
Z_E(q,a)=\mathbf 1\{\text{the returned result fails the registered quality target}\},
\]

and implementation-internal cost \(C_E(q,a)\). The minimum observed safe budget is

\[
B_E(q)=\min\{a\in\mathcal A_E:Z_E(q,a)=0\},
\]

with \(B_E(q)=\bot\) when no registered action succeeds. The symbol \(\bot\) is categorical and is never imputed as a larger numeric budget.

A policy observes a transcript \(T\) and possibly query-side observables and returns \(\pi(T,q)\in\mathcal A_E\cup\{\mathrm{abstain}\}\). Its absolute failure risk is

\[
r_E(\pi)=\Pr_{q\sim P_Q}\!\left[Z_E(q,\pi(T,q))=1\right].
\]

The registered risk tolerance is \(\delta\), the certification error probability is \(\alpha\), and \(\gamma>0\) denotes a safety margin below \(\delta\). The rejection event is \(R\), and \(a_f\) is a fallback only when it has an independent safety justification under the same target and failure semantics. Otherwise the only valid output is abstention.

## Status semantics

- **Registered-grid unresolved:** no action in the finite registered grid succeeds; recorded as \(B_E(q)=\bot\).
- **True endpoint infeasible:** no action in the full admissible action space can meet the quality target. The current finite grids do not establish this state.
- **Right-censored:** success may occur beyond the largest registered action, but it was not observed.
- **Unsafe under transported action:** a source-chosen action is executed on the target and \(Z_{E_t}(q,a_s)=1\).
- **Abstention:** the procedure refuses to label any action safe; it is not an unsafe acceptance and is accounted for separately.

Because current records cannot always separate true endpoint infeasibility from grid right-censoring, the paper uses “registered-grid unresolved” unless stronger evidence exists.

## Implementation instances

| Implementation | Registered build environment | Native action | Interpretation boundary |
|---|---|---|---|
| hnswlib HNSW | build seed × input order, with other parameters fixed | `efSearch` | candidate-list/search-control parameter; not an expansion or NDC cap |
| Faiss HNSW | registered input permutation, with other parameters fixed | `efSearch` | implementation-specific; numerical values are not compared to hnswlib |
| DiskANN3/Vamana-style | registered input permutation, fixed build options | `l_value` with `beam_width=1` | search-list size; not equal to HNSW `efSearch` |

The common scientific object is the finite action-response relation \((a,Z_E,C_E)\), not equality of raw parameter values, graph layers, edge semantics, or NDC units across implementations.

## ICBA name audit

The verified source artifacts repeatedly use the acronym **ICBA** but do not contain one stable, formally adopted expansion. To avoid inventing provenance, the paper retains **ICBA** as the method name and defines it descriptively as a *certified audit of index-build budget portability*. This phrase is a description, not a retroactive acronym expansion. Any future expansion must be introduced as an explicit naming change.

## Scope

All positive guarantees are for a named target, a frozen finite action family, and a declared query law. The empirical conclusions cover registered builds in two frozen datasets and three registered implementations spanning HNSW and Vamana-style construction. They do not certify unseen builds, shifted queries, arbitrary implementations, or open-world recovery.
