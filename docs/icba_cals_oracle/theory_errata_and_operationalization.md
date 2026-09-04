Evidence level: EXPLORATORY_FIXED_TARGET_CALS_AUDIT.
Frozen branch: exp/icba_cals_oracle_attainability (derived from c9c4915cf626d6170132c7beafd2dbbc58b44776).
All values use target-build as the outer unit, query as the inner unit, tau=0.99, delta=0.05, gamma=0.01 and seed 991.
Oracle/per-query choices are explicitly NON_DEPLOYABLE_UPPER_BOUND; no Oracle is an algorithm.

# Theory operationalization and errata
For each query q and auxiliary portal j, C_j(q) is the candidate set returned by an independent base-layer traversal; c_j and c_S are distance-call costs. We use Z_S=1[Recall@10(S,q)<0.99], with endpoint/strict failures treated as failures. The rho_min branch is evaluated only for 0<=gamma<=delta and r0>0; rescue n0 is the number of primary failures, not total queries. Absolute risk is reported, not only rho. Pre-certification rejection and post-certification accept/fallback are distinct states. Fixed-safe is not independently certified here and is therefore a registered high-budget reference, not a safety certificate. Recall and NDC are not assumed monotone in raw ef.
