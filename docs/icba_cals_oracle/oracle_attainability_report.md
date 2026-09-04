Evidence level: EXPLORATORY_FIXED_TARGET_CALS_AUDIT.
Frozen branch: exp/icba_cals_oracle_attainability (derived from c9c4915cf626d6170132c7beafd2dbbc58b44776).
All values use target-build as the outer unit, query as the inner unit, tau=0.99, delta=0.05, gamma=0.01 and seed 991.
Oracle/per-query choices are explicitly NON_DEPLOYABLE_UPPER_BOUND; no Oracle is an algorithm.

# Oracle attainability report
The fixed portal union did not rescue any primary failure at tau=0.99 in the audited 100K rows; the non-deployable per-query portal upper bound also rescued zero. Thus no additive rescue attainability was observed on either dataset. This is a strict fixed-target conclusion and is limited by three existing builds and 500 design queries.

Summary:
         dataset  raw_ef  primary_mean  union_mean  primary_risk  union_risk  primary_p95  union_p95  union_ndc
Arxiv-Nomic-100K      16       0.89620     0.89620       0.49400     0.49400    539.13333 1107.56042  869.62675
Arxiv-Nomic-100K      32       0.95987     0.95987       0.25733     0.25733    798.78333 1637.43542 1300.69700
Arxiv-Nomic-100K      64       0.98847     0.98847       0.09000     0.09000   1306.11667 2649.36458 2080.44325
       SIFT-100K      16       0.84667     0.84667       0.64133     0.64133    505.85000 1109.31458  854.91033
       SIFT-100K      32       0.93407     0.93407       0.37600     0.37600    738.70000 1585.87500 1271.70950
       SIFT-100K      64       0.98013     0.98013       0.14933     0.14933   1189.86667 2494.53333 2022.95042

Rescue rows (including non-deployable upper bound):
         dataset  raw_ef        portal_id  n0      r0  rho_min  rescued_from_primary  primary_failures  rescue_rate  union_risk  union_mean_recall  union_p95_ndc  fixed_safe_at_5pct   gamma   delta
       SIFT-100K      16 ORACLE_PER_QUERY 962 0.64133  0.93763                     0               962      0.00000     0.64133            0.84667      927.05000               False 0.01000 0.05000
       SIFT-100K      32 ORACLE_PER_QUERY 564 0.37600  0.89362                     0               564      0.00000     0.37600            0.93407     1424.00000               False 0.01000 0.05000
       SIFT-100K      64 ORACLE_PER_QUERY 224 0.14933  0.73214                     0               224      0.00000     0.14933            0.98013     2350.05000               False 0.01000 0.05000
Arxiv-Nomic-100K      16 ORACLE_PER_QUERY 741 0.49400  0.91903                     0               741      0.00000     0.49400            0.89620      988.05000               False 0.01000 0.05000
Arxiv-Nomic-100K      32 ORACLE_PER_QUERY 386 0.25733  0.84456                     0               386      0.00000     0.25733            0.95987     1534.05000               False 0.01000 0.05000
Arxiv-Nomic-100K      64 ORACLE_PER_QUERY 135 0.09000  0.55556                     0               135      0.00000     0.09000            0.98847     2564.25000               False 0.01000 0.05000