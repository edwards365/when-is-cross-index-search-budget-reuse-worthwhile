Evidence level: EXPLORATORY_FIXED_TARGET_CALS_AUDIT.
Frozen branch: exp/icba_cals_oracle_attainability (derived from c9c4915cf626d6170132c7beafd2dbbc58b44776).
All values use target-build as the outer unit, query as the inner unit, tau=0.99, delta=0.05, gamma=0.01 and seed 991.
Oracle/per-query choices are explicitly NON_DEPLOYABLE_UPPER_BOUND; no Oracle is an algorithm.

# Mechanical bridge report
The SIFT-10K mechanical smoke produced 12,000 rows (500 queries x 3 raw ef x 8 fixed portals) with zero failures. The SIFT/Arxiv-100K audit produced 72,000 rows (500 x 3 x 8 x 3 builds per dataset) with zero failures. Primary candidate preservation, candidate subset inclusion, union recall >= primary, alternate-repeat determinism, full-union rerank and NDC decomposition all passed. The bridge is an interface/invariant result only; it is not a method-performance certificate.
