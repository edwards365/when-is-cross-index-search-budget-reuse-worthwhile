import itertools
from icba_theory import brute_monotone,risk_monotone_dp
def test_dp_matches_bruteforce():
 for n in range(2,8):
  x=[i%3 for i in range(n)]
  for y in itertools.product(range(3),repeat=n):
   for d in (0,.1,.25):
    assert risk_monotone_dp(x,y,range(3),d)==brute_monotone(x,y,range(3),d)
def test_delta_zero_reduces_to_safe():
 r=risk_monotone_dp([0,1],[2,0],range(3),0);assert r[1]==0
