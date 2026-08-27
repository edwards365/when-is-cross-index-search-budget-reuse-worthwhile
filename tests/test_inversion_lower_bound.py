import itertools
from icba_theory import monotone_majorant,inversion_matching_bound
def test_linear_matching_bound_exhaustive():
 for n in range(2,9):
  x=range(n)
  for y in itertools.permutations(range(n)):
   pred,_=monotone_majorant(x,y); tax=int(sum(pred)-sum(y))
   assert inversion_matching_bound(x,y)<=tax
def test_tight_and_loose_examples():
 assert inversion_matching_bound([0,1],[2,0])==2
 y=[4,0,0];p,_=monotone_majorant(range(3),y);assert inversion_matching_bound(range(3),y)<sum(p)-sum(y)
