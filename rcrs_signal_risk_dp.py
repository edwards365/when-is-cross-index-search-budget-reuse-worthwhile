"""Exact discrete risk-matched monotone DP for a frozen budget grid."""
import numpy as np
def risk_monotone_dp(x,y,cost,grid,delta=.05):
 x=np.asarray(x);y=np.asarray(y);cost=np.asarray(cost);grid=np.asarray(grid);K=int(np.floor(delta*len(x)))
 levels=np.unique(x);groups=[np.where(x==v)[0] for v in levels];inf=float('inf')
 # state (last budget index, failures) -> (cost, path)
 st={(0,0):(0.0,[])}
 for ids in groups:
  ns={}
  for (last,f0),(prev,path) in st.items():
   for j in range(last,len(grid)):
    f=f0+int(np.sum(grid[j]<y[ids]));
    if f>K:continue
    val=prev+float(cost[ids,j].sum());key=(j,f)
    if key not in ns or val<ns[key][0]:ns[key]=(val,path+[j])
  st=ns
 if not st:raise RuntimeError('risk DP infeasible')
 (j,f),(value,path)=min(st.items(),key=lambda z:z[1][0]);mapping=dict(zip(levels.tolist(),[int(grid[z]) for z in path]))
 return {'cost':value/len(x),'failures':f,'failure_rate':f/len(x),'mapping':mapping}
def aware_risk_optimum(y,cost,grid,delta=.05):
 y=np.asarray(y);cost=np.asarray(cost);grid=np.asarray(grid);K=int(np.floor(delta*len(y)));safe=[];risky=[]
 for i in range(len(y)):
  ok=np.where(grid>=y[i])[0]
  safe_i=float(cost[i,ok].min()) if len(ok) else float('inf')
  bad=np.where(grid<y[i])[0];risk_i=float(cost[i,bad].min()) if len(bad) else safe_i
  safe.append(safe_i);risky.append(risk_i)
 if any(np.isinf(safe)):
  # Right-censored targets necessarily consume failure allowance on the frozen grid.
  mandatory=[i for i,v in enumerate(safe) if np.isinf(v)]
  if len(mandatory)>K:raise RuntimeError('aware optimum infeasible on frozen grid')
  for i in mandatory:safe[i]=risky[i]
  remaining=K-len(mandatory)
 else:remaining=K
 gains=sorted([max(0,safe[i]-risky[i]) for i in range(len(y)) if grid.max()>=y[i]],reverse=True)
 return (sum(safe)-sum(gains[:remaining]))/len(y)
