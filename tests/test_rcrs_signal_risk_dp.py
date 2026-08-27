import numpy as np
from rcrs_signal_risk_dp import risk_monotone_dp,aware_risk_optimum
def test_delta_zero_is_safe_majorant():
 g=np.array([1,2,3]);x=np.array([1,2,3]);y=np.array([2,1,3]);c=np.tile(g,(3,1));r=risk_monotone_dp(x,y,c,g,0);assert r['mapping']=={1:2,2:2,3:3};assert r['failures']==0
def test_five_percent_budget():
 g=np.array([1,2]);x=np.arange(20);y=np.array([2]+[1]*19);c=np.tile(g,(20,1));r=risk_monotone_dp(x,y,c,g,.05);assert r['failures']<=1
def test_ties_share_allocation():
 g=np.array([1,2,3]);x=np.array([1,1,2]);y=np.array([1,3,2]);c=np.tile(g,(3,1));r=risk_monotone_dp(x,y,c,g,0);assert r['mapping'][1]==3 and r['mapping'][2]==3
def test_aware_not_worse_than_monotone():
 g=np.array([1,2,3]);x=np.array([1,2,3]);y=np.array([3,1,2]);c=np.tile(g,(3,1));m=risk_monotone_dp(x,y,c,g,0)['cost'];a=aware_risk_optimum(y,c,g,0);assert a<=m

