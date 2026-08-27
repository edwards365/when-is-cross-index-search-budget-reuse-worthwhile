# Finite-Environment ICBA Lower Bound

## Loss normalization

Let the ordered action grid be embedded in `[0,1]` by dividing budget differences by the full observed budget span. On a common visible state space, write `b_j(z)` for environment `j`'s deterministic normalized minimum sufficient budget at aligned visible state `z`, and let a policy choose a possibly randomized action `a(Z)`. Define

`ell_j(a,z) = lambda (b_j(z)-a)_+ + (a-b_j(z))_+`,

where the first term is under-budget loss and the second is excess-budget loss. This surrogate keeps risk and over-allocation in a common budget unit. It is not Recall loss and does not silently convert marginal risk into pointwise safety.

## T-M1: overlap-separation lower bound

Consider two environments with visible-state laws `P_0^Z` and `P_1^Z` on the same measurable space. Let `A_Delta={z:b_1(z)-b_0(z)>=Delta}` be measurable and assume both environments assign it probability at least `rho`. For every deterministic or randomized `Z`-measurable policy,

`inf_pi sup_j E_j ell_j(pi(Z),U) >= (min{lambda,1} Delta / 2) [rho-TV(P_0^Z,P_1^Z)]_+.`

The lower bound is in normalized budget units. It is strictly positive whenever `Delta>0`, `rho>TV`, and `lambda>0`.

### Proof

Use the common part `mu=P_0^Z wedge P_1^Z`. Its mass on the aligned set is at least `[rho-TV]_+`: the average mass of the set is at least `rho`, while the total variation can remove at most `TV` from common overlap. At every aligned observation and for every action, including every realized action of a randomized policy,

`(a-b_0)_+ + lambda(b_1-a)_+ >= min{lambda,1}(b_1-b_0) >= min{lambda,1}Delta`.

Integrating against `mu` lower-bounds the sum of the two environment risks. Dividing by two lower-bounds their average, and their maximum is at least their average. Randomization cannot improve the pointwise inequality, so the same result holds after integrating over the policy's auxiliary random seed.

## Sharpness and zero cases

- With a single fully ambiguous type, `TV=0`, mass `rho=1`, and budgets separated by `Delta`, choosing either endpoint attains the bound when the adversary mixes the environments equally; thus the factor `1/2` is unavoidable for this symmetric reduction.
- `Delta=0` gives zero because no budget conflict exists.
- `rho=0` gives zero because the separated set has no mass.
- `TV=1` gives zero because the environment is perfectly identifiable from `Z`.
- If `rho<=TV`, the stated summary statistics alone permit all separated mass to lie outside the common part, so no positive bound follows without a stronger localized-overlap assumption.

## Assumptions and boundaries

The theorem does not require quality monotonicity after the sufficient-budget labels have been validly defined, but stable sufficient budgets themselves require the frozen-tail convention. Right-censored labels are not point identified and cannot be inserted as if ef=512 were sufficient; the theorem may be applied only to uncensored pairs or with a separately proved lower interval for `Delta`. The deterministic response functions `b_j(z)` are a restricted aligned-response class. If target budget is not determined by visible `z`, or environments do not share this aligned state space, a joint coupling/conditional-response formulation is required; marginal `P_j^Z` and unaligned budget histograms alone are insufficient.

This is a quantitative decision-theoretic lower bound, not a renaming of empirical portability tax: the empirical tax can instantiate `rho`, `Delta`, and overlap, whereas the theorem applies to every policy measurable in the stated information channel.

## T-M2 status

A finite-`K` pairwise corollary follows immediately by selecting any pair of environments: the minimax loss over all `K` environments is at least the largest valid two-environment lower bound over preregistered aligned pairs. A genuinely sharper Fano or packing result is not yet proved and is labeled `PROOF_SKETCH_NOT_MAIN_THEOREM`.

## Mapping to locked ICBA results

- Earlier information-order results become the qualitative statement that refining `Z` cannot increase optimal loss; T-M1 supplies a positive quantitative obstruction under overlap and budget separation.
- The exact barrier tax is a finite-table decomposition of excess allocation after aliasing has forced a safe envelope; it is an empirical instance, not the minimax proof.
- The previous collision lower bound corresponds to the `TV=0` special case.
- Restricted T4 remains a Graph-ANNS combinatorial proposition and is not promoted to a general theorem.
- Certification, target-information value and prefix recovery results remain separate upper-bound or execution-interface components.

Gate G1 remains pending exhaustive counterexample tests over the preregistered finite grids.
