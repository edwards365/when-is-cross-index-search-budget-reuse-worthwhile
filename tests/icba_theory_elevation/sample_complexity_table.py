#!/usr/bin/env python3
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/icba_theory_elevation/m_n_k_requirements.csv"
alpha = 0.05
rows = []
for layer, symbol in [("within_build_query", "n"), ("random_build_meta", "m")]:
    for delta in (0.10, 0.05, 0.01):
        required = math.ceil(math.log(alpha) / math.log(1-delta))
        upper_at_nine = 1-alpha**(1/9) if layer == "random_build_meta" else ""
        rows.append({"layer":layer,"symbol":symbol,"alpha":alpha,"target_delta":delta,
                     "zero_event_required_count":required,"upper_bound_at_count_9":upper_at_nine,
                     "assumption":"iid Bernoulli units at named layer"})
rows.extend([
    {"layer":"target_probe_testing","symbol":"k","alpha":alpha,"target_delta":"","zero_event_required_count":"NOT_IDENTIFIABLE_WITHOUT_CHANNEL_SEPARATION","upper_bound_at_count_9":"","assumption":"requires specified Z1/Z2 law and positive KL/TV separation"},
    {"layer":"candidate_selection","symbol":"M","alpha":alpha,"target_delta":"","zero_event_required_count":"LOG_M_OVER_ALPHA_SCALING","upper_bound_at_count_9":"","assumption":"finite candidate class with simultaneous or split evaluation"},
])
OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
assert [r["zero_event_required_count"] for r in rows[:3]] == [29,59,299]
assert abs((1-alpha**(1/9))-0.2831288)<1e-6
print("HIERARCHICAL_BOUND_TEST_PASS")
