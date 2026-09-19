# Reproducibility contract

## Run identity

Every native run records a stable run ID, Git commit, hardware identity, dataset path/checksum, index/build identity, algorithm, parameters, random seeds, insertion order, compiler/build configuration, timestamps, logs, raw-output path, and terminal status.

Datasets, large indexes, raw traces, credentials, and machine-local paths are reconstructed or supplied from manifests and are not committed to Git.

## Query-role firewall

Selection/design, certification, and evaluation roles are disjoint whenever the protocol claims independent qualification. Evaluation outcomes must not change the candidate, action order, hyperparameters, confidence threshold, or fallback rule. Any retrospective label is marked as analysis-only and cannot be represented as a deployment input.

## Statistical unit

The declared unit follows the claim:

- query-cluster intervals for shared-query response comparisons;
- target build as the outer unit for rebuild robustness;
- crossed target-build × query resampling when both dependencies are shared;
- per-target or per-decision CP certificates unless a simultaneous allocation is explicitly registered.

Repeated queries are never presented as independent builds.

## Measurement contract

Latency comparisons require the same machine, thread count, compiler flags, SIMD/OpenMP configuration, counter setting, affinity policy, warm-up, cache protocol, query order, and interference controls. Counter-enabled and counter-disabled builds are reported separately.

NDC is a hardware-independent measure of distance-computation work. It is not a substitute for wall time. GPU exact search is never compared as if it were CPU graph-search latency.

## Cost contract

Serving search, probing, truth acquisition, training, certification, control, fallback, and rebuild costs are named separately. A ledger may report only the components that were measured or validly reconstructed. Missing components remain symbolic or explicitly out of scope; they are never silently treated as zero.

## Reproduction tiers

1. **Compact paper replay:** regenerate checks, tables, and figures from committed compact evidence.
2. **Artifact smoke:** verify checksums, role firewalls, decisions, and focused tests without raw data.
3. **Full native replay:** use checksummed external datasets/indexes and the registered configurations.

See [QUICKSTART.md](QUICKSTART.md) and the [artifact README](../artifacts/graph_anns_phase3_ea85/README.md).

## Claim discipline

- A result is scoped to its registered builds, grids, query populations, and hardware where applicable.
- Failed seeds, fallbacks, censored endpoints, and negative results are preserved.
- Post-hoc reanalysis is labeled as such.
- Per-decision confidence is not described as simultaneous campaign coverage.
- Local mathematical guarantees are not presented as global ANN recall or complexity guarantees.
