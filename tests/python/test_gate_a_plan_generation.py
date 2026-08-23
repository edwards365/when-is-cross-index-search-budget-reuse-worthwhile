import pytest

from scripts.gate_a.generate_plans import (
    requested_center_count,
    validate_complete_scope,
    worker_owns_shard,
)


def test_requested_center_count_distinguishes_validation_from_full_run() -> None:
    assert requested_center_count(100_000, None) == 100_000
    assert requested_center_count(100_000, 1_200) == 1_200
    with pytest.raises(ValueError, match="max centers"):
        requested_center_count(100_000, 0)


def test_completed_validation_cannot_satisfy_full_run_request() -> None:
    complete = {
        "config_sha256": "frozen",
        "centers": 1_200,
        "full_frozen_center_count": False,
    }
    validate_complete_scope(
        complete,
        config_hash="frozen",
        requested_centers=1_200,
        base_vectors=100_000,
    )
    with pytest.raises(ValueError, match="different center count"):
        validate_complete_scope(
            complete,
            config_hash="frozen",
            requested_centers=100_000,
            base_vectors=100_000,
        )


def test_completed_plan_rejects_inconsistent_full_marker() -> None:
    complete = {
        "config_sha256": "frozen",
        "centers": 100_000,
        "full_frozen_center_count": False,
    }
    with pytest.raises(ValueError, match="inconsistent full-run marker"):
        validate_complete_scope(
            complete,
            config_hash="frozen",
            requested_centers=100_000,
            base_vectors=100_000,
        )


def test_selection_workers_partition_shards_without_overlap() -> None:
    assignments = [
        [start for start in range(0, 1_000, 100) if worker_owns_shard(start, 100, worker, 3)]
        for worker in range(3)
    ]
    assert assignments == [[0, 300, 600, 900], [100, 400, 700], [200, 500, 800]]
    assert sorted(start for assignment in assignments for start in assignment) == list(
        range(0, 1_000, 100)
    )
    with pytest.raises(ValueError, match="worker index"):
        worker_owns_shard(0, 100, 3, 3)
