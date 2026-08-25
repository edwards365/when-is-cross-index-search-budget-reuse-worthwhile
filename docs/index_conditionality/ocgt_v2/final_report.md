# OCGT-v2 final report

## Primary status

`INVALID_OCGT_V2_REPRODUCTION_OR_DATA_FAILURE`

The 27 graphs and 162,000 query-by-ef rows completed without runtime failures and without validation-dev or formal-test access. However, the confirmatory protocol is invalid because mandatory pre-performance reproduction and evidence-schema requirements were not satisfied. No KEEP/SHRINK/STOP algorithm authorization may be issued from this run.

## Descriptive results (non-authorizing)

- Oracle NDC headroom: Arxiv 25.29%, GloVe 39.21%, SIFT 22.54%.
- Omega: Arxiv 0.305, GloVe 0.163, SIFT 0.348.
- Centered Spearman median: 0.557, 0.784, 0.523.
- Hard top-10% Jaccard median: 0.333, 0.351, 0.266.
- Median transfer eta: Arxiv -0.005, GloVe 0.116, SIFT -0.095.
- LID/static mean NDC gain is negative on all datasets. SHEAF correlations are sometimes higher, but actual two-probe cost makes NDC gain strongly negative.

These diagnostics point toward `SHRINK_TO_HNSW_CONSTRUCTION_HISTORY` as a shadow hypothesis: same-order cross-seed rankings are much more stable than cross-order rankings, and cross-order Oracle transfer is poor. Because invalidity has highest priority, this is not the official decision.

## Invalidity reasons

- OCGT-v2 Original reproduction Gate was not completed before the 27-graph matrix
- raw query rows omit required entry_point, graph_checksum, candidate_checksum, and explicit query_split
- exact query IDs and RNG algorithm were materialized only after performance collection
- graph invariants required by preregistration were not fully captured before temporary indexes were deleted

## Scope limits

All evidence comes from three 10K train-side fixtures and 500 previously used design-dev queries per dataset. It is neither formal testing nor evidence of 100K/1M or industrial performance. No validation-dev or formal-test member was accessed.
