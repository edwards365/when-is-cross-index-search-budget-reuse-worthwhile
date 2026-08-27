import itertools
from icba_theory import information_envelope
def test_envelope_is_least_safe_for_all_small_cells():
 for n in range(2,7):
  for y in itertools.product(range(3),repeat=n):
   s=[i%2 for i in range(n)]; pred,mp=information_envelope(s,y)
   assert all(pred[i]>=y[i] for i in range(n))
   for cell,v in mp.items():assert v==max(y[i] for i in range(n) if s[i]==cell)
