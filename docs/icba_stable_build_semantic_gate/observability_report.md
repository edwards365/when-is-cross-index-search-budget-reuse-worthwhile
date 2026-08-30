# Trace observability and instrumentation contract

## Current status

The project wrapper already records or can reconstruct 16 of the 24 required fields (66.7%). The missing eight are heap snapshots, first-safe checkpoint, checkpoint top-k, checkpoint candidate set, backup path, explicit tie events, filter/deletion state, and a typed stop reason. The pinned hnswlib source exposes enough internal state for an extended tracing search to record all 24, but this requires a project-side mirror/instrumentation extension and equivalence tests against native `searchKnn`.

Therefore the gate is not `TRACE_INSTRUMENTATION_NOT_AVAILABLE`. It is `TRACE_EXTENSION_REQUIRED_BEFORE_PILOT`.

## Exact replay conditions

Exact replay is conditional on: identical serialized index bytes, metric and floating-point behavior; a total deterministic queue comparator; identical filter/deletion state; identical entry point and upper-layer path; and a trace schema recording every candidate insertion, pop, admission/rejection, visited transition, lower-bound transition, and stop reason. The upstream comparator orders by distance only, so equal-distance events are comparator-equivalent and portable replay cannot be claimed without an explicit secondary key in the tracer/action definition.

## Ground-truth boundary

`first safe discovery` requires exact-neighbor truth for the design workload. Consequently the labeled critical-certificate variant is workload-aware and its truth acquisition is a build cost. Design truth must be disjoint from calibration, certification, and evaluation truth. An unlabeled variant may record trace frequency and margins, but must not call them recall-critical or safety-critical.

## Query-role protocol

The pilot must enforce pairwise-disjoint query identifiers for design, calibration, certification, and evaluation. Only design queries may influence repair; only calibration queries may estimate the empirical structure-to-`ef` bridge; certification is reserved for the later safety gate; evaluation remains sealed. Violations trigger `QUERY_ROLE_PROTOCOL_INVALID`.

The field-level decision is in `results/icba_stable_build_semantic_gate/observability_matrix.csv`.

