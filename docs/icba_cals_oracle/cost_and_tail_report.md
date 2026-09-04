Evidence level: EXPLORATORY_FIXED_TARGET_CALS_AUDIT.
Frozen branch: exp/icba_cals_oracle_attainability (derived from c9c4915cf626d6170132c7beafd2dbbc58b44776).
All values use target-build as the outer unit, query as the inner unit, tau=0.99, delta=0.05, gamma=0.01 and seed 991.
Oracle/per-query choices are explicitly NON_DEPLOYABLE_UPPER_BOUND; no Oracle is an algorithm.

# Cost and tail report
Union lanes add an auxiliary traversal and exact merge calls, so p95 NDC is materially above the primary lane. Costs were measured in NDC; wall-clock and truth/control/certification costs were not available and are marked SYMBOLIC_COST_ONLY. Build-cluster bootstrap uses 5,000 resamples of the three builds (seed 991); one-build native-entrypoint rows are flagged underpowered in leave-one-build-out. Query-pooled p95 is descriptive and never substitutes for build uncertainty. Endpoint/right-censoring was not used to manufacture gains.
         dataset  raw_ef  primary_mean  union_mean  primary_risk  union_risk  primary_p95  union_p95  union_ndc
Arxiv-Nomic-100K      16       0.89620     0.89620       0.49400     0.49400    539.13333 1107.56042  869.62675
Arxiv-Nomic-100K      32       0.95987     0.95987       0.25733     0.25733    798.78333 1637.43542 1300.69700
Arxiv-Nomic-100K      64       0.98847     0.98847       0.09000     0.09000   1306.11667 2649.36458 2080.44325
       SIFT-100K      16       0.84667     0.84667       0.64133     0.64133    505.85000 1109.31458  854.91033
       SIFT-100K      32       0.93407     0.93407       0.37600     0.37600    738.70000 1585.87500 1271.70950
       SIFT-100K      64       0.98013     0.98013       0.14933     0.14933   1189.86667 2494.53333 2022.95042