import math
from rcrs_fast_theory import *

def test_no_inversion():
 f,_=safe_monotone_majorant([1,2,3],[2,3,4]);assert list(f)==[2,3,4];assert max_weight_disjoint_inversion([1,2,3],[2,3,4])[0]==0
def test_reverse():
 f,_=safe_monotone_majorant([1,2,3,4],[4,3,2,1]);assert list(f)==[4,4,4,4];assert max_weight_disjoint_inversion([1,2,3,4],[4,3,2,1])[0]==4
def test_large_and_small_gap_differ():
 assert max_weight_disjoint_inversion([1,2],[10,1])[0]==9
 assert max_weight_disjoint_inversion([1,2],[2,1])[0]==1
def test_ties_merge_by_max():
 f,m=safe_monotone_majorant([1,1,2],[2,5,3]);assert list(f)==[5,5,5];assert m[1]==5
def test_matching_can_be_loose():
 f,_=safe_monotone_majorant([1,2,3],[5,1,1]);tax=sum(f-[5,1,1]);lb,_=max_weight_disjoint_inversion([1,2,3],[5,1,1]);assert lb<tax
def test_matching_tight():
 f,_=safe_monotone_majorant([1,2],[5,1]);tax=sum(f-[5,1]);lb,_=max_weight_disjoint_inversion([1,2],[5,1]);assert lb==tax
def test_certification_numbers():
 assert certification_n(.05,.05)==59;assert certification_n(.01,.05)==299;assert certification_n(.001,.05)==2995
def test_break_even():
 assert break_even(100,10,8)==50;assert break_even(100,10,10)=='NO_FINITE_BREAK_EVEN_WORKLOAD'

