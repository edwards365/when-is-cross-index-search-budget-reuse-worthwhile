import itertools
from icba_theory import monotone_majorant,brute_monotone
def test_majorant_matches_bruteforce_permutations():
 for n in range(2,8):
  x=range(n)
  for y in itertools.permutations(range(n)):
   pred,_=monotone_majorant(x,y); brute=brute_monotone(x,y,range(n))
   assert pred.sum()==brute[0]
def test_ties_use_cell_max_then_prefix_max():
 pred,_=monotone_majorant([0,0,1],[1,3,2]);assert pred.tolist()==[3,3,3]
