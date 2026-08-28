# T-OW5 sample-complexity decomposition

Let `n` be labeled calibration queries per environment, `m` independently sampled historical environments, `k` target probes, and `M` candidate policies.

## Within-build query risk (`n`)

For iid Bernoulli failures, exact binomial or time-uniform alternatives estimate `R_theta`. With zero failures, the one-sided `(1-alpha)` Clopper–Pearson upper bound is `1-alpha^(1/n)`. Certifying risk at most `delta_q` therefore requires

`n >= ceil(log(alpha)/log(1-delta_q))`.

This controls query risk only for the named environment. Dependence, query shift and censoring require a changed model or conservative interval.

## Build-level meta-risk (`m`)

If builds are iid from `Pi` and no bad build is observed, the identical form is

`U_alpha(0,m)=1-alpha^(1/m)`.

At `alpha=0.05`, zero bad builds require `m=29,59,299` to certify `delta_b=0.10,0.05,0.01`, respectively. Nine builds give upper bound about `0.2831`, not a 5% certificate. If each build's bad/good label is estimated from finite queries, the classification error must also be controlled.

## Target environment testing (`k`)

`k` acts on environment identification through the chosen observation channel. For iid probes and a simple pair with per-probe KL `d`, total KL is `k d`. Standard testing bounds imply exponential improvement under positive separation; conversely T-OW1b remains nontrivial while `TV(Q0^k,Q1^k)<1`. If `d=0`, no finite `k` helps. If the true environment lies outside support or the observation-response relation is wrong, exact environment identification inside the candidate model still does not guarantee a correct budget.

Labeled `Z2` and unlabeled `Z1` have different laws and costs, so their `k` requirements are not interchangeable.

## Candidate count (`M`)

For a finite family, uniform Hoeffding-style selection bounds scale as `log(M/alpha)` rather than `log(1/alpha)`. Exact constants depend on the loss and dependence structure. Post-selection evaluation on reused data without correction is not covered.

## What additional data cannot fix

- Increasing `n` cannot establish a meta-environment law or repair support misspecification.
- Increasing `m` cannot create a deployable observation channel or identify query-specific source-Oracle actions.
- Increasing `k` cannot make a misspecified response map correct.
- Increasing `M` enlarges multiplicity and does not constitute evidence.

## Status

The zero-event binomial requirements, fixed-versus-random-build separation and non-implication statements are `FORMAL_PROOF_COMPLETE`. General dependent hierarchical rates and matching adaptive-selection bounds remain `PROOF_SKETCH` until their sampling assumptions are fixed.
