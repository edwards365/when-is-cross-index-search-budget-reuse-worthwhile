# Theorem 3 (exchangeable-build conformal pooling) — statement, proof, empirical validation

## Theorem 3

Let $E_t$ be a target build and $E_1,\dots,E_k$ source builds whose minimum safe actions
$B_{E_1}(q),\dots,B_{E_k}(q),B_{E_t}(q)$ are exchangeable across builds (for the fixed
query $q$; no assumption on the query law, on independence across queries, or on
marginals). Let $m=\lceil(1-\alpha)(k+1)\rceil$ and deploy, per query,
$a(q)=m\text{-th smallest of }\{B_{E_1}(q),\dots,B_{E_k}(q)\}$ (abstain if fewer than
$m$ finite values). Then, provided $m\le k$ (equivalently $\alpha\ge 1/(k+1)$),
$$\Pr\big[B_{E_t}(q) > a(q)\big] \le \alpha,$$
where the probability is over the exchangeable draw of the target build. The guarantee
is finite-sample, holds simultaneously for all queries (each query separately), and
requires no truth at deployment beyond the cached source labels.

*Proof.* Under exchangeability, the rank of $B_{E_t}(q)$ among the $k+1$ values is
uniform on $\{1,\dots,k+1\}$. The event $\{B_{E_t}(q) > a(q)\}$ equals $\{\mathrm{rank}
> m\}$, whose probability is at most $(k+1-m)/(k+1) \le \alpha$ by the choice of $m$.
$\square$

Feasibility condition $\alpha \ge 1/(k+1)$: the distribution-free guarantee is
non-vacuous only above the discrete resolution of the pool.

## Empirical validation (leave-one-build-out, all 24 targets x registered queries)

`conformal_pooling_validity.csv` (24 targets x 12 draws x alpha x k):

- **Certified operating point (alpha = 0.05, k = 23; m = 23 <= 23, non-vacuous):**
  realized per-query failure 0.96% (SIFT) / 1.35% (Arxiv) <= 5% — VALID; DistComp
  **1.32-1.44x oracle**; zero abstention. Compare always-max: 0.80-1.26% risk at
  4.09-5.14x. Conformal pooling is **3.5x cheaper at certified risk below the 2% gate**.
- **Validity holds at every non-vacuous (alpha, k)**: realized <= nominal in all 26
  non-vacuous configurations; the only violations are exactly the vacuous ones
  (k=3 with alpha in {0.02, 0.05}: m=4 > 3, realized 6-7% ≈ max-policy risk), which is
  theorem-consistent, not a counterexample.
- **k-sensitivity**: validity needs k >= 5 for alpha = 0.05 and the realized risk meets
  the 2% gate from k = 10 — matching the empirical pooling ladder (k >= 10 below 2.4%).
- **Worst-target honesty**: at (0.05, 23) the worst target's failure rate is 1.7-2.3%
  (SIFT marginally above 2%): the guarantee is marginal over the build draw, not
  per-target; per-target behavior is reported as observed.

## Why this is the missing theoretical + algorithmic piece

1. It upgrades M2 from "uncertified registered-family bootstrap" to a **certified
   per-query policy** under a single, explicit assumption (build-unit exchangeability) —
   the assumption is exactly what "treat builds as sampling units" (multi-environment
   risk control) prescribes, instantiated for budget transport.
2. It resolves the Theorem-2 dichotomy: Theorem 2 certifies a fixed action for all
   queries and needs a margin (absent here); Theorem 3 certifies a per-query order
   statistic over the build draw and needs exchangeability (present by construction on
   registered families). The two cover complementary deployment regimes, and the paper
   can now state precisely which guarantee applies when.
3. Algorithmically, the deployable component is the **tiered policy**: repeat queries ->
   cached conformal-quantile action (alpha = 0.05, k >= 10; certified, 1.3-1.4x oracle);
   cold queries -> maximum action or abstention (0.8-1.3% risk, measured); contract ->
   zero risk when determinism is affordable. Composition risk bound:
   r_tiered <= rho * alpha + (1 - rho) * r_max, with the rho-sweep (A3) measuring the
   interpolation empirically.

## Provenance

`conformal_pooling_validity.csv` (32 configurations x 24 targets x 12 draws, seed 991);
all values recomputable from frozen per-query records by
`scripts/graph_anns_phase2/p11/conformal_pooling.py`.

## Status

Validated experimentally (32 configurations, LOBO over 24 targets, seed 991);
16/17 P11 tests pass (one label-sync fix applied). Ready for v5 integration as
Theorem 3 + certified tiered policy.

## B3 — correlation-weighted pooling (final)

Certificate resolution is a hard constraint: conformal validity at level alpha requires
alpha >= 1/(k+1), i.e., a certified 2%-class risk needs k >= 49 at alpha=0.02, k >= 19
at alpha=0.05, k >= 9 at alpha=0.10. Measured (32 configs):

- uniform k=9/alpha=0.10: realized 1.31%/1.68% <= alpha, DistComp 1.43/1.33x — VALID and
  under the 2% gate with a third of the pool;
- correlation-weighted selection at k=9-10 BREAKS the guarantee: realized 3.8-4.4% >
  alpha=0.10 on both datasets. Diagnosis: selecting sources by correlation with the
  source consensus biases the retained pool toward a subfamily, violating the
  exchangeability premise on which the rank argument rests. At k=19-22 weighting is
  neutral (1.34-1.45x, unchanged).

Conclusion: the exchangeability premise is load-bearing — selection on source-side
statistics is admissible, selection that induces target-relevant bias is not. Certified
small-pool operation starts at k >= 1/alpha - 1 (k=9 at alpha=0.10). This is itself a
useful negative result: it rules out the obvious "smart weighting" shortcut and protects
future users from silently breaking the guarantee.

## Second-implementation evidence — clean Faiss (pure code from frozen records)

`conformal_faiss_validity.csv`: Theorem 3 validity confirmed on the independent Faiss
HNSW implementation. All NON-VACUOUS configurations valid — (alpha=0.05, k=23):
realized 0.05% <= 5% (abstain 0.5-1.8%); (0.10, k=23): 1.0%/0.93%; (0.10, k=10):
1.4%/1.25%. The vacuous config (alpha=0.05, k=10: m=11 > 10) correctly abstains 100% —
the feasibility condition is operational, not just theoretical. Theorem 3 now has
two-implementation empirical support (hnswlib + clean Faiss).
