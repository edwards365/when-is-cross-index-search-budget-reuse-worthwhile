# Endpoint Feasibility Control

The frozen 81 graphs reproduce exactly as 54 `CERTIFIED_ENDPOINT_FEASIBLE`, 17 `RIGHT_CENSORED_AT_MAX_BUDGET`, and 10 `NO_PRACTICAL_SAFE_ENDPOINT`. Every SIFT and Arxiv graph is certified across hnswlib, Faiss HNSW and Vamana (54 total). Every GloVe graph is outside the feasible stratum (0/27 certified).

The primary open-world failure analysis therefore contains only the 54 SIFT/Arxiv targets. It does not use GloVe to establish migration failure. For each retained build, `feasible_only_open_world.csv` records the conservative under-budget point estimate, exact one-sided 95% Clopper--Pearson upper bound, and the same quantities after the preregistered deletion of the highest-savings 1% of evaluation queries.

The retained open-world point risks remain well above 5% in the previously frozen aggregates: hnswlib SIFT/Arxiv 9.32%/7.03%, Faiss 22.83%/15.71%, and Vamana 16.89%/7.62%. The top-1% deletion columns remain nonzero and are evaluated build by build; positive risk upper bounds are not treated as independent across the 744 queries or across graph pairs.

GloVe is a separate endpoint-feasibility barrier. Its maximum-grid empirical failure ranges are 4.5%--5.5% for hnswlib, 5.0%--6.5% for Faiss and 4.9%--5.3% for Vamana, while no graph's one-sided upper confidence limit meets `delta_q=0.05`. Frozen data cannot distinguish whether extending the budget grid would eventually provide a safe endpoint or whether some queries are structurally unreachable. The correct label is `RIGHT_CENSORING_PREVENTS_IDENTIFICATION`; the closed-world 67.69% search-only NDC reduction is not a safe gain.

Gate B is evaluated only on SIFT/Arxiv and therefore cannot be explained by GloVe endpoint infeasibility. Its final pass/fail is recorded after build-level aggregation and top-1% robustness checks.
