#!/usr/bin/env python3
"""Precompute the frozen, query-independent E0 exact-64 neighbor cache."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from narhnsw.e0_plans import exact_local_neighbors


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_inputs(path: Path) -> dict[str, dict[str, Any]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest["formal_test_members_accessed"]:
        raise PermissionError("R0 input manifest violates the formal-test firewall")
    return {str(item["dataset"]): item for item in manifest["inputs"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_e0.yaml"))
    parser.add_argument(
        "--inputs", type=Path, default=Path("results/gb_mpcc/r0_inputs/manifest.json")
    )
    parser.add_argument("--output", type=Path, default=Path("results/gb_mpcc/e0/local_neighbors"))
    parser.add_argument("--block-size", type=int, default=128)
    args = parser.parse_args()

    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if protocol["firewall"]["formal_test_access"] != "forbidden":
        raise PermissionError("E0 formal-test firewall is open")
    inputs = load_inputs(args.inputs)
    args.output.mkdir(parents=True, exist_ok=True)
    neighbor_specification = protocol["state_distribution"]["local_neighbors"]
    if neighbor_specification != "exact_64_nonself_neighbors_in_first_10k_base":
        raise ValueError("E0 local-neighbor specification changed")
    summaries = []
    for dataset in protocol["datasets"]:
        dataset_id = str(dataset["id"])
        record = inputs[dataset_id]
        source = Path(record["path"])
        if sha256(source) != record["fbin_sha256"]:
            raise ValueError(f"{dataset_id}: frozen train input checksum mismatch")
        points = np.memmap(
            source,
            dtype=np.float32,
            mode="r",
            shape=(int(record["points"]), int(record["dimensions"])),
        )
        neighbor_ids, local_scales = exact_local_neighbors(
            points,
            64,
            block_size=args.block_size,
        )
        destination = args.output / f"{dataset_id}.npz"
        if destination.exists():
            raise FileExistsError(destination)
        np.savez_compressed(
            destination,
            neighbor_external_labels=neighbor_ids,
            local_scales=local_scales,
        )
        summaries.append(
            {
                "dataset": dataset_id,
                "points": len(points),
                "neighbors": neighbor_ids.shape[1],
                "minimum_local_scale": float(local_scales.min()),
                "maximum_local_scale": float(local_scales.max()),
                "cache_sha256": sha256(destination),
            }
        )
        print(json.dumps(summaries[-1], sort_keys=True), flush=True)
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "status": "complete",
                "datasets": summaries,
                "source": "frozen_train_prefix_fbin_only",
                "query_independent": True,
                "formal_test_members_accessed": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
