#!/usr/bin/env python3
import math

def upper_zero(alpha, count):
    return 1-alpha**(1/count)

def required(alpha, delta):
    return math.ceil(math.log(alpha)/math.log(1-delta))

assert required(.05,.10)==29
assert required(.05,.05)==59
assert required(.05,.01)==299
assert upper_zero(.05,9) > .28
assert upper_zero(.05,59) <= .05
assert upper_zero(.05,58) > .05
print("HIERARCHICAL_BOUND_TEST_PASS")
