# Degree-constrained repair readiness

## Decision

`PSEUDOCODE_ONLY`

The objective is now sufficiently frozen for a pilot implementation specification, but no implementation or effectiveness evidence exists. The method requires project C++ code around the pinned hnswlib index; it is not a proven upstream-compatible core patch.

## Frozen pilot specification

1. **Critical edge.** For each labeled design query, record the successful candidate-queue insertion parent of every certificate node on or before the first safe checkpoint. The first successful insertion is unique under the recorded event order; mere adjacency or first reachability is not the definition.
2. **Path impact.** The normalized frequency with which an edge is critical across design queries and shadow builds, optionally weighted by pre-registered query weights.
3. **Frontier margin.** At a certificate admission or pop, the gap in the declared total priority key to the closest non-certificate competitor. Exact ties have margin zero.
4. **Intruder risk.** The design/shadow frequency or an upper confidence bound for target-only competitors that pop before a downstream certificate node.
5. **Backup edge.** An alternative insertion edge observed in at least `r_min` shadow builds whose recorded replay admits the certificate node before its required checkpoint.
6. **Edge score.** `w(e)=lambda_c*c(e)+lambda_p*p(e)+lambda_b*b(e)+lambda_m*clip(m(e))-lambda_i*i(e)`. Coefficients, clipping, and normalization are pre-registered using design data only.
7. **Shadow aggregation.** Report mean and a pre-specified lower confidence bound; protected status uses the lower bound.
8. **Degree overflow.** Retain mandatory protected edges first, then apply the declared diversity pruning to remaining slots. If mandatory count exceeds the degree cap, the certificate is invalid; never silently drop a mandatory edge.
9. **Connectivity.** After repair, require directed layer-0 reachability from the entry point for every retained node plus weak connectivity; otherwise roll back the query-local repair batch.
10. **Layers.** Pilot repair acts on layer 0 only. Upper layers remain unchanged.
11. **Entry point.** The serialized entry point is unchanged.
12. **Order.** Apply post-build repair before serialization, then audit reciprocal pruning and protected-edge survival.
13. **Complexity.** Trace collection is proportional to observed search work; score aggregation is linear in recorded events; repair is `O(sum_v d_v log d_v)` with the chosen local sort/prune implementation, excluding graph-wide connectivity checks.
14. **Memory.** Store bounded per-edge aggregates, not full traces, after audit export. A pre-registered byte cap is mandatory.
15. **Serialization.** Use native index serialization plus a sidecar manifest containing source commit, metric, build seed/order, protected edges, scores, coefficient version, and SHA-256.
16. **Invalid certificate.** Fall back to the unmodified build (or the separately declared consensus route); do not infer safety.
17. **Labeled/unlabeled variants.** Only the labeled variant may use first-safe checkpoints and “critical” terminology. The unlabeled variant is a trace-stability heuristic.

## Unresolved implementation risks

The hnswlib neighbor representation and reverse-pruning behavior can delete previously selected reciprocal edges. Mandatory-edge preservation therefore needs explicit post-repair verification. Comparator ties also require an explicit secondary identifier in the tracing model. Neither change establishes the empirical `ef` bridge.

