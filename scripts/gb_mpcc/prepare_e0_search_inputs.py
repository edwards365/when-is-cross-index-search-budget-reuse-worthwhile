#!/usr/bin/env python3
"""Prepare frozen E0 design-dev queries and exact 10K top-10 truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from narhnsw.ground_truth import exact_top_k


GATE_DATASET_IDS = {
    "sift_10k": "sift_100k",
    "glove100_10k": "glove100_100k",
    "arxiv_nomic_10k": "arxiv_nomic_100k",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_matrix(path: Path, values: np.ndarray, dtype: np.dtype[Any]) -> None:
    matrix = np.ascontiguousarray(values, dtype=dtype)
    if matrix.ndim != 2:
        raise ValueError("binary matrix must have exactly two dimensions")
    with path.open("xb") as stream:
        stream.write(struct.pack("<QQ", *matrix.shape))
        matrix.tofile(stream)


def load_frozen_inputs(path: Path) -> dict[str, dict[str, Any]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest["formal_test_members_accessed"]:
        raise PermissionError("frozen train manifest violates formal-test firewall")
    return {str(record["dataset"]): record for record in manifest["inputs"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_e0.yaml"))
    parser.add_argument(
        "--gate-config", type=Path, default=Path("configs/gate_a/gate_a_100k.yaml")
    )
    parser.add_argument(
        "--inputs", type=Path, default=Path("results/gb_mpcc/r0_inputs/manifest.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/gb_mpcc/e0/search_inputs")
    )
    args = parser.parse_args()

    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    firewall = protocol["firewall"]
    if (
        firewall["formal_test_access"] != "forbidden"
        or firewall["validation_dev_access"] != "forbidden"
        or firewall["query_or_truth_may_affect_construction"] is not False
        or protocol["formal_test_gate"] != "closed"
    ):
        raise PermissionError("E0 query firewall is not frozen closed")
    query_range = protocol["design_dev"]["query_ids"]
    if query_range != {"start_inclusive": 0, "stop_exclusive": 500}:
        raise ValueError("E0 frozen query range changed")
    if protocol["design_dev"]["truth"] != "exact_top10_over_same_first_10k_normalized_base":
        raise ValueError("E0 truth definition changed")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    gate = yaml.safe_load(args.gate_config.read_text(encoding="utf-8"))
    if gate["formal"] is not False or gate["firewall"] != "sealed":
        raise PermissionError("Gate-A design-dev source is not sealed")
    inputs = load_frozen_inputs(args.inputs)
    args.output.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    for dataset in protocol["datasets"]:
        dataset_id = str(dataset["id"])
        gate_record = gate["datasets"][GATE_DATASET_IDS[dataset_id]]
        query_path = Path(gate_record["queries"])
        if sha256(query_path) != gate_record["queries_sha256"]:
            raise ValueError(f"{dataset_id}: frozen design-dev query checksum mismatch")
        queries = np.load(query_path, allow_pickle=False)[:500]
        if queries.shape != (500, int(dataset["dimensions"])):
            raise ValueError(f"{dataset_id}: invalid design-dev query shape")

        input_record = inputs[dataset_id]
        base_path = Path(input_record["path"])
        if sha256(base_path) != input_record["fbin_sha256"]:
            raise ValueError(f"{dataset_id}: frozen 10K base checksum mismatch")
        base = np.memmap(
            base_path,
            dtype=np.float32,
            mode="r",
            shape=(int(input_record["points"]), int(input_record["dimensions"])),
        )
        if base.shape != (10000, int(dataset["dimensions"])):
            raise ValueError(f"{dataset_id}: frozen base shape changed")
        labels, distances = exact_top_k(base, queries, 10, metric="l2")
        if labels.min() < 0 or labels.max() >= 10000 or not np.isfinite(distances).all():
            raise ValueError(f"{dataset_id}: invalid exact truth")

        query_output = args.output / f"{dataset_id}_queries.f32bin"
        truth_output = args.output / f"{dataset_id}_truth.u32bin"
        distance_output = args.output / f"{dataset_id}_truth_distances.f64.npy"
        write_matrix(query_output, queries, np.dtype("<f4"))
        write_matrix(truth_output, labels, np.dtype("<u4"))
        np.save(distance_output, distances, allow_pickle=False)
        records.append(
            {
                "dataset": dataset_id,
                "query_ids": [0, 500],
                "queries": query_output.as_posix(),
                "queries_sha256": sha256(query_output),
                "truth": truth_output.as_posix(),
                "truth_sha256": sha256(truth_output),
                "truth_distances": distance_output.as_posix(),
                "truth_distances_sha256": sha256(distance_output),
                "truth_base_vectors": 10000,
                "truth_k": 10,
                "truth_metric": "squared_l2_float64_stable_external_label_tie",
                "normalized": bool(dataset["normalized"]),
                "source_role": "frozen_design_dev_only",
                "formal_test_members_accessed": False,
                "validation_dev_accessed": False,
            }
        )
        print(json.dumps(records[-1], sort_keys=True), flush=True)

    manifest = {
        "schema_version": 1,
        "status": "complete",
        "protocol_sha256": sha256(args.protocol),
        "query_count": 500,
        "truth_k": 10,
        "datasets": records,
        "construction_accessed_queries_or_truth": False,
        "validation_dev_accessed": False,
        "formal_test_members_accessed": False,
        "e1_authorized": False,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
