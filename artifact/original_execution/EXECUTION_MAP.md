# Paper-to-execution map

This is the current portable-entry map. The earlier `artifact-sources-v1`
`CHAINS.md` is a historical source inventory, not the current execution status.
The saved-result reconstruction remains independent of new measurement.

## Choose the intended reproduction

1. **Reconstruct the paper:** use the fixed `artifact-paper-v2` saved-input
   reconstruction. This regenerates numerical results and intervals without
   rebuilding ANN indexes or replacing historical timing observations.
2. **Inspect provenance:** use `artifact-sources-v1`, original receipt mappings
   and the component records. Sanitized path prefixes do not change measurements.
3. **Execute original procedures on new outputs:** follow the entries below.
   They require explicit raw inputs, dependency identities, resources and fresh
   output directories. Their small synthetic CI tests do not establish full-size
   regeneration or identical historical performance.

## Coverage by experiment family

| Paper evidence | Portable entry and dependency order | Distinctions that must survive reproduction |
|---|---|---|
| 100K transfer; Fig. 2 and §IV-A | [100K transfer](portable_transfer_100k/README.md): prepare → compile/build → role responses → paper-row export | HNSW and Faiss use different action grids. Corrected Faiss uses 750 train-derived queries. The 24/13 content-identity issue belongs to the million-scale Faiss panel, not this 100K graph set. |
| 100K prospective recovery and paired baselines; §V | [100K recovery](portable_recovery_100k/README.md): separate S9-3/S9-4 preparation → shared S9-3 graphs → calibration profiles → locks → evaluation/timing | Arxiv normalized-IP truth is paired with the historical physical L2 index. Its native `n3` is not an exact distance counter. |
| Deep1M recovery; §V | [Deep](portable_deep/README.md): registered historical roles → eight graphs → calibration → qualification → evaluation | Historical HDF5 test roles require explicit access authorization; they are not the new train-only roles. |
| Multigraph ambiguity; §IV-B | [Three-implementation diagnostic](portable_ambiguity/README.md): membership/truth → native dependencies → 81 units → 648-direction analysis | 1024 encodes no finite tail and is not a searched action. DiskANN seed labels are repetition labels, not independently seeded builds. |
| Fixed-member million transfer and paired refresh; §§IV–V | [Transfer/refresh](portable_transfer_1m/README.md): registered members → state truth/graphs → source lock → remaining role locks → evaluation | E1a and E1b have different memberships and insertion-order rules. Their source NDC export is a separately documented measurement. |
| Fresh-query mechanisms, deployment and simple baselines; Figs. 3–4 | [Inputs](portable_fresh_inputs/README.md) → [graphs](portable_graphs/README.md) / [truth](portable_truth/README.md) → [profiles](portable_profiles/README.md) → [arrays](portable_arrays/README.md) → [History-Max](portable_policy/README.md) / [TG and fixed budgets](portable_baselines/README.md) → [timing](portable_timing/README.md) | Keep 500/500/500/1000 roles and the 8×11 action responses. TG500 is nested. Empirical optimum references and retrospective comparisons do not become deployable causal gains. |
| Lifecycle components and answer reuse; Figs. 5–6 | [Cost components and new measurements](portable_costs/README.md), [fresh-process reload](portable_reload/README.md), [answer lookup](portable_cache/README.md) | The new typed ledger connects original measurement boundaries and locked responses. Outer wrapper elapsed time is not a substitute. Saved-paper reconstruction and newly measured scenarios remain distinct. |
| Native supplement and 100K member-refresh | [Vamana/DARTH](portable_native/README.md): source/dependency preparation → new build → registered inputs → fixed source/model → held-out roles; separate refresh stages | Full-source new builds do not attest old reused object files. SIFT DARTH recall is self-reported; genuine-IP returned IDs/scores have a different verification scope. |
| Official Ada-ef supplementary transfer | [Official Ada-ef](portable_adaef/README.md): base/truth → official native build → eight source adapters → selection/qualification locks → 64 evaluation responses | Its efConstruction500 source statistics and full retained base differ from the fresh-query family. The historical unobserved exit and missing full acquisition time remain unchanged. |
| Million-scale Faiss E3/E6 supplement | [Faiss E3/E6](portable_faiss_1m/README.md): E1a truth → 48 graph records → source/selection/qualification/evaluation → corrected GENERIC counter → separate AVX2 timing | 24 records per dataset include 13 content identities. All registered weights remain. GENERIC exact counts are not an AVX2 timing denominator. |

## Validation interpretation

Each entry's README names installation commands, phases, input identities,
resource limits and outputs. CI tests use newly generated small inputs; they do
not reopen sealed experiments. A native compile, an input-hash check, a saved
result reconstruction and a full scientific rerun are four different checks.
The final release records the actual checks, not inferred success from code
presence. A stopped dependency or frozen-byte mismatch stops dependent work.

Raw vectors and indexes are not embedded in Git. Obtain raw data through the
declared upstream access paths and retain their licensing conditions. Public
dependency downloads remain network requirements; this is not an offline mirror
of every Rust crate, system library or dataset.
