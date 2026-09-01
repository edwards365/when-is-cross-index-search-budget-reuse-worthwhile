# Held-out evaluation risk-diagnostic report

Evaluation used 500 queries per dataset and did not reselect. It is a `HELD_OUT_RISK_DIAGNOSTIC`.

| Dataset | CIBS Recall | Recall delta vs B1 | CIBS mean NDC | Mean gain vs B1 | p95 delta |
|---|---|---|---|---|---|
| SIFT-100K | 0.9908 | -0.0042 | 1255.5 | 0.468% | +10.95 |
| ArXiv-Nomic-100K | 0.9784 | -0.0082 | 818.4 | 20.043% | -271.25 |

Both Recall deltas violate the preregistered -0.001 Minimum Gate. SIFT additionally misses the 1% mean-gain gate and has a positive p95 delta.
