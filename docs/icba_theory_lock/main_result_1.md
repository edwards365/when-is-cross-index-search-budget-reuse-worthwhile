# Main Result I: Information-Constrained Adaptation and Zero-Tax Characterization

## Theorem I-A — Safe Envelope Optimality (`FORMALLY_PROVED`)

Let `X` be a source-side summary and `B` the target stable sufficient budget. Define `g*(x)=ess sup(B|X=x)` with respect to a regular conditional distribution, or equivalently as the least `sigma(X)`-measurable almost-sure upper bound of `B`. Then `g*(X)>=B` almost surely. If another `sigma(X)`-measurable allocation `g(X)` is safe, the defining least-upper-bound property gives `g(X)>=g*(X)` almost surely. Therefore any action-monotone cost satisfies `C(g(X))>=C(g*(X))` almost surely and hence in expectation when integrable.

If cost has flat segments, allocations larger than `g*` can tie its cost, so action minimizers need not be unique. If cost is strictly increasing on the admissible budget support, any cost-optimal safe action equals `g*` almost surely; otherwise a positive-probability strict increase would strictly raise expected cost.

In a finite empirical information cell, the essential supremum is the maximum observed target budget. Empty/zero-probability cells impose no almost-sure constraint. Ties in `X` are one information cell and must not be split after outcomes are observed.

## Theorem I-B — Zero Information-Tax Characterization (`FORMALLY_PROVED UNDER EXPLICIT CONDITIONS`)

Assume `C` is strictly increasing on the budget support and both costs are integrable. Define

`T_info = E[C(g*(X))-C(B)]`.

The integrand is nonnegative. If `B` is `sigma(X)`-measurable, then `B` itself is a safe `sigma(X)`-measurable allocation and minimality gives `g*(X)=B` almost surely, hence zero tax. Conversely, zero expectation of a nonnegative integrable variable implies `C(g*(X))=C(B)` almost surely; strict increase implies `g*(X)=B` almost surely, so `B` is `sigma(X)`-measurable. Thus zero tax is equivalent to lossless target-demand measurability from the source summary under these conditions.

The converse can fail for non-strict costs: different budgets on one flat cost segment can have zero tax without demand measurability. In continuous-summary populations, the statement is modulo null sets and conditional essential suprema, not literal maxima of singleton observations. In the finite sample, zero tax is equivalent to constant target demand inside every observed source-summary cell when cost is strictly increasing and there is no censoring ambiguity.

## Theorem I-C — Information Refinement (`FORMALLY_PROVED; STANDARD DECISION-THEORY INSTANCE`)

If `sigma(X1)` is contained in `sigma(X2)`, every `X1`-measurable safe policy is also `X2`-measurable. Optimization over the larger feasible class therefore gives `V0(X2)<=V0(X1)`. This is an ICBA specialization of standard value-of-information ordering and is not claimed as a new generic principle.

## Frozen empirical protocol

The source summary is the already frozen source stable budget on the 750-query train-side `confirm` partition used by the preceding unified analysis. This is not validation-dev or formal-test. No continuous-feature binning is introduced. An aliasing group is a source-budget level containing more than one target budget. Exact zero tax requires zero empirical clipped NDC difference and no right censoring. Before computation, approximate zero was fixed at information tax no greater than 1% of fixed NDC, again excluding censored pairs. Results are reported separately by implementation, dataset, and same-order versus cross-order category. Censored clipped costs are lower bounds and cannot establish population zero tax.
