# Frozen CIBS-Fixed pilot contract

## Authorization and prohibition

This contract authorizes a falsifiable Stage-I CIBS-Fixed pilot only after role manifests and build manifests are frozen. It does not authorize CIBS-Race, training, validation-dev/formal-test access, or confirmatory claims.

## Data and implementation

- datasets: SIFT-100K and Arxiv-Nomic-100K;
- implementation: hnswlib;
- same data, graph degree `M`, `efConstruction`, metric, compiler, threads, and SIMD across candidates;
- main portfolio: (K=3) preregistered seeds/insertion orders;
- main evidence: (n=256), or the actual smaller frozen eligible sentinel count;
- fixed \(\alpha=\delta=.05\), raw (L=12) fixed-`ef` grid;
- ablation only: (K=2,n=128); it never replaces the main setting.

GloVe is excluded unless a new endpoint audit establishes feasibility without touching sealed sets.

## Query roles and sealing

Before execution, create immutable `cibs_sentinel`, `cibs_evaluation`, and `cibs_future_confirm` manifests. Record IDs, SHA256, pairwise overlap counts (all zero), master seed, and truth-access policy. Recommended evaluation size is at least 500; future-confirm uses the remaining or new independent queries. If sentinel has only 250 eligible queries, use 250 and the precomputed exact threshold; do not borrow from evaluation.

## Candidate-build manifest

Pre-register every seed and insertion order and record build ID, artifact path/hash, data hash, parameters, toolchain, hardware-relevant flags, timestamps, build failures, build time, peak memory, and index size. Never discard a failed build or generate candidates based on sentinel/evaluation truth.

## Baselines

1. Random Single Build;
2. Registered Single Build;
3. Certified Single Build;
4. CIBS-Fixed;
5. Full Profiling;
6. Oracle Portfolio (nondeployable upper bound only).

All certification baselines use the same risk event, evidence roles, exact truth, and multiplicity logic appropriate to their registered family.

## Measurements

For every eligible unit record raw Recall@10, endpoint failure, unsafe-selected indicator, mean/p95/p99 NDC, actual expansions, requested `ef`, selected build/budget, fallback, truth count/cost, candidate-search count/cost, build time, peak memory, index size, total offline cost, workload break-even, and a top-1%-deletion sensitivity result.

## Selection

Run the frozen algorithm in `cibs_fixed_algorithm.md`. Evaluation does not alter the action, thresholds, tie-breaking, baseline definitions, or exclusion rules. Oracle outcomes do not define deployment choices.

## Success gate — required on both datasets

\[
\Delta\operatorname{Recall@10}\ge-0.001,\quad
\text{net mean-NDC gain}\ge1\%,\quad
\Delta p95\le0.
\]

Additionally: simultaneous unsafe selection is controlled; endpoint behavior does not worsen; build-service break-even is finite; and mean-NDC gain remains positive after removing the highest-gain 1% of queries. Artifacts must replay exactly.

## Stop conditions

Stop extension if any of the following occurs: proxy savings do not translate to NDC; p95 worsens; the safety gate fails; no candidate certifies; build cost gives no finite break-even; one build alone drives the result; multiplicity causes unusable rejection; query roles overlap or truth access is contaminated; or any artifact cannot be replayed.

## Stage transition

Stage II CIBS-Race is authorized for implementation only after both datasets pass all gates and an independent portfolio confirms that the result is not a selected-seed artifact.

