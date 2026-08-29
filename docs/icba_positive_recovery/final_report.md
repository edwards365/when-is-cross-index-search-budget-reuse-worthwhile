# ICBA positive recovery closure

## Audit

The sprint starts from 10e003386a5ea67274b0fdb767a7a7a7a106dd43. Recovery outputs verify 48/48; the inherited legacy limitation remains 111/123. M0/M1 no-op reproduced: all 576 target shifts are zero and pair/k results agree within 1e-9. Target sentinel and evaluation sets are disjoint, but source training and calibration share 177 and 567 query IDs with target evaluation, so this is paired rebuild replay rather than new-query confirmation.

## Theory

P1 is a formal fixed-target marginal order-statistic theorem. P2 is a formal PAC tolerance result with k_min=59 for alpha=delta=0.05; k=32 is ineligible and k>=64 is only sample-size eligible under exchangeability and certified endpoints. P3 formally proves monotone safe deconservatization. P4a is a verified two-world counterexample showing that history cannot improve worst-case guarantees without structure; P4b remains `CONDITIONAL_RECOVERY_PROPOSITION_NOT_IDENTIFIED`.

## Methods and safety

B2 uses raw source predictions and target sentinel residuals only. At k=32,64,128,256 its pass counts are 0,84,141,144 of 144. At k=256 median saving versus fixed-safe is 58.21% on SIFT and 50.32% on Arxiv; median additional saving versus B1 is 30.25% and 18.65%. B2 versus B1 target-build bootstrap mean effects are 29.40% (95% CI 24.81%–33.34%) and 26.17% (16.99%–36.79%). After removing the top 1% benefit queries, all 144 pairs remain safe and mean B1-relative savings remain 29.34% and 26.09%.

B3 relative to B2 has no identified history value: SIFT mean effect 0.90% (−8.73%–11.25%) and Arxiv −0.13% (−9.24%–10.26%). It does not halve truth, its bootstrap intervals cross zero, and it does not resolve a B2 fallback problem at the passing k=256 configuration.

## Cost and deployment boundary

Calibration-search cost includes k×12 query-budget evaluations. At k=256, search-side median break-even versus B1 is approximately 5,180 queries on SIFT and 9,424 on Arxiv for finite directions. Ground-truth generation/storage and B5 full retraining costs remain `NOT_ESTIMABLE`; B5 cannot be formed without target evaluation query-ID overlap. Therefore deployment net value and comparison with full retraining are not established.

## Unified decision

Gate I passes. Gate S passes for B2 at k=256 as `FIXED_TARGET_DESIGN_SAFETY`. Gate D passes. Gate H fails. Gate R passes only at design stage. Gate V is partial/NOT_ESTIMABLE. The unique final label is `POSITIVE_MECHANISM_STANDARD_BASELINE_ONLY`: B2 validates a useful but standard target residual recalibration mechanism, while history adds no identified incremental value. No novel history method or outer-build/deployable-net-gain claim is authorized. No new graph, GPU, validation-dev, or formal-test access occurred.
