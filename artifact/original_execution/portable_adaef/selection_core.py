from scipy.stats import beta
N, DELTA, RISK_LIMIT = 500, .05 / 3, .05
def cp_ucb(failures):
    if not 0 <= failures <= N:
        raise ValueError("failure count outside 500-query role")
    return 1.0 if failures == N else float(beta.ppf(1 - DELTA, failures + 1, N - failures))

def summary(rows, recall_key, ndc_key):
    failures = sum(r[recall_key] < .95 for r in rows.values())
    ucb = cp_ucb(failures)
    mean_recall = sum(r[recall_key] for r in rows.values()) / N
    mean_ndc = sum(r[ndc_key] for r in rows.values()) / N
    return {"failures": failures, "risk_cp_ucb_delta_0_05_over_3": ucb,
            "screen_eligible": bool(ucb <= RISK_LIMIT),
            "mean_recall_at_10": mean_recall, "mean_native_distance_calls": mean_ndc}

