#!/usr/bin/env python3
"""Reconstruct, trace, verify, and delete the frozen 9-run D0-D index pairs."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, BinaryIO

import yaml


MINIMUM_FREE_BYTES = 10 * 2**30


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stream_sha256(stream: BinaryIO) -> str:
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def decompressed_sha256(path: Path) -> str:
    with gzip.open(path, "rb") as stream:
        return stream_sha256(stream)


def check_disk(path: Path) -> float:
    free = shutil.disk_usage(path).free
    if free < MINIMUM_FREE_BYTES:
        raise OSError(f"free disk {free / 2**30:.3f} GiB below frozen 10 GiB gate")
    return free / 2**30


def run_checked(command: list[str], stdout: Path, stderr: Path) -> float:
    started = time.perf_counter()
    with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
        process = subprocess.run(command, stdout=out, stderr=err, check=False)
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command)
    return time.perf_counter() - started


def compress(source: Path, destination: Path) -> None:
    with source.open("rb") as input_stream, gzip.open(destination, "wb", compresslevel=6) as output:
        shutil.copyfileobj(input_stream, output, length=4 * 1024 * 1024)


def count_csv(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def execute(
    job: dict[str, Any],
    protocol: dict[str, Any],
    replay: Path,
    comparator: Path,
    train_inputs: dict[str, dict[str, Any]],
    search_inputs: dict[str, dict[str, Any]],
    e0: Path,
    output: Path,
    stop: threading.Event,
) -> dict[str, Any]:
    run_id = job["run_id"]
    final = output / "runs" / run_id
    marker = final / "COMPLETE.json"
    if marker.is_file():
        record = json.loads(marker.read_text(encoding="utf-8"))
        if record["status"] != "complete" or not record["temporary_indexes_deleted"]:
            raise ValueError(f"{run_id}: invalid existing marker")
        return record
    if stop.is_set():
        raise RuntimeError("D0-D stopped before job start")
    if final.exists():
        raise FileExistsError(f"refusing partial output {final}")
    check_disk(output)
    work = output / ".work" / run_id
    if work.exists():
        raise FileExistsError(f"refusing stale work directory {work}")
    logs = output / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    original = work / "original"
    primary = work / "primary"
    train = train_inputs[job["dataset"]]
    search = search_inputs[job["dataset"]]
    metric = "ip" if train["normalized"] else "l2"
    common = [
        str(Path(train["path"]).resolve()),
        str(train["points"]),
        str(train["dimensions"]),
        str(job["seed"]),
        "16",
        "100",
        metric,
    ]
    original_plan = e0 / "audits" / f"{run_id}-original-plan.csv"
    primary_plan = e0 / "plans" / run_id / "geometry_backbone_mpcc_R4.csv"
    original_seconds = run_checked(
        [str(replay.resolve()), *common, str(original_plan.resolve()), str(original.resolve())],
        logs / f"{run_id}.original.stdout.log",
        logs / f"{run_id}.original.stderr.log",
    )
    primary_seconds = run_checked(
        [str(replay.resolve()), *common, str(primary_plan.resolve()), str(primary.resolve())],
        logs / f"{run_id}.primary.stdout.log",
        logs / f"{run_id}.primary.stderr.log",
    )
    for method, directory in (("original_algorithm4", original), ("geometry_backbone_mpcc_R4", primary)):
        expected = e0 / "runs" / run_id / method
        if sha256(directory / "layer0_edges.csv") != decompressed_sha256(
            expected / "layer0_edges.csv.gz"
        ):
            raise ValueError(f"{run_id}/{method}: reconstructed edge bytes differ from E0")
        if sha256(directory / "internal_to_external.csv") != decompressed_sha256(
            expected / "internal_to_external.csv.gz"
        ):
            raise ValueError(f"{run_id}/{method}: reconstructed mapping differs from E0")
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        if not metadata["upper_checksum_equal"]:
            raise ValueError(f"{run_id}/{method}: upper checksum mismatch")

    trace_csv = work / "first_divergence.csv"
    trace_metadata = work / "trace_metadata.json"
    trace_seconds = run_checked(
        [
            str(comparator.resolve()),
            str((original / "index.bin").resolve()),
            str((primary / "index.bin").resolve()),
            str(Path(search["queries"]).resolve()),
            str(Path(search["truth"]).resolve()),
            metric,
            ",".join(map(str, protocol["firewall"]["ef_search"])),
            run_id,
            str(trace_csv.resolve()),
            str(trace_metadata.resolve()),
        ],
        logs / f"{run_id}.trace.stdout.log",
        logs / f"{run_id}.trace.stderr.log",
    )
    trace = json.loads(trace_metadata.read_text(encoding="utf-8"))
    if not trace["trace_matches_native_search"] or trace["formal_test_members_accessed"]:
        raise ValueError(f"{run_id}: invalid trace metadata")
    if count_csv(trace_csv) != trace["harmed_query_ef_pairs"]:
        raise ValueError(f"{run_id}: trace row count mismatch")

    final.mkdir(parents=True)
    compress(trace_csv, final / "first_divergence.csv.gz")
    shutil.copy2(trace_metadata, final / "trace_metadata.json")
    record = {
        "status": "complete",
        "run_id": run_id,
        "dataset": job["dataset"],
        "build_seed": job["seed"],
        "harmed_query_ef_pairs": trace["harmed_query_ef_pairs"],
        "original_reconstruction_seconds": original_seconds,
        "primary_reconstruction_seconds": primary_seconds,
        "trace_seconds": trace_seconds,
        "original_edges_exact_e0": True,
        "primary_edges_exact_e0": True,
        "mapping_exact_e0": True,
        "upper_checksums_equal": True,
        "trace_matches_native_search": True,
        "trace_sha256": sha256(final / "first_divergence.csv.gz"),
        "temporary_indexes_deleted": False,
        "new_ef_points": False,
        "validation_dev_accessed": False,
        "formal_test_members_accessed": False,
    }
    for index in (original / "index.bin", primary / "index.bin"):
        index.unlink()
    if any((directory / "index.bin").exists() for directory in (original, primary)):
        raise RuntimeError(f"{run_id}: temporary index deletion failed")
    record["temporary_indexes_deleted"] = True
    marker.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.rmtree(work)
    check_disk(output)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--protocol", type=Path, default=Path("preregistration/post_e0_d0_dfg.yaml")
    )
    parser.add_argument("--e0", type=Path, default=Path("results/gb_mpcc/e0"))
    parser.add_argument("--output", type=Path, default=Path("results/post_e0/d0d"))
    parser.add_argument("--replay", type=Path, default=Path("build-r0/hnsw_replay_layer0_plan"))
    parser.add_argument("--comparator", type=Path, default=Path("build-r0/hnsw_d0_compare_indexes"))
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_trace_or_diagnostic_graph_reconstruction":
        raise PermissionError("D0-D/F/G protocol not frozen")
    firewall = protocol["firewall"]
    if (
        firewall["validation_dev_access"] != "forbidden"
        or firewall["formal_test_access"] != "forbidden"
        or firewall["new_ef_points"] != "forbidden"
        or firewall["bep_implementation"] != "forbidden_before_total_d0_pass"
    ):
        raise PermissionError("D0-D firewall changed")
    parent = json.loads(Path(protocol["parent_manifest"]).read_text(encoding="utf-8"))
    if parent["status"] != protocol["parent_d0b_decision"]:
        raise ValueError("D0-B parent did not authorize D0-D")
    matrix = protocol["matrix"]
    if args.workers != matrix["maximum_parallel_reconstructions"] or args.workers != 3:
        raise ValueError("D0-D requires frozen maximum three workers")
    train_manifest = json.loads(
        Path("results/gb_mpcc/r0_inputs/manifest.json").read_text(encoding="utf-8")
    )
    search_manifest = json.loads(
        (args.e0 / "search_inputs" / "manifest.json").read_text(encoding="utf-8")
    )
    if train_manifest["formal_test_members_accessed"] or search_manifest[
        "formal_test_members_accessed"
    ]:
        raise PermissionError("input firewall violation")
    train_inputs = {item["dataset"]: item for item in train_manifest["inputs"]}
    search_inputs = {item["dataset"]: item for item in search_manifest["datasets"]}
    args.output.mkdir(parents=True, exist_ok=True)
    check_disk(args.output)
    jobs = [
        {"dataset": dataset, "seed": int(seed), "run_id": f"{dataset}-b{seed}"}
        for dataset in matrix["datasets"]
        for seed in matrix["build_seeds"]
    ]
    stop = threading.Event()
    records = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                execute,
                job,
                protocol,
                args.replay,
                args.comparator,
                train_inputs,
                search_inputs,
                args.e0,
                args.output,
                stop,
            ): job
            for job in jobs
        }
        for future in as_completed(futures):
            try:
                record = future.result()
            except BaseException:
                stop.set()
                for pending in futures:
                    pending.cancel()
                raise
            records.append(record)
            print(
                json.dumps(
                    {
                        "complete": len(records),
                        "expected": 9,
                        "run_id": record["run_id"],
                        "harmed": record["harmed_query_ef_pairs"],
                        "free_gib": check_disk(args.output),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    if len(records) != 9:
        raise RuntimeError("D0-D matrix incomplete")
    summary = {
        "status": "D0D_TRACE_MATRIX_COMPLETE",
        "runs": 9,
        "harmed_query_ef_pairs": sum(item["harmed_query_ef_pairs"] for item in records),
        "all_reconstructions_exact_e0": True,
        "all_traces_match_native_search": True,
        "all_temporary_indexes_deleted": True,
        "new_ef_points": False,
        "validation_dev_accessed": False,
        "formal_test_members_accessed": False,
        "records": sorted(records, key=lambda item: item["run_id"]),
    }
    (args.output / "matrix_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "records"}))


if __name__ == "__main__":
    main()
