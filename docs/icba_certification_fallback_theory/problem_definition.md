# ICBA certification--fallback positive theory: problem definition

## Frozen boundary and input audit

- Requested server repository `/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs` and requested server worktree path are not mounted in this execution environment. No server directory was overwritten or deleted.
- The private GitHub repository was resolved read-only before mutation. Commit `97ca42a120fff015885bba509e8aa90178aabfa2` and theory reference `4e728d437038816a7706e9cb802d19274aa691b9` both exist.
- Remote branch `exp/icba_certification_fallback_theory` did not exist and was created from exactly `97ca42a120fff015885bba509e8aa90178aabfa2`. Local authoring is isolated under the conversation workspace.
- Available local disk at start: approximately 30 GiB. The process snapshot showed no active Faiss/HNSW/Vamana experiment, validation-dev, or formal-test job.
- The frozen active-observation input audit reports 36/36 tests, 61/61 current SHA entries, and 51/51 parent SHA entries verified. Because the frozen repository bytes are not mounted locally, this task verified the committed manifest and audit record but did not claim a new byte-for-byte replay of those 61 files.
- The inherited limitation remains `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123`: 111 matching tracked blobs, eight mismatched tracked CSVs, and four absent `__pycache__` entries. None is repaired here.
- No validation-dev or formal-test path, content, or API object was read. No graph was built, no model trained, no experimental result regenerated, and no frozen artifact modified.

## Probability spaces and fixed-target scope

Let `G` be a named target build. Conditional on `G`, business queries `Q` are distributed as `P_G`. The fixed-target probability space contains:

1. selection data `D_sel`;
2. certification data `D_cert=(Q_i,Y_i)_{i=1}^m`, independent of `D_sel` conditional on `G`;
3. any internal randomizer `U` used by the selection/control rule;
4. fresh business queries, independent of the evidence conditional on `G`.

Evaluation data are not measurable with respect to the deployment rule. They are used only after the method is frozen, and are not used anywhere in this theory closure.

An outer-build statement introduces a separate random variable `G~Pi`. Nothing in the fixed-target results supplies `Pi`, exchangeable builds, or support coverage. Therefore

`P_{D_sel,D_cert|G}{r_G(Pi_D)<=delta} >= 1-alpha`

does not imply either

`P_{G~Pi}{r_G(Pi_D)<=delta} >= 1-alpha`

or

`sup_G r_G(Pi_D)<=delta`.

## Ordered finite budgets and absolute safety

The budget grid is

`E={e_1<e_2<...<e_L}`.

A policy is a measurable map `pi:q -> e_l`. For a query and policy, let

`Z_abs,G(q,pi)=1{under-budget or endpoint-censored}`.

The phrase endpoint-censored includes both a record whose safe endpoint lies beyond the observed grid and a query with no verified practical safe endpoint. It is not converted into a success at `e_L`. The fixed-target risk is

`r_G(pi)=E_{Q~P_G}[Z_abs,G(Q,pi)]`.

Safety means `r_G(pi)<=delta`. The strict certification error budget is `alpha`: over the random evidence, the probability of deploying a policy with risk greater than `delta` is at most `alpha`.

Candidate policies are ordered by conservative budget:

`pi_1 preceq pi_2 preceq ... preceq pi_L`.

The ordered-certification results require the query-level assumption

`Z_{l+1}(q)<=Z_l(q)` for every query in the support of `P_G`.

Risk monotonicity alone is weaker and is not enough for the ordinal-variable/DKW reduction. Under pointwise nesting define the minimum successful rung

`S(q)=min{l:Z_l(q)=0}`,

with `S(q)=L+1` if every candidate is an absolute failure. Then

`Z_l(q)=1{S(q)>l}` and `r_l=P_G(S>l)`.

## Actions and information

- `Oracle action`: may use the complete target response and is a nondeployable comparator.
- `Observable action`: measurable with respect to source information, preregistered metadata, `D_sel`, `D_cert`, and an independent randomizer.
- `reuse`: retain the source policy family without target fitting.
- `recalibrate`: change a preregistered calibration/control parameter using target evidence.
- `retrain`: fit a target-specific policy using a separately priced training/profiling sample.
- `fallback`: use a separately justified safe policy, or abstain if no such policy exists.

A maximum observed budget is not a known-safe fallback when endpoint censoring is possible. The terminal policy `pi_fixed` may be called fixed-safe only when its own risk statement is supplied independently of the candidate certificate.

## Cost random variables

For a policy `pi` and a fresh business query, `C_G(Q,pi(Q),V)` is the random search cost, where `V` contains search-engine randomness. Define its fixed-target mean

`mu_G(pi)=E[C_G(Q,pi(Q),V)|G]`.

The selection rule returns a random candidate `Pi_S=S(D_sel,U)`. The certification rule returns `R in {0,1}`, with `R=1` meaning rejection. The deployed policy is

`Pi_D=(1-R)Pi_S+R pi_f`

as a policy-valued selector. Define the conditional fallback gap

`Delta C_f=E[mu_G(pi_f)-mu_G(Pi_S)|R=1,G]`.

This definition allows candidate cost and rejection to be dependent. Evidence cost contains truth acquisition, probes, and certificate computation:

`C_evidence=C_truth+C_probe+C_certificate`.

`C_control` contains per-business-query control, dispatch, and policy-inference overhead. All components must be converted to compatible per-query units. For workload `N`, the amortized evidence term is `C_evidence/N`.

Search cost, truth acquisition cost, training cost, and control cost are distinct. A training action can have a larger fixed cost and a smaller recurrent search cost.

## Mean and tail objectives

The primary accounting theorem is an expectation identity. The operational tail metric is separately

`q_.95(Pi_D)=inf{t:P(C_G(Q,Pi_D(Q),V)<=t)>=.95}`.

Quantiles are nonlinear: the p95 of a mixture is not the mixture of component p95 values, and no mean identity implies a p95 guarantee. A deployable decision must therefore pass both the fixed-target safety certificate and a separately preregistered tail gate.

## Baseline and oracle

Let `B` be one fixed strong baseline with mean cost `C_B`. Let `pi_star` be the target oracle minimizer in the same action class under the same hard safety semantics. Its headroom is

`G_oracle=C_B-mu_G(pi_star)`.

Changing the baseline, safety event, cost unit, or action class between the two terms invalidates the comparison.
