#!/usr/bin/env python3
"""Validate and checksum the frozen R0 candidate-log matrix."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compressed_rows(path: Path) -> int:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        header = next(csv.reader(stream))
        if not header:
            raise ValueError(f"{path}: empty header")
        return sum(1 for _ in stream)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_r0.yaml"))
    parser.add_argument("--raw", type=Path, default=Path("results/gb_mpcc/r0_candidates"))
    parser.add_argument(
        "--output", type=Path, default=Path("manifests/gb_mpcc_r0_candidates.json")
    )
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    records: list[dict[str, object]] = []
    for dataset in protocol["datasets"]:
        for seed in protocol["original_candidate_recording"]["build_seeds"]:
            run_id = f"{dataset['id']}-b{seed}"
            directory = args.raw / run_id
            metadata_path = directory / "metadata.json"
            candidate_path = directory / "insertion_candidates.csv.gz"
            adjacency_path = directory / "insertion_adjacency_changes.csv.gz"
            mapping_path = directory / "internal_to_external.csv"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("status") != "complete":
                raise ValueError(f"{run_id}: incomplete")
            if metadata.get("formal_test_members_accessed") is not False:
                raise ValueError(f"{run_id}: formal-test firewall failure")
            if metadata.get("accessed_hdf5_members") != ["train"]:
                raise ValueError(f"{run_id}: unexpected HDF5 member audit")
            candidate_rows = compressed_rows(candidate_path)
            adjacency_rows = compressed_rows(adjacency_path)
            if candidate_rows != metadata["candidate_rows"]:
                raise ValueError(f"{run_id}: candidate row count mismatch")
            if adjacency_rows != metadata["adjacency_change_rows"]:
                raise ValueError(f"{run_id}: adjacency row count mismatch")
            with mapping_path.open(newline="", encoding="utf-8") as stream:
                mapping = list(csv.DictReader(stream))
            internal = {int(row["internal_id"]) for row in mapping}
            external = {int(row["external_label"]) for row in mapping}
            expected = set(range(int(metadata["points"])))
            if internal != expected or external != expected:
                raise ValueError(f"{run_id}: insertion mapping is not a permutation")
            records.append(
                {
                    "run_id": run_id,
                    "dataset": dataset["id"],
                    "build_seed": seed,
                    "status": "complete",
                    "candidate_rows": candidate_rows,
                    "adjacency_change_rows": adjacency_rows,
                    "points": metadata["points"],
                    "dimensions": metadata["dimensions"],
                    "index_saved": False,
                    "accessed_hdf5_members": ["train"],
                    "formal_test_members_accessed": False,
                    "checksums": {
                        "metadata.json": sha256(metadata_path),
                        "insertion_candidates.csv.gz": sha256(candidate_path),
                        "insertion_adjacency_changes.csv.gz": sha256(adjacency_path),
                        "internal_to_external.csv": sha256(mapping_path),
                    },
                }
            )
    result = {
        "schema_version": 1,
        "protocol_sha256": sha256(args.protocol),
        "expected_runs": 9,
        "complete_runs": len(records),
        "failed_runs": 0,
        "formal_test_members_accessed": False,
        "runs": records,
    }
    if len(records) != 9:
        raise ValueError("R0 candidate matrix is incomplete")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "runs"}, indent=2))


if __name__ == "__main__":
    main()
