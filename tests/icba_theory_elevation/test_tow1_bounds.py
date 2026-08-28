#!/usr/bin/env python3
import math

def lower_bound(rho, tv):
    assert 0 <= rho <= 1 and 0 <= tv <= 1
    return rho * (1 - tv)

def pinsker_probe_bound(rho, k, kl):
    return rho * max(0.0, 1.0 - math.sqrt(k * kl / 2.0))

assert lower_bound(0.4, 0.0) == 0.4
assert lower_bound(0.4, 1.0) == 0.0
assert lower_bound(0.0, 0.2) == 0.0
assert pinsker_probe_bound(0.5, 0, 0.3) == 0.5
assert pinsker_probe_bound(0.5, 100, 1.0) == 0.0
assert pinsker_probe_bound(0.5, 4, 0.01) <= pinsker_probe_bound(0.5, 1, 0.01)
print("TOW1_BOUND_TEST_PASS")
