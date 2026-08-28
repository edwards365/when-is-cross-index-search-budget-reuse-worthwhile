# Hidden-Environment Safe Budgeting

## Statistical object

An environment `theta` specifies a query law `P_theta`, an ordered finite budget set `B`, a safety-loss process `L_theta(x,b)`, a cost process `C_theta(x,b)`, and an observation channel `Q_theta^j` for information lane `Zj`. A deployment strategy may randomize and maps `(x,Z_theta^(k),U)` to a budget in `B` or to a fallback action. Randomization `U` is independent of the environment and queries. The fallback has an explicit safety and cost pair; it is not identified with the largest budget.

For action `a`, environment-conditional query risk and cost are

`R_theta(pi)=Pr[L_theta(X,pi(X,Z,U))>0 | theta]` and `K_theta(pi)=E[C_theta(X,pi(X,Z,U)) | theta]`.

When a genuine environment law `Pi` is assumed, build reliability is

`Pr_{theta~Pi}(R_theta(pi)>delta_q) <= delta_b`.

This statement is undefined—not merely unproved—when the observed builds are fixed design and no sampling law `Pi` is posited.

## Information lanes

- `Z0`: deployment metadata known without target outcomes, such as dataset, implementation, declared construction history and retained seed.
- `Z1`: unlabeled target-runtime observations obtainable online or during reconstruction, such as work counters or returned-distance summaries. Availability and semantic equivalence must be audited per implementation.
- `Z2`: labeled target sentinels requiring target ground truth. Probe count `k` controls only uncertainty carried by this channel.
- `Z3`: per-query source Oracle derived from complete labeled source budget curves. This is an analysis upper bound, not a deployable observation.

All results name the lane. A guarantee established using `Z2` or `Z3` is not transferred to `Z0` or `Z1` by omission.

## Four scopes

1. **Finite closed world:** `theta` lies in an enumerated candidate set; coverage is conditional on that support and its stored policies.
2. **Fixed-design build family:** conclusions concern exactly the observed builds. Query sampling can be probabilistic while build generalization remains descriptive.
3. **Hierarchical random environment:** builds are exchangeable or iid from a stated `Pi`; both query and build uncertainty are inferential.
4. **Arbitrary open world:** no support, smoothness or observation-response relation is assumed. Only minimax statements over the declared environment class are valid.

Distribution-free refers to a named sampling level. Query-level distribution-free coverage inside observed builds does not imply distribution-free coverage over unseen builds.

## Ordered actions and safety boundary

If loss is monotone in budget, define the minimal safe action `b*_theta(x)=min{b: L_theta(x,b)=0}` when it exists. Right censoring means `b*` exceeds the observed grid or is unidentified; endpoint infeasibility means no practical action in the grid satisfies the population or certified criterion. Neither state may be imputed as the maximum observed budget without an explicit conservative convention.

For two environments, a disagreement set is `A={x: b*_{theta0}(x) and b*_{theta1}(x) exist and differ by at least Delta}`. Its mass `rho` and the information-channel distance between environments drive the safety–conservatism lower bound. When loss is non-monotone, the primitive object is the safe-action set rather than `b*`, and any theorem must be restated in terms of incompatible safe sets.

## Guarantees and costs

- A **conditional guarantee** fixes the observed environment or history.
- A **marginal guarantee** averages over a stated sampling law.
- A **minimax guarantee** controls the worst member of a declared class.
- An **average-case guarantee** depends on `Pi` and cannot certify arbitrary open-world environments.

Total cost includes selected search cost, target-probe acquisition, fingerprint instrumentation, fallback, and amortization over the future workload. Safety, conservatism and fallback are separate coordinates unless a preregistered scalarization is supplied.

## Empirical instantiation

The frozen Graph-ANNS evidence is a fixed-design family of 81 graphs and 972,000 query-budget records. The six feasible SIFT/Arxiv dataset-by-implementation cells contain nine builds each. The 648 directed comparisons are dependent contrasts, not 648 environment draws. The current stage therefore supports fixed-family empirical claims and model-explicit theory; it does not itself identify a population law over graph builds.

## Integrity limitation

Continuation is conditional on the current 59/59 Full Seal artifact hashes and native seal test. The inherited 123-entry micro-closure list is not Git-reproducible (111 matches, eight mismatches, four absent cache files). This limitation remains visible in every final claim.
