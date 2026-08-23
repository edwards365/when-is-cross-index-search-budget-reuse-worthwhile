#!/usr/bin/env python3
"""Run frozen R0 diagnostics by loading existing Original Gate-A indexes read-only."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import struct
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import yaml

DATASET_MAP = {
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
    values = np.ascontiguousarray(values, dtype=dtype)
    with path.open("wb") as stream:
        stream.write(struct.pack("<QQ", *values.shape))
        values.tofile(stream)


def free_gib(path: Path) -> float:
    return shutil.disk_usage(path).free / 2**30


def structural_sources(path: Path) -> dict[tuple[str, int], set[int]]:
    result: dict[tuple[str, int], set[int]] = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if "selected_external_labels" not in row:
                raise ValueError("structural replay lacks reproducible selection labels")
            key = (row["dataset"], int(row["build_seed"]))
            result.setdefault(key, set()).add(int(row["external_source_label"]))
    if len(result) != 9 or any(len(labels) != 256 for labels in result.values()):
        raise ValueError("structural event matrix is not 9 x 256")
    return result


def run_one(task: dict[str, Any], executable: Path, efs: list[int], output: Path) -> dict[str, Any]:
    run_id = task["run_id"]
    run_output = output / "raw" / run_id
    run_output.mkdir(parents=True, exist_ok=False)
    raw_csv = run_output / "matched_trace_states.csv"
    command = [
        str(executable.resolve()),
        str(Path(task["index"]).resolve()),
        str(Path(task["queries"]).resolve()),
        str(Path(task["truth"]).resolve()),
        str(Path(task["sources"]).resolve()),
        task["metric"],
        ",".join(map(str, efs)),
        str(raw_csv.resolve()),
    ]
    process = subprocess.run(command, text=True, capture_output=True, check=False)
    (run_output / "stdout.log").write_text(process.stdout, encoding="utf-8")
    (run_output / "stderr.log").write_text(process.stderr, encoding="utf-8")
    if process.returncode:
        raise subprocess.CalledProcessError(
            process.returncode, command, process.stdout, process.stderr
        )
    compressed = raw_csv.with_suffix(".csv.gz")
    with raw_csv.open("rb") as source, gzip.open(compressed, "wb", compresslevel=6) as target:
        shutil.copyfileobj(source, target, length=4 * 1024 * 1024)
    raw_csv.unlink()
    with gzip.open(compressed, "rt", encoding="utf-8", newline="") as stream:
        matched_rows = sum(1 for _ in csv.DictReader(stream))
    metadata = {
        "run_id": run_id,
        "dataset": task["dataset"],
        "build_seed": task["build_seed"],
        "status": "complete",
        "matched_trace_rows": matched_rows,
        "query_ids": [0, 500],
        "ef_search": efs,
        "index_loaded_read_only": True,
        "index_built_or_mutated": False,
        "formal_test_members_accessed": False,
        "trace_sha256": sha256(compressed),
    }
    (run_output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--addendum",
        type=Path,
        default=Path("preregistration/gb_mpcc_r0_trace_addendum.yaml"),
    )
    parser.add_argument(
        "--gate-a-config", type=Path, default=Path("configs/gate_a/gate_a_100k.yaml")
    )
    parser.add_argument(
        "--structural",
        type=Path,
        default=Path("results/gb_mpcc/r0_replay_trace_ready/per_event_selector.csv.gz"),
    )
    parser.add_argument("--executable", type=Path, default=Path("build-r0/hnsw_r0_trace_existing"))
    parser.add_argument("--output", type=Path, default=Path("results/gb_mpcc/r0_trace"))
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    addendum = yaml.safe_load(args.addendum.read_text(encoding="utf-8"))
    protocol = Path(addendum["parent_protocol"])
    if sha256(protocol) != addendum["parent_protocol_sha256"]:
        raise ValueError("parent R0 protocol hash mismatch")
    if addendum["status"] != "frozen_before_reading_query_trace_events":
        raise PermissionError("trace addendum is not frozen")
    if addendum["firewall"]["formal_test_access"] != "forbidden":
        raise PermissionError("formal-test firewall is not closed")
    if not args.executable.is_file():
        raise FileNotFoundError(args.executable)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    if free_gib(Path.cwd()) < 10:
        raise OSError("free storage is below the frozen 10 GiB safety gate")
    args.output.mkdir(parents=True)
    (args.output / "inputs").mkdir()
    (args.output / "raw").mkdir()

    config = yaml.safe_load(args.gate_a_config.read_text(encoding="utf-8"))
    sources = structural_sources(args.structural)
    inputs: dict[str, dict[str, Path]] = {}
    for r0_dataset, gate_dataset in DATASET_MAP.items():
        dataset = config["datasets"][gate_dataset]
        query_path = Path(dataset["queries"])
        truth_path = Path(dataset["ground_truth"])
        if sha256(query_path) != dataset["queries_sha256"]:
            raise ValueError(f"{r0_dataset}: design-dev query checksum mismatch")
        if sha256(truth_path) != dataset["ground_truth_sha256"]:
            raise ValueError(f"{r0_dataset}: design-dev truth checksum mismatch")
        queries = np.load(query_path, allow_pickle=False)[:500]
        truth = np.load(truth_path, allow_pickle=False)[:500, :10]
        query_bin = args.output / "inputs" / f"{r0_dataset}_queries.f32bin"
        truth_bin = args.output / "inputs" / f"{r0_dataset}_truth.u32bin"
        write_matrix(query_bin, queries, np.dtype(np.float32))
        write_matrix(truth_bin, truth, np.dtype(np.uint32))
        inputs[r0_dataset] = {"queries": query_bin, "truth": truth_bin}

    tasks: list[dict[str, Any]] = []
    for r0_dataset, gate_dataset in DATASET_MAP.items():
        dataset = config["datasets"][gate_dataset]
        metric = "ip" if dataset["normalized"] else "l2"
        for seed in addendum["index_policy"]["build_seeds"]:
            run_id = f"{r0_dataset}-b{seed}"
            index = Path(f"results/gate_a/raw/{gate_dataset}-original-b{seed}/index.bin")
            index_metadata = json.loads(
                (index.parent / "metadata.json").read_text(encoding="utf-8")
            )
            if (
                index_metadata["status"] != "complete"
                or index_metadata["method"] != "original"
                or index_metadata["build_seed"] != seed
                or index_metadata["formal_test_members_accessed"] is not False
            ):
                raise ValueError(f"{run_id}: existing index provenance check failed")
            source_path = args.output / "inputs" / f"{run_id}_sources.txt"
            source_path.write_text(
                "".join(f"{label}\n" for label in sorted(sources[(r0_dataset, seed)])),
                encoding="utf-8",
            )
            tasks.append(
                {
                    "run_id": run_id,
                    "dataset": r0_dataset,
                    "build_seed": seed,
                    "index": index,
                    "queries": inputs[r0_dataset]["queries"],
                    "truth": inputs[r0_dataset]["truth"],
                    "sources": source_path,
                    "metric": metric,
                }
            )

    efs = [int(value) for value in addendum["ef_search"]]
    records: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_one, task, args.executable, efs, args.output): task for task in tasks
        }
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            print(json.dumps(record, sort_keys=True), flush=True)
            if free_gib(Path.cwd()) < 10:
                raise OSError("free storage fell below the frozen 10 GiB safety gate")
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "complete_runs": len(records),
        "expected_runs": 9,
        "addendum_sha256": sha256(args.addendum),
        "structural_replay_sha256": sha256(args.structural),
        "existing_indexes_loaded_read_only": True,
        "index_built_or_mutated": False,
        "formal_test_members_accessed": False,
        "runs": sorted(records, key=lambda row: row["run_id"]),
    }
    if len(records) != 9:
        raise RuntimeError("trace diagnostic matrix is incomplete")
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in manifest.items() if key != "runs"}))


if __name__ == "__main__":
    main()
