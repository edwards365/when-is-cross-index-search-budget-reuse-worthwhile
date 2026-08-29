"""Unified safety events for the ASRC semantic-repair stage."""
import numpy as np


def safety_events(allocation, required_budget, endpoint_infeasible):
    """Return (Z_abs, Z_rec, endpoint_infeasible).

    Z_abs is true when the allocation is below the required safe budget OR no
    observable safe endpoint exists.  Z_rec is true only for endpoint-feasible
    queries whose allocation is below the required safe budget.
    """
    a = np.asarray(allocation, dtype=int)
    y = np.asarray(required_budget, dtype=int)
    c = np.asarray(endpoint_infeasible, dtype=bool)
    if not (a.shape == y.shape == c.shape):
        raise ValueError("allocation, required_budget, and censoring must align")
    under = a < y
    return under | c, under & ~c, c


def failure_count(allocation, required_budget, endpoint_infeasible, risk="absolute"):
    z_abs, z_rec, _ = safety_events(allocation, required_budget, endpoint_infeasible)
    if risk == "absolute":
        return int(z_abs.sum())
    if risk == "recoverable":
        return int(z_rec.sum())
    raise ValueError("risk must be 'absolute' or 'recoverable'")
