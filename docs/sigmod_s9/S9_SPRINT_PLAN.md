# SIGMOD E&A S9: stable 9/10 evidence sprint

Frozen manuscript baseline: `96399e742248964dcd49db2fadb0e857a06e3bdd`

The sprint targets the remaining sources of reviewer uncertainty. It does not treat a score as an experimental endpoint, and it does not permit tuning after held-out results.

## S9-1 — Reproducibility and artifact confidence

**Purpose.** Convert the current internally checked artifact into a clean-environment, anonymous, claim-to-file reproducibility record. This raises confidence in the existing evidence without changing scientific claims.

**Work.** Rebuild the anonymous package from its allowlist; regenerate tables, figures, main PDF, and appendix; replay all evidence checkers; audit query-role manifests, hashes, paths, metadata, and identity leakage; record which native data are packaged and which require separately provisioned resources.

**Gate.** Zero identity leaks, zero unresolved references, zero claim-map mismatches, all registered checks pass, and all regenerated headline values match the frozen manuscript. Same-host clean replay must not be described as independent replication.

## S9-2 — Deployment-grade runtime and lifecycle economics

**Purpose.** Remove the largest remaining evidence limitation: NDC is a machine-independent serving-work endpoint but not latency or monetary cost. This phase tests whether the qualified policies deliver real runtime value after all information costs are charged.

**Work.** Freeze machine, compiler, affinity, thread count, warm-up, cache state, interleaving order, and repetition count before measurement. Compare endpoints, target-global calibration, TCP, and fixed-slack routes under identical query/build roles. Report p50/p95/p99 latency, throughput, fallback/non-fallback tails, calibration, certification, truth, control, and acquisition cost under cached and cold-history ledgers over declared serving horizons.

**Gate.** Safety remains qualified; runtime intervals are based on paired interleaved measurements; positive claims require a confidence interval excluding zero for the relevant serving or lifecycle estimand; p95 noninferiority is checked separately. A failed runtime translation becomes a boundary result, not a reason to change the policy.

## S9-3 — Prospective robustness outside the registered evidence pool

**Purpose.** Reduce dependence on the current finite set of builds, grids, and query populations and test whether the decision procedure—not merely one favorable realization—transfers.

**Work.** Before result access, freeze fresh build seeds/orders, query-role IDs, grids, SLAs, and candidate rules. Run new-build and new-query confirmation on the two 100K datasets and the justified scale block. Preserve endpoint-clipped and strict-SLA cases. No hyperparameter or lane may be changed after the freeze.

**Gate.** No role overlap; native outputs and action ordering are reproducible; claim-specific safety and tail gates pass on each positive block; build-cluster intervals and leave-one-build-out diagnostics are reported. Cross-dataset universality is not required, but each retained claim must match its registered scope.

## S9-4 — Mechanism, equal-information baselines, and external comparators

**Purpose.** Establish why value appears, when a simpler target-global policy is sufficient, and whether ICBA changes conclusions for external adaptive-search methods. This protects the paper from the criticism that it only measures a phenomenon and then presents a favorable policy.

**Work.** Use matched labels, builds, grids, failure events, and cost accounting for target-global, TCP, fixed slack, DARTH/Ada-ef-compatible policies, and available external controls. Separate graph-response variation, query conditioning, target calibration, certification rejection, fallback, and endpoint clipping. Run component ablations and predeclared failure attribution; do not force incompatible methods into a single leaderboard.

**Gate.** Every comparison has a documented common estimand or is explicitly marked incomparable. Equal-information comparisons remain primary for incremental method value. Negative and dataset-dependent results are retained.

## S9-5 — Theory, manuscript, and adversarial submission seal

**Purpose.** Turn S9-1 through S9-4 into a coherent paper rather than an accumulation of appendices. Strengthen the link between observation limits, fixed-target certification, recovery choice, and economic deployment decisions.

**Work.** Update the theory-contact table and claim map; state assumptions and estimands next to each theorem/proposition; integrate runtime and prospective evidence by research question; regenerate all figures/tables; run reverse numerical checks, anonymity/metadata checks, clean artifact replay, and an adversarial mock review. Keep the main paper within the official limit and move diagnostic depth to the separate appendix/artifact.

**Gate.** No claim exceeds its evidence scope; every headline number has one canonical machine-readable source; all PDFs and the anonymous package build cleanly; remaining limitations are explicit and non-duplicative. Final submission still requires a real anonymous artifact URL in the submission form.

## Execution order and stop rules

1. S9-1 begins immediately and is low-risk.
2. S9-2 starts only after S9-1 passes.
3. S9-3 starts only after the runtime protocol and frozen policies are sealed.
4. S9-4 may reuse frozen responses but may not inspect S9-3 evaluation data to choose methods.
5. S9-5 begins only when scientific outputs are frozen.

Any input mismatch, role overlap, untracked scientific change, insufficient disk headroom, or active conflicting process stops the affected phase. Existing results, indexes, logs, and other users' files are never deleted to force progress.
