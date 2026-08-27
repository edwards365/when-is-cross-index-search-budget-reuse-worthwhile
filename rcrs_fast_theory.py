"""Discrete fast-sprint theory utilities; no ANN data access."""
import math
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

def safe_monotone_majorant(x, y):
    """Return f*(x_i), merging tied x by max y and taking prefix maxima."""
    x=np.asarray(x); y=np.asarray(y)
    levels=np.unique(x); tie_max=np.array([y[x==v].max() for v in levels])
    values=np.maximum.accumulate(tie_max)
    return np.array([values[np.searchsorted(levels,v)] for v in x]), dict(zip(levels.tolist(),values.tolist()))

def inversion_edges(x,y):
    x=np.asarray(x);y=np.asarray(y);out=[]
    for i in range(len(x)):
        for j in range(len(x)):
            if i!=j and x[i]<=x[j] and y[i]>y[j]:out.append((i,j,float(y[i]-y[j])))
    # identical unordered endpoints can arise from ties; retain maximum orientation/weight.
    best={}
    for i,j,w in out:
        k=tuple(sorted((i,j)));best[k]=max(best.get(k,0),w)
    return [(i,j,w) for (i,j),w in best.items()]

def max_weight_disjoint_inversion(x,y):
    """Exact maximum-weight matching formulated as a binary MILP."""
    edges=inversion_edges(x,y)
    if not edges:return 0.0,[]
    n=len(x); rows=[];cols=[]
    for e,(i,j,_) in enumerate(edges):rows.extend([i,j]);cols.extend([e,e])
    A=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,len(edges))).tocsr()
    res=milp(c=-np.array([e[2] for e in edges]),integrality=np.ones(len(edges)),bounds=Bounds(0,1),constraints=LinearConstraint(A,0,1),options={'time_limit':120})
    if not res.success:raise RuntimeError('maximum-weight inversion matching did not solve: '+res.message)
    chosen=[edges[i] for i,v in enumerate(res.x) if v>.5]
    return float(sum(e[2] for e in chosen)),chosen

def certification_n(delta,alpha):
    if not (0<delta<1 and 0<alpha<1):raise ValueError
    return math.ceil(math.log(alpha)/math.log(1-delta))

def break_even(calibration_cost,fixed_cost,online_cost):
    den=fixed_cost-online_cost
    return calibration_cost/den if den>0 else 'NO_FINITE_BREAK_EVEN_WORKLOAD'

