# Vamana Stage-I external-validity report

## Decisions

- Scientific: `VAMANA_STRONG_EXTERNAL_REPLICATION_TWO_DATASETS`.
- Implementation validity: `VALID_SEMANTIC_BRIDGE_INHERITED_AND_REAUDITED`.
- Arxiv extension: completed after SIFT passed its pre-registered continuation gate.
- Paper-title scope: “Graph-ANNS” is allowed only with explicit restriction to the registered HNSW and DiskANN3/Vamana-style build operators; no open-world claim.
- Further non-HNSW implementation: useful for breadth, not required to establish this registered two-operator result.

## Results

SIFT used 12 replayable builds, 750 new evaluation queries and 36 primary directed source→target pairs. Category change was 71.07%; jointly-feasible budget inconsistency was 70.80%; transport risk was 16.86% (query-bootstrap 95% CI 15.65%–18.10%). Arxiv values were 48.27%, 47.47%, and 11.37% (10.20%–12.60%). Reference risk is zero by the registered target-own minimum-safe-budget definition, so risk increments equal absolute transport risks.

Within-implementation ratio-of-means cost taxes were 1.00% on SIFT and 1.11% on Arxiv; both intervals cross zero. Therefore cost evidence is weak and the strong result is carried by H1 and safety-risk materiality, not by a cost claim.

LOBO never changed the positive risk direction. Removing the top risk-contributing 1% queries left risks of 16.36% and 10.72%. Event classes sum to one and raw Recall was monotone over the registered grid in these runs.

## Evidence scope and access firewall

Inference is over the query distribution conditional on the registered 12-build families. The 12 builds per dataset do not prove unseen-build or open-world generalization; LOBO is diagnostic. Vamana and HNSW raw budgets/costs are not compared. The Arxiv HDF5 `test`, validation-dev, formal-test, runtime, and future-replication vectors/truth were not accessed. Prior HNSW E4 query vectors were read only for content-hash overlap auditing; overlap was zero and no prior truth or result was used.
