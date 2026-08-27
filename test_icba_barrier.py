import numpy as np
def barrier(y,m,c):
 return sum(c[l]-c[l-1] for l in range(1,len(c)) if y<l<=m)
def test_telescoping_random_nonlinear_flat_and_weighted():
 rng=np.random.default_rng(991)
 for _ in range(5000):
  L=int(rng.integers(2,7));inc=rng.integers(0,20,L-1);c=np.empty(L);c[0]=rng.integers(0,10);c[1:]=c[0]+np.cumsum(inc)
  y=int(rng.integers(0,L));m=int(rng.integers(y,L));w=float(rng.random())
  assert np.isclose(w*barrier(y,m,c),w*(c[m]-c[y]))
def test_no_inversion_aliasing_can_tax():
 x=np.array([1,1]);y=np.array([1,2]);m=np.array([2,2]);c=np.array([0,1,5]);assert sum(c[mm]-c[yy] for yy,mm in zip(y,m))==4
def test_high_inversion_small_gap_and_rare_large_jump():
 assert barrier(1,2,np.array([0,1,1.01]))<barrier(1,2,np.array([0,1,100]))
