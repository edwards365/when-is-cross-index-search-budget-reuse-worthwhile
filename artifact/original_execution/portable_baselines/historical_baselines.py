"""Unchanged cp/simple_decision from the frozen retrospective baseline analysis."""
from scipy.stats import beta
GRID=[10, 20, 40, 80, 120, 200, 400, 800, 1200, 1600, 2400]

def cp(x,n,alpha):
    return 1.0 if x==n else float(beta.ppf(1-alpha,x+1,n-x))


def simple_decision(hs,ns,hc,size,method):
    nsel=size
    eligible=[i for i in range(11) if cp(int((hs[i,:nsel]<10).sum()),nsel,.05/11)<=.05]
    idx=9 if method=='fixed1600' else (min(eligible,key=lambda i:(float(ns[i,:nsel].mean()),i)) if eligible else 10)
    ce=cp(int((hc[10,:size]<10).sum()),size,.025)
    cc=cp(int((hc[idx,:size]<10).sum()),size,.025)
    d='UNDEPLOYABLE' if ce>.05 else ('CANDIDATE' if cc<=.05 else 'ENDPOINT')
    return dict(candidate_index=idx,candidate_action=GRID[idx],decision=d,
                deployed_index=idx if d=='CANDIDATE' else (10 if d=='ENDPOINT' else -1),
                eligible_actions=[GRID[i] for i in eligible],cert_candidate_ucb=cc,cert_endpoint_ucb=ce,
                selection_n=0 if method=='fixed1600' else size,certification_n=size)


