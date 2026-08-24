#!/usr/bin/env python3
"""Run the frozen nine-run D0-E/F counterfactual matrix and delete indexes."""

from __future__ import annotations

import argparse
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
    with source.open("rb") as src, gzip.open(destination, "wb", compresslevel=6) as dst:
        shutil.copyfileobj(src, dst, length=4 * 1024 * 1024)


def execute(
    job: dict[str, Any], protocol: dict[str, Any], replay: Path, evaluator: Path,
    train_inputs: dict[str, dict[str, Any]], search_inputs: dict[str, dict[str, Any]],
    e0: Path, plans: Path, output: Path, stop: threading.Event,
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
        raise RuntimeError("D0-E/F stopped before job start")
    if final.exists():
        raise FileExistsError(f"refusing partial output {final}")
    check_disk(output)
    work = output / ".work" / run_id
    if work.exists():
        raise FileExistsError(f"refusing stale work directory {work}")
    logs = output / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    original, primary = work / "original", work / "primary"
    train, search = train_inputs[job["dataset"]], search_inputs[job["dataset"]]
    metric = "ip" if train["normalized"] else "l2"
    common = [str(Path(train["path"]).resolve()), str(train["points"]),
              str(train["dimensions"]), str(job["seed"]), "16", "100", metric]
    original_plan = e0 / "audits" / f"{run_id}-original-plan.csv"
    primary_plan = e0 / "plans" / run_id / "geometry_backbone_mpcc_R4.csv"
    original_seconds = run_checked(
        [str(replay.resolve()), *common, str(original_plan.resolve()), str(original.resolve())],
        logs / f"{run_id}.original.stdout.log", logs / f"{run_id}.original.stderr.log")
    primary_seconds = run_checked(
        [str(replay.resolve()), *common, str(primary_plan.resolve()), str(primary.resolve())],
        logs / f"{run_id}.primary.stdout.log", logs / f"{run_id}.primary.stderr.log")
    for method, directory in (("original_algorithm4", original),
                              ("geometry_backbone_mpcc_R4", primary)):
        expected = e0 / "runs" / run_id / method
        if sha256(directory / "layer0_edges.csv") != decompressed_sha256(expected / "layer0_edges.csv.gz"):
            raise ValueError(f"{run_id}/{method}: edge reconstruction differs from E0")
        if sha256(directory / "internal_to_external.csv") != decompressed_sha256(expected / "internal_to_external.csv.gz"):
            raise ValueError(f"{run_id}/{method}: mapping differs from E0")
        if not json.loads((directory / "metadata.json").read_text(encoding="utf-8"))["upper_checksum_equal"]:
            raise ValueError(f"{run_id}/{method}: upper checksum mismatch")
    result_csv, metadata = work / "counterfactual.csv", work / "metadata.json"
    evaluate_seconds = run_checked([
        str(evaluator.resolve()), str((original / "index.bin").resolve()),
        str((primary / "index.bin").resolve()), str(Path(search["queries"]).resolve()),
        str(Path(search["truth"]).resolve()), metric,
        ",".join(map(str, protocol["firewall"]["ef_search"])), run_id,
        str((original / "layer0_edges.csv").resolve()),
        str((primary / "layer0_edges.csv").resolve()), str((plans / run_id).resolve()),
        str(result_csv.resolve()), str(metadata.resolve())],
        logs / f"{run_id}.evaluate.stdout.log", logs / f"{run_id}.evaluate.stderr.log")
    meta = json.loads(metadata.read_text(encoding="utf-8"))
    if not meta["native_original_exact"] or not meta["native_primary_exact"]:
        raise ValueError(f"{run_id}: custom/native equivalence failed")
    expected_rows = 12 * len(protocol["firewall"]["ef_search"]) * 500 + 1
    with result_csv.open("rb") as stream:
        rows = sum(1 for _ in stream)
    if rows != expected_rows:
        raise ValueError(f"{run_id}: expected {expected_rows} CSV rows, found {rows}")
    final.mkdir(parents=True)
    compress(result_csv, final / "counterfactual.csv.gz")
    shutil.copy2(metadata, final / "metadata.json")
    record = {
        "status": "complete", "run_id": run_id, "dataset": job["dataset"],
        "build_seed": job["seed"], "rows": rows - 1,
        "original_reconstruction_seconds": original_seconds,
        "primary_reconstruction_seconds": primary_seconds,
        "evaluate_seconds": evaluate_seconds, "original_edges_exact_e0": True,
        "primary_edges_exact_e0": True, "mapping_exact_e0": True,
        "upper_checksums_equal": True, "native_original_exact": True,
        "native_primary_exact": True,
        "result_sha256": sha256(final / "counterfactual.csv.gz"),
        "temporary_indexes_deleted": False, "new_ef_points": False,
        "validation_dev_accessed": False, "formal_test_members_accessed": False,
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
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/post_e0_d0_dfg.yaml"))
    parser.add_argument("--e0", type=Path, default=Path("results/gb_mpcc/e0"))
    parser.add_argument("--plans", type=Path, default=Path("results/post_e0/d0f_plans"))
    parser.add_argument("--output", type=Path, default=Path("results/post_e0/d0ef"))
    parser.add_argument("--replay", type=Path, default=Path("build-r0/hnsw_replay_layer0_plan"))
    parser.add_argument("--evaluator", type=Path, default=Path("build-r0/hnsw_d0_counterfactual_search"))
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    firewall = protocol["firewall"]
    if (protocol["status"] != "frozen_before_trace_or_diagnostic_graph_reconstruction"
            or firewall["validation_dev_access"] != "forbidden"
            or firewall["formal_test_access"] != "forbidden"
            or firewall["new_ef_points"] != "forbidden"
            or firewall["bep_implementation"] != "forbidden_before_total_d0_pass"):
        raise PermissionError("D0-E/F frozen protocol or firewall changed")
    if args.workers != 3 or args.workers != protocol["matrix"]["maximum_parallel_reconstructions"]:
        raise ValueError("D0-E/F requires frozen maximum three workers")
    plan_summary = json.loads((args.plans / "matrix_summary.json").read_text(encoding="utf-8"))
    if plan_summary["status"] != "D0F_ADDBACK_PLANS_COMPLETE" or plan_summary["formal_test_members_accessed"]:
        raise ValueError("D0-F plans incomplete or unsafe")
    train_manifest = json.loads(Path("results/gb_mpcc/r0_inputs/manifest.json").read_text(encoding="utf-8"))
    search_manifest = json.loads((args.e0 / "search_inputs" / "manifest.json").read_text(encoding="utf-8"))
    if train_manifest["formal_test_members_accessed"] or search_manifest["formal_test_members_accessed"]:
        raise PermissionError("input firewall violation")
    train_inputs = {x["dataset"]: x for x in train_manifest["inputs"]}
    search_inputs = {x["dataset"]: x for x in search_manifest["datasets"]}
    args.output.mkdir(parents=True, exist_ok=True)
    check_disk(args.output)
    jobs = [{"dataset": dataset, "seed": int(seed), "run_id": f"{dataset}-b{seed}"}
            for dataset in protocol["matrix"]["datasets"] for seed in protocol["matrix"]["build_seeds"]]
    stop, records = threading.Event(), []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(execute, job, protocol, args.replay, args.evaluator,
                               train_inputs, search_inputs, args.e0, args.plans,
                               args.output, stop): job for job in jobs}
        for future in as_completed(futures):
            try:
                record = future.result()
            except BaseException:
                stop.set()
                for pending in futures:
                    pending.cancel()
                raise
            records.append(record)
            print(json.dumps({"complete": len(records), "expected": 9,
                              "run_id": record["run_id"],
                              "free_gib": check_disk(args.output)}, sort_keys=True), flush=True)
    if len(records) != 9:
        raise RuntimeError("D0-E/F matrix incomplete")
    summary = {"status": "D0EF_COUNTERFACTUAL_MATRIX_COMPLETE", "runs": 9,
               "rows": sum(x["rows"] for x in records),
               "all_reconstructions_exact_e0": True,
               "all_native_adjacency_checks_exact": True,
               "all_temporary_indexes_deleted": True, "new_ef_points": False,
               "validation_dev_accessed": False, "formal_test_members_accessed": False,
               "records": sorted(records, key=lambda x: x["run_id"])}
    (args.output / "matrix_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}))


if __name__ == "__main__":
    main()
