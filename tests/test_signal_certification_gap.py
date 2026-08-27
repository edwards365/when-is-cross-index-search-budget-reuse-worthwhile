from sklearn.metrics import roc_auc_score
import numpy as np
def test_monotone_transform_same_auc_different_fixed_cutoff():
 y=np.array([1,1,0,0]);a=np.array([4,3,2,1]);b=a/5
 assert roc_auc_score(y,a)==roc_auc_score(y,b)==1
 assert (a>=.7).sum()!= (b>=.7).sum()
def test_high_auc_does_not_certify_tail():
 y=np.r_[np.ones(980),np.zeros(10),np.ones(10)]
 score=np.r_[np.full(980,.9),np.full(10,.8),np.full(10,.1)]
 assert roc_auc_score(y,score)>.98
 assert (y[score>=.8]==0).mean()>.005
