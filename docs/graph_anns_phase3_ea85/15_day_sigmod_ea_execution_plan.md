# Graph-ANNS ICBA/TCP: 15-Day SIGMOD E&A Closure Plan

## Objective and evidence policy

The package targets a reproducible SIGMOD E&A submission, not a claim of universal superiority. The primary estimand is the probability that a deployed implementation-native search action produces `Recall@10 < 0.95` after a graph rebuild or registered data refresh. The primary statistical unit is the target build. Design, selection, certification, evaluation, and cold-evaluation queries remain disjoint. Negative and boundary results are retained. External-method integration failures are reported separately and are never interpreted as scientific failures.

## Phase 0 — Unified protocol and artifact ledger (Day 1)

Goal: freeze one event definition, native action semantics, query-role firewall, target-build inference, cost fields, and stopping rules before new evidence is observed.

Exit gate:

- all manifests are machine-readable and hashed;
- all role intersections are zero;
- every experiment reports the same risk, mean-cost, p95/p99, fallback, and amortization fields or an explicit `NOT_ESTIMABLE`;
- legacy full-hit evidence is preserved and clearly separated from the new Recall@10=.95 estimand.

Status: complete.

## Phase 1 — External adaptive-search comparison (Days 2–4)

Goal: establish whether the rebuild portability failure and ICBA safety/value decomposition also appear for published adaptive methods.

Registered comparisons:

1. official DARTH at Recall@10=.95 on SIFT-100K and Arxiv-Nomic-100K;
2. official Ada-ef at Recall@10=.95, using a project-side adapter without modifying the official checkout;
3. raw external policy, ICBA-audited policy with fixed-safe fallback, and the fixed-safe native endpoint.

Exit gate:

- at least three semantically valid target builds per dataset for the main comparison;
- independent certification and evaluation;
- raw and audited safety/efficiency reported separately;
- ten-build extension only after the three-build semantic gate passes.

Current status: DARTH complete; Ada-ef environment and official-header compile bridge in progress.

## Phase 2 — Mixed insert/delete-to-rebuild refresh (Days 5–7)

Goal: move beyond seed-only rebuilds and isolate three effects: rebuild randomness, a 5% mixed insert/delete refresh, and repeated versus cold queries.

Design:

- SIFT-100K and Arxiv-Nomic-100K;
- one registered 5% mixed refresh scenario per dataset, six target builds per scenario;
- 1% and 10% refresh sensitivity as secondary analyses;
- 500 fresh cold-evaluation queries per dataset;
- compare fixed-safe, source reuse, TCP, and external baselines that pass Phase 1 integration.

Exit gate: exact update membership and build seeds are reproducible; the update-only, rebuild-only, and query-reuse effects are separately estimable; safety and cost conclusions survive leave-one-build-out analysis.

## Phase 3 — Vamana native-action semantic bridge (Days 8–10)

Goal: close the implementation-family gap without equating `l_value` to HNSW `efSearch`.

Design:

- six Vamana builds per dataset;
- full registered `l_value` grid with fixed beam width;
- actual target-safe reference action, never a substituted zero-risk legacy baseline;
- same Recall@10=.95 event and target-build inference.

Exit gate: native-action ledger is complete; zero-risk or null-headroom outcomes are retained; Vamana contributes quantitatively only when its estimand matches the unified protocol.

## Phase 4 — Third-family scale check (Days 11–12)

Goal: test whether the phenomenon and the audit conclusions extend beyond the two development families.

Design:

- Deep1M/deep-image-96, eight hnswlib builds;
- optional four-build Faiss-HNSW confirmation if resources and semantic checks pass;
- no downscaling to a small dataset if Deep1M is unavailable.

Exit gate: fresh query roles, build-level uncertainty, safety, mean cost, and tail cost are reproducible; cross-family conclusions are explicitly stratified rather than requiring every metric to be positive everywhere.

## Phase 5 — Statistical and economic seal (Days 13–14)

Goal: turn the experiment matrix into decision evidence suitable for E&A review.

Required outputs:

- target-build cluster bootstrap, 5000 repetitions, seed 991;
- per-dataset estimates, pooled estimates only when scientifically meaningful, LOBO, and deletion of the largest-benefit build;
- mean, p95, p99, fallback and abstention rates;
- profiling, truth, certification, rebuild, and serving costs;
- break-even at N in {1e3, 1e4, 1e5, 1e6, 1e7};
- an explicit boundary/negative result table.

Exit gate: headline claims are supported by machine-readable tables and remain valid under the registered robustness analyses; unsupported universal or SOTA language is absent.

## Phase 6 — Anonymous artifact and paper-facing seal (Day 15)

Goal: provide a one-command, reviewer-auditable package.

Deliverables:

- environment lockfiles and external-source commit ledger;
- lightweight smoke path and full reproduction path;
- dataset preparation and checksum manifests;
- figure/table regeneration scripts;
- expected runtime/storage ledger and failure diagnostics;
- claim-to-evidence matrix and limitations.

Final gate: a clean clone can reproduce smoke outputs; all main tables/figures trace to frozen inputs and scripts; repository state is committed and pushed; no sealed evaluation role was used for tuning.

## Decision rule for the submission route

The E&A package is ready when the artifact is executable, the unified estimand is respected across families, the principal portability phenomenon is reproducible beyond one method and one dataset, and ICBA/TCP are reported as conditional tools with safety, efficiency, tail, and amortization evidence. A regular-paper claim of broad method superiority requires additional cross-method efficiency wins; E&A does not require absolute SOTA, but it does require rigorous, useful, and reproducible evidence.
