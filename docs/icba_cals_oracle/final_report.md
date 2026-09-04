Evidence level: EXPLORATORY_FIXED_TARGET_CALS_AUDIT.
Frozen branch: exp/icba_cals_oracle_attainability (derived from c9c4915cf626d6170132c7beafd2dbbc58b44776).
All values use target-build as the outer unit, query as the inner unit, tau=0.99, delta=0.05, gamma=0.01 and seed 991.
Oracle/per-query choices are explicitly NON_DEPLOYABLE_UPPER_BOUND; no Oracle is an algorithm.

# Final report
## Decision
**NO_ADDITIVE_RESCUE_ATTAINABILITY**

All mechanical invariants passed, but no fixed portal or non-deployable per-query portal increased recall for primary failures at tau=0.99. Both datasets remain above the 5% risk target at every audited raw ef (SIFT union risk 0.641/0.376/0.149; Arxiv union risk 0.494/0.257/0.090 for ef 16/32/64). The union p95 NDC is higher than primary (approximately SIFT 1109/1586/2495 and Arxiv 1108/1637/2649). Consequently Q1 additive rescue, Q2 fixed portal sufficiency, and Q3 economic rescue gates fail; no CALS method derivation is authorized. This does not refute the external theory or prior experiments.

## Limitations
Three existing builds and 500 design queries per dataset are a pilot; a 5000-resample build bootstrap is therefore wide and the result is exploratory. Parquet was not written because no parquet engine is installed; CSVs and checksums are supplied. Truth/control/portal-selection costs are not estimable. The external theory object is provenance-limited and read-only.
