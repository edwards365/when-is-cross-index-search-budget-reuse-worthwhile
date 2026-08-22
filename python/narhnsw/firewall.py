"""Role-aware HDF5 access guard for sealed Phase-II development runs."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import h5py
import numpy as np

SplitRole = Literal["construction", "development", "formal_test"]
FORMAL_MEMBERS = frozenset({"test", "neighbors", "distances"})


def read_hdf5_rows(
    path: Path,
    member: str,
    rows: slice,
    *,
    role: SplitRole,
    formal_enabled: bool = False,
) -> np.ndarray:
    """Read an explicitly authorized member; sealed development rejects formal data."""

    if member in FORMAL_MEMBERS and (role != "formal_test" or not formal_enabled):
        raise PermissionError(f"formal HDF5 member is sealed: {member}")
    if role in {"construction", "development"} and member != "train":
        raise PermissionError(f"development access is restricted to train, got: {member}")
    with h5py.File(path, "r") as handle:
        return np.asarray(handle[member][rows])
