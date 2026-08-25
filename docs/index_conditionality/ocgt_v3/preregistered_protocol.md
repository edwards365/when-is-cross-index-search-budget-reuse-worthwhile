# OCGT-v3 preregistered protocol

OCGT-v3 is a confirmatory mechanism experiment on independent train-member fallback queries and new graph instances. Its thresholds were chosen after observing exploratory OCGT-v2, but are frozen before any OCGT-v3 HNSW construction or search.

## Frozen inputs

- Datasets: `sift_10k`, `glove100_10k`, `arxiv_nomic_10k`; first 10,000 normalized-as-declared train vectors.
- Queries: 500 deterministic train-member vectors per dataset selected with seed 20260901, excluding base and all prior design source IDs.
- Split: 125 calibration and 375 confirmatory-audit queries, PCG64 seed 20260902; exact IDs and hashes are in the committed manifests.
- Formal-test access is forbidden.

## Frozen graph/search matrix

- HNSW: M=16, efConstruction=100, k=10.
- Graph seeds: 43, 59, 71.
- Orders: random, LID ascending, LID descending. Random-order seed: 20260903, shared across graph seeds within a dataset.
- efSearch: 10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512.
- Planned matrix: 27 graphs and 162,000 query×graph×ef rows.

## Gate R

Before the remaining matrix, build the nine seed-43 dataset×order graphs and compare native search against the non-invasive recorder for all 54,000 query×ef cells. Labels, recall, exact NDC, graph hashes, entry point, max level and parameters must match exactly; deterministic reruns are mandatory. Failure after repair yields `INVALID_OCGT_V3_NATIVE_REPRODUCTION_FAILURE`.

## Primary analysis

Stable sufficient ef at Recall@10≥0.9 is primary; Recall=1.0 and first sufficient ef are sensitivities. Right-censor values exceeding 512. Fixed ef is selected only on calibration queries at aggregate recall 0.95, falling back dataset-wide to 0.90 if any graph cannot reach 0.95. Quality-preserving Oracle uses actual NDC. Query-level paired bootstrap uses 5,000 replicates and seed 991.

Query×graph conditionality uses y=log2(stable sufficient ef), a query/graph/interaction variance decomposition, Omega, rank correlations, reversals, same-order cross-seed variance and cross-order variance. Directed source-to-target Oracle transfer uses a single calibration multiplier, selected for recall loss no worse than -0.001, then evaluated once on confirmatory-audit queries.

## Secondary analysis

Only the frozen OCGT-v2 LID/SHEAF implementation may be reused. SHEAF probes are ef16 and ef24 and the primary cost is C16+C24+Cpred. If exact implementation identity cannot be established, report `SECONDARY_PREDICTOR_NOT_REPRODUCIBLE`.

## Frozen gates

- Gate O: at least two datasets have mean Oracle headroom >10%, trimmed-1% headroom >3%, and bootstrap lower bound >0.
- Gate C: at least two datasets have Omega>0.10 with lower bound >0.05, and positive cross-order minus same-order/cross-seed transfer regret with lower bound >0; the effect must survive global calibration and concentration checks.
- O+C pass: `KEEP_HNSW_CONSTRUCTION_HISTORY_CONDITIONALITY`.
- O pass/C fail: `SHRINK_TO_ORACLE_REALIZABILITY_GAP`.
- O fail: `STOP_INDEX_CONDITIONAL_QUERY_DIFFICULTY`.
- Any data, reproduction, schema, independence or protocol failure: `INVALID_OCGT_V3_REPRODUCTION_OR_DATA_FAILURE`.

No endpoint, threshold, seed, order, ef value or dataset may be changed after this document is committed. Corrections require an append-only amendment with timestamp and reason.
