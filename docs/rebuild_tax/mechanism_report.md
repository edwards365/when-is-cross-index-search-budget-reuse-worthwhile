# Gate M mechanism report

Gate M is frozen as **KEEP_REBUILD_TAX_MECHANISM**: all three datasets pass the preregistered mechanism criterion using only the 540,000 frozen source rows and 5,000 query-level bootstrap replicates (seed 991). No HNSW query was run, and validation-dev and formal-test remain sealed.

| Dataset | Realistic PIB (delta=0) | 95% lower bound | Oracle retention |
|---|---:|---:|---:|
| Arxiv | 13.593% | 12.701% | 67.501% |
| GloVe | 34.084% | 31.621% | 71.998% |
| SIFT | 22.894% | 21.658% | 43.100% |

The signal is not explained by a few extreme queries: after removing the largest 1% contributions, PIB remains 12.589%, 33.056%, and 20.694%, respectively. Leave-one-history-out minimum PIB remains positive (9.570%, 24.722%, and 14.477%). Realistic-history rank reshaping is material: mean Spearman correlation is 0.578/0.835/0.524 and mean percentile displacement is 0.185/0.116/0.203 for Arxiv/GloVe/SIFT.

PIB is identical across delta in {0, .001, .005, .01, .05, .10} for the nine-history realistic group because the finite empirical upper quantile still selects the maximum at every listed delta; this is quantile resolution, not evidence of delta invariance in a larger population. Geometry-only out-of-fold R2 is weak (0.025/0.012/0.028). Graph-global features explain graph-level mean budget more strongly (0.870/0.871/0.558), but with only 15 graph configurations per dataset they do not explain the query-by-history interaction and must not be read as a deployable predictor. Incremental trace attribution is unavailable because the frozen source contains no full topology or per-query trace events.

The authorized next step is Gate T on development data only: implement and test the frozen conformal/sentinel rule, account for full and amortized costs, and explicitly mark sentinel sizes exceeding the 250-query calibration split as finite-sample infeasible. Validation access remains prohibited until both Gate M and Gate T pass.
