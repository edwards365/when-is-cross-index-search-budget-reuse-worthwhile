from pathlib import Path
import math
import tempfile

import pytest

from runtime_alignment import *


def test_01_tau_boundary_passes(): assert failure_z(.99, False, False) == 0
def test_02_below_tau_fails(): assert failure_z(.989, False, False) == 1
def test_03_endpoint_fails(): assert failure_z(1.0, True, False) == 1
def test_04_censor_fails(): assert failure_z(1.0, False, True) == 1
def test_05_first_sufficient_budget():
    rows=[{"budget":16,"recall":.98,"endpoint_infeasible":False,"right_censored":False},{"budget":32,"recall":.99,"endpoint_infeasible":False,"right_censored":False}]
    assert sufficient_budget(rows)==32
def test_06_max_budget_not_imputed():
    rows=[{"budget":384,"recall":.98,"endpoint_infeasible":False,"right_censored":False}]
    assert sufficient_budget(rows) is None
def test_07_cp_zero_failures_positive(): assert 0 < cp_upper(0,250,.05) < .05
def test_08_cp_all_failures_one(): assert cp_upper(10,10,.05)==1
def test_09_cp_rejects_bad_counts():
    with pytest.raises(ValueError): cp_upper(3,2,.05)
def test_10_bonferroni(): assert bonferroni_alpha(.05,7)==pytest.approx(.05/7)
def test_11_multiplicity_positive():
    with pytest.raises(ValueError): bonferroni_alpha(.05,0)
def test_12_roles_disjoint(): assert_disjoint_roles({r:[r] for r in ROLES})
def test_13_roles_overlap_rejected():
    d={r:[r] for r in ROLES}; d["evaluation"]=["x"]; d["certification"]=["x"]
    with pytest.raises(ValueError): assert_disjoint_roles(d)
def test_14_missing_role_rejected():
    with pytest.raises(ValueError): assert_disjoint_roles({"icba_selection":[]})
def test_15_cost_quantiles_from_vector():
    s=summarize_cost([1,2,3,100]); assert s["mean"]==26.5 and s["p95"]>3
def test_16_cost_scalar_rejected():
    with pytest.raises(ValueError): summarize_cost([])
def test_17_break_even_missing(): assert break_even(None,1)=="NOT_ESTIMABLE"
def test_18_break_even_nonpositive(): assert break_even(10,0)=="NO_FINITE_BREAK_EVEN"
def test_19_break_even_finite(): assert break_even(10,2)==5
def test_20_shared_cert_splits_alpha(): assert select_one_then_certify(0,0,250)[2]==.025
def test_21_separate_cert_keeps_alpha(): assert select_one_then_certify(0,0,250,False)[2]==.05
def test_22_registry_frozen(): assert [x["id"] for x in fixed_action_registry()]==[f"A{i}" for i in range(7)]
def test_23_certificate_roundtrip():
    u=cp_upper(0,250,.025)
    c=Certificate("t","b","A1","q","failure_Z","abc",TAU,DELTA,.05,2,250,0,u,"A6")
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"c.json"; c.serialize(p); assert p.exists()
def test_24_certificate_rejects_wrong_ucb():
    c=Certificate("t","b","A1","q","failure_Z","abc",TAU,DELTA,.05,2,250,0,.5,"A6")
    with pytest.raises(ValueError): c.validate()
