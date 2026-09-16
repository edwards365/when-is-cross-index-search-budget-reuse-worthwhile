# Supplement Loop 2: harmonized lifecycle cost protocol

## Objective

Determine the amortization horizon of target-selection TCP recalibration under
the already sealed 5% mixed-refresh experiment. This is a cost-only analysis;
no action, model, query role, seed, safety decision, or effect estimate may be
changed.

## Frozen accounting unit

The primary cost currency is implementation-native distance evaluations. Time
is secondary and descriptive because historical wall-clock conditions are not
fully controlled. For TCP versus fixed-safe on the same rebuilt target graph:

- rebuild and common data-loading costs cancel and are reported separately;
- exact target labels cost `target_base_rows` distances per labeled query;
- selection search cost is the sum of registered grid-replay `dists` over the
  500 selection queries;
- certification search cost is the registered selected action's `dists` over
  the independent 500 certification queries;
- profiling/control costs use the sealed per-build ledgers and replay tables;
- serving saving is fixed-safe evaluation mean NDC minus deployed TCP mean NDC;
- fallback serving cost is already present in the deployed evaluation lane.

Truth, selection, certification, control, and serving terms must be reported
individually. Any unavailable component remains `NOT_ESTIMABLE`; it is never
set to zero unless it is provably common and cancels in the comparison.

## Statistics and horizons

Use the 20 sealed target builds (10 SIFT, 10 Arxiv), target build as the outer
unit, 5,000 bootstrap repetitions with seed 991, dataset-separated results,
LOTO, and deletion of the largest-benefit build. Report total incremental cost
and net distance saving for N in `{1e3,1e4,1e5,1e6,1e7}` plus the per-build
break-even query count. Tail safety and risk decisions are imported unchanged
from Phase 2.

## Gate

`LIFECYCLE_DISTANCE_COST_GATE_PASSED` requires on both datasets: certified risk
at most 5%, positive net saving at at least one registered N, positive
target-build bootstrap lower bound at that N, positive LOTO/deletion checks,
and no omitted non-common cost. Otherwise report
`LIFECYCLE_COST_CONDITIONAL_OR_NOT_ESTIMABLE` with the exact missing or failing
component. Wall-clock is never promoted to a controlled systems claim.
