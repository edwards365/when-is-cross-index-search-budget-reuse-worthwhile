#!/usr/bin/env python3
import pathlib,sys
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/"src/asrc_semantic_repair"))
from safety_events import safety_events,failure_count

def check(a,y,c,za,zr):
    A,R,C=safety_events(a,y,c)
    assert A.tolist()==za and R.tolist()==zr and C.tolist()==list(c)

def main():
    check([1],[2],[False],[True],[True])       # insufficient, feasible
    check([2],[2],[False],[False],[False])     # sufficient, feasible
    check([11],[11],[True],[True],[False])     # endpoint-censored at max
    check([11],[11],[True],[True],[False])     # fixed endpoint itself fails
    check([11],[11],[False],[False],[False])   # safe fallback
    a=np.array([0,2,11]);y=np.array([1,2,11]);c=np.array([0,0,1],bool)
    assert failure_count(a,y,c)==2             # sentinel/eval common function
    A,R,_=safety_events(a,y,np.zeros(3,bool))
    assert np.array_equal(A,a<y) and np.array_equal(R,a<y) # no-censor regression
    try:safety_events([1],[1,2],[False]);raise AssertionError("shape guard")
    except ValueError:pass
    print("SAFETY_EVENT_TEST_PASS")

if __name__=="__main__":main()
