Evidence level: EXPLORATORY_FIXED_TARGET_CALS_AUDIT.
Frozen branch: exp/icba_cals_oracle_attainability (derived from c9c4915cf626d6170132c7beafd2dbbc58b44776).
All values use target-build as the outer unit, query as the inner unit, tau=0.99, delta=0.05, gamma=0.01 and seed 991.
Oracle/per-query choices are explicitly NON_DEPLOYABLE_UPPER_BOUND; no Oracle is an algorithm.

# Executive brief
CALS mechanical bridge: PASS (84,000 combined rows including the 12,000 SIFT-10K smoke rows). Attainability: FAIL on the audited fixed target—no fixed or per-query Oracle portal rescued any primary miss at Recall@10>=0.99. Safety and tail gates fail (risk remains 9–64.1%; union p95 increases). Final label: NO_ADDITIVE_RESCUE_ATTAINABILITY. No deployment method or Oracle claim is authorized; external theory remains unrefuted.
