# Main Result II: Exact Safe Monotone Portability Tax and Barrier Decomposition

## Theorem II-A — Zero monotone-tax characterization (`FORMALLY_PROVED UNDER EXPLICIT CONDITIONS`)

Let source and target demands be `X=B_s` and `Y=B_t`. Among nondecreasing safe mappings, the pointwise-minimal action at source level `x` is the prefix essential supremum `f*(x)=ess sup{Y:X<=x}` (with tied source levels treated as one cell). Under integrability and a cost strictly increasing on the budget support, `T_mono=E[C(f*(X))-C(Y)]` is zero if and only if `Y=f(X)` almost surely for some nondecreasing measurable `f`. Sufficiency is immediate. For necessity, the nonnegative integrand has zero expectation only if strict cost equality and hence action equality holds almost surely; `f*` itself supplies the required monotone function.

With flat cost segments, distinct actions can have equal cost and the converse fails. With right censoring, an observed clipped zero cannot establish zero population tax. On a finite grid, ties with distinct target demands rule out zero action tax even when there is no strict rank inversion between distinct source levels.

## Theorem II-B — Exact barrier decomposition (`FORMALLY_PROVED`)

For ordered actions `e_1<...<e_L`, let query-specific monotone costs be `C_q(e_l)` and increments `Delta C_{q,l}=C_q(e_l)-C_q(e_{l-1})`. For any observed target action `Y_q=e_j` and safe monotone action `M_q=e_k>=Y_q`, telescoping gives

`C_q(M_q)-C_q(Y_q)=sum_l Delta C_{q,l} 1{Y_q<e_l<=M_q}`.

Taking a weighted finite sum or expectation yields the exact total tax. The statement permits nonlinear monotone costs, flat increments, and nonuniform query weights. Linear budget cost is the special case where increments are budget gaps; native NDC uses each query's measured incremental NDC. This equality explains why inversion rate alone cannot determine tax: tax also depends on which barriers are crossed, their cost increments, and the mass forced across them.

## Boundary examples

- **No strict inversion but positive tax:** tied source demands with different target demands force the lower target-demand query up to the tied-cell maximum.
- **High inversion, small tax:** many reversals confined to adjacent actions separated by a nearly flat cost increment.
- **Rare inversion, large tax:** one incompatible pair crossing a very large nonlinear cost jump can dominate total tax.

## T4 final disposition

The inversion matching result is retained as `PROVED_UNDER_EXPLICIT_CONDITIONS_RESTRICTED_PROPOSITION`: finite uncensored grid, additive linear budget-gap weights, and vertex-disjoint inversion matching. It is a corollary-style lower bound supporting the exact barrier theorem, not a coequal main theorem. Existing exhaustive checks and new fixed-seed property tests are computational validation only. No general nonlinear-NDC matching theorem is claimed.

## Empirical computation

The frozen 750-query train-side confirm split is used for all 648 directed graph pairs. For observed target demands, query-specific NDC increments telescope exactly to direct monotone-minus-target cost. Censored queries are excluded from equality totals and reported separately; clipping is not used to claim safe above-grid cost. Pair totals, per-level contributions, top-1% trimmed means, same/cross-order categories, and restricted matching diagnostics are saved independently.
