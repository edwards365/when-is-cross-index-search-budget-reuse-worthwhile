#!/usr/bin/env python
"""Run one immutable Gate-A build/query task through the native exact-NDC harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import struct
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import psutil
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))

from narhnsw.firewall import read_hdf5_rows  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_float_matrix(path: Path, values: np.ndarray) -> None:
    values = np.ascontiguousarray(values, dtype=np.float32)
    with path.open("wb") as handle:
        handle.write(struct.pack("<QQ", *values.shape))
        values.tofile(handle)


def write_u32_matrix(path: Path, values: np.ndarray) -> None:
    values = np.ascontiguousarray(values, dtype=np.uint32)
    with path.open("wb") as handle:
        handle.write(struct.pack("<QQ", *values.shape))
        values.tofile(handle)


def write_order(path: Path, values: np.ndarray) -> None:
    values = np.ascontiguousarray(values, dtype=np.uint32)
    with path.open("wb") as handle:
        handle.write(struct.pack("<Q", len(values)))
        values.tofile(handle)


def resolve_ef_values(config: dict[str, object], requested: str | None) -> list[int]:
    search = config["search"]
    if requested is None:
        return list(search["base_ef"])
    try:
        values = [int(value) for value in requested.split(",")]
    except ValueError as error:
        raise ValueError("ef values must be comma-separated integers") from error
    if not values or any(value <= 0 for value in values) or values != sorted(set(values)):
        raise ValueError("ef values must be positive, unique, and increasing")
    allowed = set(search["base_ef"]) | set(search["predeclared_midpoints"])
    if not set(values) <= allowed:
        raise ValueError("ef values must come from the frozen base grid or predeclared midpoints")
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--hardware-id")
    parser.add_argument("--ef-values")
    args = parser.parse_args()
    config_bytes = args.config.read_bytes()
    config_hash = hashlib.sha256(config_bytes).hexdigest()
    config = yaml.safe_load(config_bytes)
    ef_values = resolve_ef_values(config, args.ef_values)
    matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    matches = [row for row in matrix["runs"] if row["run_id"] == args.run_id]
    if len(matches) != 1:
        raise ValueError("run ID is absent or duplicated in the frozen matrix")
    task = matches[0]
    if task["config_sha256"] != config_hash or matrix["config_sha256"] != config_hash:
        raise ValueError("run matrix and config hashes differ")
    if config["formal"] or config["firewall"] != "sealed":
        raise PermissionError("Gate-A runner requires sealed development mode")
    if task["method"] == "original" and args.plan is not None:
        raise ValueError("Original must not receive a selection plan")
    if task["method"] != "original" and args.plan is None:
        raise ValueError("non-Original methods require a frozen plan")
    if args.plan is not None and not args.plan.is_file():
        raise FileNotFoundError(args.plan)
    if not args.executable.is_file():
        raise FileNotFoundError(args.executable)

    available_gib = psutil.virtual_memory().available / 2**30
    minimum_gib = float(config["runtime"]["minimum_free_ram_gib"])
    if available_gib < minimum_gib:
        raise MemoryError(
            f"available RAM {available_gib:.3f} GiB is below frozen minimum {minimum_gib:.3f} GiB"
        )
    output = REPO / config["runtime"]["raw_root"] / args.run_id
    if output.exists():
        raise FileExistsError("run output exists and will not be overwritten")
    output.mkdir(parents=True)
    started_utc = datetime.now(UTC).isoformat()
    dataset = config["datasets"][task["dataset"]]
    failure_path = output / "failure.json"

    try:
        base = read_hdf5_rows(
            REPO / dataset["source"],
            dataset["source_member"],
            slice(0, config["base_vectors"]),
            role="construction",
        ).astype(np.float32, copy=False)
        if dataset["normalized"]:
            base /= np.linalg.norm(base, axis=1, keepdims=True)
        queries = np.load(REPO / dataset["queries"], allow_pickle=False)
        truth = np.load(REPO / dataset["ground_truth"], allow_pickle=False)
        order = np.random.default_rng(task["build_seed"]).permutation(len(base)).astype(np.uint32)
        order_hash = hashlib.sha256(order.view(np.uint8)).hexdigest()
        plan_hash = sha256(args.plan) if args.plan is not None else None
        with tempfile.TemporaryDirectory(prefix="narhnsw-gatea-") as temporary:
            temporary_path = Path(temporary)
            points_path = temporary_path / "points.f32bin"
            queries_path = temporary_path / "queries.f32bin"
            truth_path = temporary_path / "truth.u32bin"
            order_path = temporary_path / "order.u32bin"
            write_float_matrix(points_path, base)
            write_float_matrix(queries_path, queries)
            write_u32_matrix(truth_path, truth)
            write_order(order_path, order)
            del base, queries, truth, order
            command = [
                str(args.executable.resolve()),
                str(points_path),
                str(order_path),
                str(queries_path),
                str(truth_path),
                str(args.plan.resolve()) if args.plan is not None else "-",
                "ip" if dataset["normalized"] else "l2",
                str(config["build"]["M"]),
                str(config["build"]["ef_construction"]),
                str(task["build_seed"]),
                task["dataset"],
                task["method"],
                str(task["control_seed"]) if task["control_seed"] is not None else "-",
                ",".join(str(value) for value in ef_values),
                str(config["search"]["warmup_queries"]),
                str(config["search"]["latency_rounds"]),
                config_hash,
                args.hardware_id or platform.node(),
                args.run_id,
                str(output.resolve()),
            ]
            environment = os.environ.copy()
            environment["OMP_NUM_THREADS"] = "1"
            environment["OPENBLAS_NUM_THREADS"] = "1"
            process = subprocess.Popen(
                command,
                cwd=REPO,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            observed = psutil.Process(process.pid)
            peak_rss = 0
            while process.poll() is None:
                try:
                    peak_rss = max(peak_rss, observed.memory_info().rss)
                except psutil.NoSuchProcess:
                    pass
                time.sleep(0.02)
            stdout, stderr = process.communicate()
            (output / "stdout.log").write_text(stdout, encoding="utf-8")
            (output / "stderr.log").write_text(stderr, encoding="utf-8")
            if process.returncode:
                raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)
        metadata_path = output / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.update(
            {
                "dataset": task["dataset"],
                "git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
                ).strip(),
                "started_utc": started_utc,
                "completed_utc": datetime.now(UTC).isoformat(),
                "peak_rss_bytes": peak_rss,
                "available_ram_gib_at_start": available_gib,
                "insertion_order_sha256": order_hash,
                "plan_sha256": plan_hash,
                "formal_test_members_accessed": False,
                "accessed_hdf5_members": ["train"],
                "status": "complete",
            }
        )
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(metadata, indent=2, sort_keys=True))
    except Exception as error:
        failure_path.write_text(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "started_utc": started_utc,
                    "failed_utc": datetime.now(UTC).isoformat(),
                    "formal_test_members_accessed": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise


if __name__ == "__main__":
    main()
