# Endpoint and fallback report

Endpoints are reconstructed per query from raw Recall@10 on the registered common six-level grid. Queries without a successful observed budget are right-censored; ef=200 is never imputed as success. Ef=200 is only a predeclared fallback candidate and is promoted within a fold only when its pseudo-certification Clopper–Pearson upper bound at alpha 0.025 is at most 0.05.
