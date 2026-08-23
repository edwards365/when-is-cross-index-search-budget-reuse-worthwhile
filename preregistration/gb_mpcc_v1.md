# GB-MPCC v1 preregistration

Status: frozen before any GB-MPCC performance run. Parent Gate-A freeze commit:
`b02afed`. The machine-readable protocol is `gb_mpcc_v1.yaml`.

## Scope and firewall

GB-MPCC is a query-independent HNSW construction hypothesis. Base/train vectors may
define candidates, local scales, directions, and coverage states. Development or
formal-test queries, truth, search traces, and beam boundaries may not enter the
construction score. HDF5 `test`, `neighbors`, and `distances` remain forbidden.

The existing 1,000 train-derived development queries per dataset are partitioned
before new performance work: query IDs 0–499 are design-dev and 500–999 are
validation-dev. Design-dev permits formula checks, mechanism labels, and one-time
variant selection. Validation-dev permits gate decisions only. The original HDF5
formal-test members remain sealed until a frozen E1 pass and explicit E2 unseal.

## Frozen mechanism family

Algorithm 4 first supplies a mandatory geometric backbone. At most four flexible
slots are optimized by deterministic greedy marginal coverage over 2,048 frozen
direction–scale states. Candidate membership always uses the exact original-space
progress inequality; PCA is only a direction generator. The candidate direction
models are empirical base-neighbor directions, local-PCA directions, and an
ambient-isotropic negative reference. Near, medium, and far normalized-radius bins
and their equal weights are fixed in the YAML.

Only design-dev may choose one primary direction model and one slot count from
`{1,2,4}` after T0/R0. That choice is then committed and cannot change on
validation-dev. Tie-breaking, seeds, HNSW construction, insertion order, controls,
metrics, statistical units, and gate thresholds are already frozen.

## Interpretation boundary

The local coverage objective is normalized, monotone, and submodular on frozen
states. Its cardinality-constrained greedy guarantee applies only to incremental
coverage beyond the frozen backbone. It is not a theorem about reciprocal pruning,
the final directed HNSW graph, beam behavior, Recall, NDC, or latency. TV and
Wasserstein bounds quantify proxy-distribution error; they are not performance
guarantees.

## Gate order

T0 must validate formulas, non-degenerate capacity on at least two datasets,
measurable non-equivalence to Algorithm 4, and novelty. R0 then replays frozen
candidates without constructing a new graph. E0 builds 10K development graphs only
if T0/R0 pass. E1 runs 100K validation only after E0 passes. E2 remains closed.

No near-threshold result authorizes a post-hoc grid, state distribution, slot count,
epsilon, seed, insertion order, endpoint, or subgroup change. Failures receive only
the labels enumerated in the YAML.
