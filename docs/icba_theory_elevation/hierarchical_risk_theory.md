# T-OW2 and hierarchical risk theory

## T-OW2: query certificates do not imply build reliability

Let the observed build family be `Theta_obs={theta_1,...,theta_m}` and suppose a policy satisfies `R_theta_i(pi)<=delta_q` for every observed build. Without an assumption linking unseen environments to the observed family, this gives no bound on `Pr_{theta~Pi}(R_theta(pi)>delta_q)`.

Minimal counterexample: take one observed environment where the policy is always safe and one unseen environment where it is always unsafe. Any meta-law assigning mass `p` to the unseen environment has build-level bad probability `p`, which may be any number in `[0,1]` while every observed query certificate remains unchanged. Hence a desired `delta_b` cannot be inferred.

Status: `FORMAL_PROOF_COMPLETE`. This is a logical non-implication and does not depend on Graph-ANNS-specific measurements.

## Two-level semantics

- **Fixed design:** the nine builds in a cell are named environments. Statements are simultaneous or descriptive over those nine only. Build bootstrap is a sensitivity calculation, not a population certificate.
- **Random build:** environments are iid/exchangeable from an explicit `Pi`. Then build indicators `1{R_theta(pi)>delta_q}` support binomial or conformal inference, subject to query-risk classification uncertainty.

Query and build uncertainty must be nested or union-bounded. Treating 972,000 rows, 648 directed pairs, or 9×query counts as independent builds is invalid.

## Candidate selection

Selecting among `M` candidates with the same evidence requires simultaneous control, sample splitting, or a valid selection-aware method. A simple Bonferroni construction replaces level `alpha` by `alpha/M` at the affected layer. Candidate multiplicity is not repaired merely by increasing target probes unless those probes are reserved for selection-aware evaluation.
