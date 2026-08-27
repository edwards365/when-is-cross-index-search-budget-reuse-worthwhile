"""Finite ICBA constructions used for exhaustive validation, not ANN I/O."""
from functools import lru_cache
import itertools, math
import numpy as np
from scipy.stats import beta, binom

def information_envelope(summary,target):
 s=np.asarray(summary); y=np.asarray(target); levels=np.unique(s)
 mp={int(v):int(y[s==v].max()) for v in levels}
 return np.array([mp[int(v)] for v in s]),mp

def monotone_majorant(source,target):
 s=np.asarray(source); y=np.asarray(target); levels=np.unique(s)
 cell=np.array([y[s==v].max() for v in levels]); vals=np.maximum.accumulate(cell)
 mp={int(v):int(z) for v,z in zip(levels,vals)}
 return np.array([mp[int(v)] for v in s]),mp

def inversion_matching_bound(source,target):
 s=np.asarray(source); y=np.asarray(target); n=len(s); edges={}
 for i in range(n):
  for j in range(i+1,n):
   if s[i]<s[j] and y[i]>y[j]:edges[i,j]=int(y[i]-y[j])
   elif s[j]<s[i] and y[j]>y[i]:edges[i,j]=int(y[j]-y[i])
 @lru_cache(None)
 def dp(mask):
  if not mask:return 0
  i=(mask&-mask).bit_length()-1; best=dp(mask&~(1<<i))
  rest=mask&~(1<<i)
  while rest:
   j=(rest&-rest).bit_length()-1;rest&=~(1<<j)
   best=max(best,edges.get(tuple(sorted((i,j))),0)+dp(mask&~(1<<i)&~(1<<j)))
  return best
 return dp((1<<n)-1)

def brute_monotone(source,target,grid,delta=0.0):
 s=np.asarray(source);y=np.asarray(target);levels=np.unique(s);k=math.floor(delta*len(y));best=None
 for actions in itertools.combinations_with_replacement(grid,len(levels)):
  mp=dict(zip(levels,actions));pred=np.array([mp[v] for v in s]);fail=int((pred<y).sum());cost=float(pred.sum())
  if fail<=k and (best is None or cost<best[0]):best=(cost,fail,actions)
 return best

def risk_monotone_dp(source,target,grid,delta=0.0):
 s=np.asarray(source);y=np.asarray(target);levels=np.unique(s);groups=[np.where(s==v)[0] for v in levels];k=math.floor(delta*len(y))
 st={(0,0):(0,())}
 for ids in groups:
  nxt={}
  for (last,f0),(cost,path) in st.items():
   for j in range(last,len(grid)):
    f=f0+int((grid[j]<y[ids]).sum())
    if f>k:continue
    key=(j,f);cand=(cost+len(ids)*grid[j],path+(grid[j],))
    if key not in nxt or cand[0]<nxt[key][0]:nxt[key]=cand
  st=nxt
 return None if not st else min((v[0],key[1],v[1]) for key,v in st.items())

def cp_upper(k,n,alpha):
 return 1.0 if k==n else float(beta.ppf(1-alpha,k+1,n-k))
def certification_k(n,m,alpha,delta):
 ok=[k for k in range(n+1) if cp_upper(k,n,alpha/m)<=delta]
 return max(ok) if ok else -1
def certification_power(n,m,alpha,delta,p):
 return float(binom.cdf(certification_k(n,m,alpha,delta),n,p))
