# Instrumentation gate

Status: **PASS** for project-side instrumentation equivalence. This gate is infrastructure evidence only; it is not evidence for or against Stable-by-Construction.

The tracer emits the frozen 24-field contract for every query/ef pair. Its introduction parent is the parent associated with the first successful candidate-queue insertion in the recorded event order. Exact truth is not consulted by the tracer; `first_safe_discovery` and `endpoint_status` therefore remain explicit non-truth sentinels until a permitted design/calibration caller supplies truth-derived annotations.

The upstream hnswlib search comparator is preserved to guarantee native equivalence. In particular, upstream ordering remains distance-based. `composite_priority_key` records the diagnostic `(distance,nodeID)` representation and `tie_event` records observed equal-distance boundary ties; these fields do **not** claim that the frozen upstream comparator was changed to node-ID tie-breaking.

Evidence:

- Synthetic fixture: 256 queries × 3 ef = 768 comparisons; executable-internal native/tracer top-k and exact distance-count checks passed, and 22/22 schema/semantic checks passed.
- Frozen SIFT design-dev fixture: query IDs 0–99 × ef {10,20,40} = 300 comparisons on the existing Original 100K seed-7 index. Native/tracer top-k equality was 300/300 and exact distance-count equality was 300/300.
- Contract completeness was 24/24 fields for all 300 SIFT rows, with no empty cells. One equal-distance tie diagnostic was observed and retained.

The SIFT fixture is the already frozen design-dev input used by the prior R0 audit; no certification-reserved or evaluation-reserved truth was accessed. The next protocol step is to freeze/reuse the four-way 1000-query role split before any Stable result is inspected.
