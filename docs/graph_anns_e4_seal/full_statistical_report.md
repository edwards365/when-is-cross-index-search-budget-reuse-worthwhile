# Full statistical report

## Units and estimands

The design is 2 datasets × 8 construction-seed blocks × 3 fixed insertion-order treatments. Queries are a crossed inner unit; the 552 directed pairs are dependent derived contrasts and are never treated as IID.

H1-A is descriptive: $P_q[\max_G B_G(q)-\min_G B_G(q)>0]$. SIFT is 0.894667, with mean/median/p90/p95 diameter 46.16/30/100/142; Arxiv is 0.753333, with 31.72/20/70/110. No population CI is attached to this nonsmooth range/support statistic.

H1-B is $E[1\{B_{s,o}(q)
e B_{s,o'}(q)\}]$ within seed; H1-C is the analogous within-order cross-seed contrast. SIFT H1-B is 0.574278 [0.552408, 0.596799], absolute difference 23.960; H1-C is 0.132460 [0.111531, 0.148421], absolute difference 3.418. Arxiv H1-B is 0.452333 [0.428731, 0.475677], and H1-C is 0.126175 [0.105611, 0.141929]. Intervals use 5000 crossed seed–query resamples with seed 991 and fixed order treatments.

H2 estimates $E[Z_t(B_s)-Z_t(B_t)]$. SIFT risk increment is 0.215734 [0.207408, 0.223998], safe ROM tax 0.194472 [0.182599, 0.206595]. Arxiv values are 0.171205 [0.162014, 0.180611] and 0.148793 [0.137201, 0.164104]. Random-only and all leave-one-seed/order contrasts remain positive.
