from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.stats import beta

TAU = 0.99
DELTA = 0.05
ALPHA = 0.05
GRID = (8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384)
ROLES = ("icba_selection", "certification", "evaluation", "future_confirm")


def failure_z(recall: float, endpoint_infeasible: bool, right_censored: bool) -> int:
    return int(recall < TAU or endpoint_infeasible or right_censored)


def sufficient_budget(rows: Sequence[Mapping[str, object]]) -> int | None:
    """First observed feasible budget meeting tau; endpoint is never imputed."""
    ordered = sorted(rows, key=lambda r: int(r["budget"]))
    for row in ordered:
        if failure_z(float(row["recall"]), bool(row["endpoint_infeasible"]), bool(row["right_censored"])) == 0:
            return int(row["budget"])
    return None


def cp_upper(failures: int, n: int, alpha: float) -> float:
    if not (0 <= failures <= n) or n <= 0 or not (0 < alpha < 1):
        raise ValueError("invalid binomial inputs")
    return 1.0 if failures == n else float(beta.ppf(1 - alpha, failures + 1, n - failures))


def bonferroni_alpha(alpha: float, multiplicity: int) -> float:
    if multiplicity < 1:
        raise ValueError("multiplicity must be positive")
    return alpha / multiplicity


def assert_disjoint_roles(role_ids: Mapping[str, Iterable[str]]) -> None:
    normalized = {role: set(map(str, ids)) for role, ids in role_ids.items()}
    missing = set(ROLES) - set(normalized)
    if missing:
        raise ValueError(f"missing roles: {sorted(missing)}")
    for i, left in enumerate(ROLES):
        for right in ROLES[i + 1 :]:
            overlap = normalized[left] & normalized[right]
            if overlap:
                raise ValueError(f"role overlap {left}/{right}: {sorted(overlap)[:3]}")


def summarize_cost(costs: Sequence[float]) -> dict[str, float]:
    values = np.asarray(costs, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("finite per-query cost vector required")
    return {
        "mean": float(np.mean(values)),
        "p50": float(np.quantile(values, 0.50)),
        "p95": float(np.quantile(values, 0.95)),
        "p99": float(np.quantile(values, 0.99)),
    }


def break_even(offline_cost: float | None, online_saving: float | None) -> float | str:
    if offline_cost is None or online_saving is None:
        return "NOT_ESTIMABLE"
    if online_saving <= 0:
        return "NO_FINITE_BREAK_EVEN"
    return float(offline_cost / online_saving)


def select_one_then_certify(
    selected_failures: int,
    fallback_failures: int,
    n: int,
    shared_certification_set: bool = True,
) -> tuple[bool, bool, float]:
    local_alpha = ALPHA / 2 if shared_certification_set else ALPHA
    return (
        cp_upper(selected_failures, n, local_alpha) <= DELTA,
        cp_upper(fallback_failures, n, local_alpha) <= DELTA,
        local_alpha,
    )


@dataclass(frozen=True)
class Certificate:
    target: str
    build: str
    action: str
    query_law: str
    event: str
    evidence_hash: str
    tau: float
    delta: float
    alpha: float
    multiplicity: int
    n: int
    failures: int
    ucb: float
    fallback: str

    def validate(self) -> None:
        if self.tau != TAU or self.delta != DELTA or self.alpha <= 0:
            raise ValueError("certificate constants invalid")
        if self.multiplicity < 1 or not (0 <= self.failures <= self.n):
            raise ValueError("certificate counts invalid")
        if not all((self.target, self.build, self.action, self.query_law, self.event, self.evidence_hash, self.fallback)):
            raise ValueError("certificate identity incomplete")
        expected = cp_upper(self.failures, self.n, self.alpha / self.multiplicity)
        if abs(expected - self.ucb) > 1e-12:
            raise ValueError("certificate UCB inconsistent")

    def serialize(self, path: Path) -> None:
        self.validate()
        path.write_text(json.dumps(asdict(self), sort_keys=True, indent=2) + "\n")


def evidence_hash(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p)):
        digest.update(str(path).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def fixed_action_registry() -> list[dict[str, str]]:
    return [
        {"id": "A0", "action": "DIRECT_REUSE"},
        {"id": "A1", "action": "SOURCE_EF_UP_ONE_RUNG"},
        {"id": "A2", "action": "TARGET_NEIGHBORHOOD_RECALIBRATION"},
        {"id": "A3", "action": "TARGET_FIXED_EF_FULL_GRID_PROFILING"},
        {"id": "A4", "action": "TARGET_RETRAIN", "status": "NOT_IMPLEMENTED_NOT_ESTIMABLE"},
        {"id": "A5", "action": "INDEPENDENTLY_CERTIFIED_FALLBACK"},
        {"id": "A6", "action": "REJECT_ABSTAIN_NO_SAFE_ACTION"},
    ]
