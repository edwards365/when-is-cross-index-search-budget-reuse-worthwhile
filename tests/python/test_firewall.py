from pathlib import Path

import h5py
import numpy as np
import pytest
from narhnsw.firewall import read_hdf5_rows


def test_development_hdf5_guard_allows_only_train(tmp_path: Path) -> None:
    path = tmp_path / "fixture.hdf5"
    with h5py.File(path, "w") as handle:
        handle["train"] = np.arange(12).reshape(6, 2)
        handle["test"] = np.arange(4).reshape(2, 2)
        handle["neighbors"] = np.arange(4).reshape(2, 2)
        handle["distances"] = np.arange(4).reshape(2, 2)
    observed = read_hdf5_rows(path, "train", slice(0, 2), role="development")
    assert observed.shape == (2, 2)
    for member in ("test", "neighbors", "distances"):
        with pytest.raises(PermissionError, match="sealed"):
            read_hdf5_rows(path, member, slice(None), role="development")


def test_formal_member_requires_both_role_and_explicit_enable(tmp_path: Path) -> None:
    path = tmp_path / "fixture.hdf5"
    with h5py.File(path, "w") as handle:
        handle["test"] = np.ones((2, 2))
    with pytest.raises(PermissionError, match="sealed"):
        read_hdf5_rows(path, "test", slice(None), role="formal_test")
    observed = read_hdf5_rows(
        path, "test", slice(None), role="formal_test", formal_enabled=True
    )
    assert observed.shape == (2, 2)
