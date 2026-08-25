# OCGT-v3 final report

## Final decision
`KEEP_HNSW_CONSTRUCTION_HISTORY_CONDITIONALITY`

Gate R, Gate O and Gate C all passed. The result supports HNSW construction-history conditionality on the independent 10K fixture; it does not establish 100K/1M or production effectiveness.

## Confirmatory estimates

- arxiv_nomic_10k: Oracle headroom 24.92% (95% CI 23.68–26.12%); Omega 0.264 (0.216–0.324); cross-order minus same-order regret 0.0567 (0.0507–0.0627).
- glove100_10k: Oracle headroom 44.66% (95% CI 42.29–47.18%); Omega 0.164 (0.142–0.189); cross-order minus same-order regret 0.1657 (0.1561–0.1753).
- sift_10k: Oracle headroom 25.17% (95% CI 23.97–26.37%); Omega 0.375 (0.320–0.432); cross-order minus same-order regret 0.1024 (0.0985–0.1065).

All three effects remain after removing the largest 1% contributions. Cross-order transfer is consistently worse than same-order cross-seed transfer after a single calibration multiplier.

## Secondary predictors

The frozen LID/static predictor does not pass the algorithm gate because GloVe and SIFT recall losses exceed -0.001. SHEAF-like prediction fails after charging C16+C24+Cpred and has strongly negative net NDC utility. These results reject only the frozen implementations, not all possible LID or dynamic-probe methods.

## Integrity and scope

- 27/27 primary graphs and 162,000/162,000 primary rows; zero failed runs.
- Gate R: 9/9 graphs and 54,000/54,000 native-versus-instrumented cells matched exactly.
- Independent queries came only from the train-member fallback; design-dev and formal-test were not used.
- No post-result tuning, extra seed, extra order, extra ef point or graph modification occurred.
- Conclusions are limited to three 10K fixtures and require larger-scale external confirmation before any systems claim.
