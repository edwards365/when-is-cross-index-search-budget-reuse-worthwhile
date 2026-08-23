#!/usr/bin/env python
"""Generate resumable all-source Geometry/GGR/control plans for one Gate-A build."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import hnswlib
import numpy as np
import psutil
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))
sys.path.insert(0, str(REPO))

from narhnsw.controls import (  # noqa: E402
    geometry_safe_random_selection,
    shuffled_resistance_selection,
)
from narhnsw.firewall import read_hdf5_rows  # noqa: E402
from narhnsw.ggr import geometry_guarded_resistance_selection  # noqa: E402

from scripts.experiments.run_phase2_selector_audit import local_scheme_a  # noqa: E402


def array_sha256(values: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(np.ascontiguousarray(values).view(np.uint8))
    return digest.hexdigest()


def method_names(control_seeds: list[int]) -> list[str]:
    names = ["geometry", "ggr_0"]
    for seed in control_seeds:
        names.extend([f"geometry_safe_random_c{seed}", f"shuffled_resistance_c{seed}"])
    return names


def shard_complete(shard_root: Path, start: int, stop: int, methods: list[str]) -> bool:
    prefix = f"{start:06d}_{stop:06d}"
    return all((shard_root / f"{prefix}_{method}.csv").is_file() for method in methods) and (
        shard_root / f"{prefix}_audit.csv"
    ).is_file()


def requested_center_count(base_vectors: int, max_centers: int | None) -> int:
    if max_centers is None:
        return base_vectors
    if not 0 < max_centers <= base_vectors:
        raise ValueError("max centers must lie in [1, base_vectors]")
    return max_centers


def validate_complete_scope(
    complete: dict[str, object],
    *,
    config_hash: str,
    requested_centers: int,
    base_vectors: int,
) -> None:
    if complete.get("config_sha256") != config_hash:
        raise ValueError("completed plan uses a different config")
    if complete.get("centers") != requested_centers:
        raise ValueError("completed plan uses a different center count")
    expected_full = requested_centers == base_vectors
    if complete.get("full_frozen_center_count") is not expected_full:
        raise ValueError("completed plan has an inconsistent full-run marker")


def worker_owns_shard(
    start: int, shard_size: int, worker_index: int, worker_count: int
) -> bool:
    if worker_count <= 0 or not 0 <= worker_index < worker_count:
        raise ValueError("selection worker index must lie in [0, worker_count)")
    return (start // shard_size) % worker_count == worker_index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--build-seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shard-size", type=int, default=100)
    parser.add_argument("--max-centers", type=int)
    parser.add_argument("--selection-worker-index", type=int, default=0)
    parser.add_argument("--selection-worker-count", type=int, default=1)
    args = parser.parse_args()
    if not args.output.is_absolute():
        args.output = (REPO / args.output).resolve()
    config_bytes = args.config.read_bytes()
    config_hash = hashlib.sha256(config_bytes).hexdigest()
    config = yaml.safe_load(config_bytes)
    if config["formal"] or config["firewall"] != "sealed":
        raise PermissionError("plan generation requires sealed development mode")
    if args.dataset not in config["datasets"]:
        raise ValueError("dataset is not in the frozen config")
    if args.build_seed not in config["build"]["build_seeds"]:
        raise ValueError("build seed is not in the frozen config")
    if args.shard_size <= 0:
        raise ValueError("shard size must be positive")
    worker_owns_shard(
        0,
        args.shard_size,
        args.selection_worker_index,
        args.selection_worker_count,
    )
    available_gib = psutil.virtual_memory().available / 2**30
    minimum_gib = float(config["runtime"]["minimum_free_ram_gib"])
    if available_gib < minimum_gib:
        raise MemoryError(
            f"available RAM {available_gib:.3f} GiB is below frozen minimum {minimum_gib:.3f} GiB"
        )

    count = requested_center_count(config["base_vectors"], args.max_centers)
    complete_path = args.output / "complete.json"
    if complete_path.exists():
        complete = json.loads(complete_path.read_text(encoding="utf-8"))
        validate_complete_scope(
            complete,
            config_hash=config_hash,
            requested_centers=count,
            base_vectors=config["base_vectors"],
        )
        print(json.dumps(complete, indent=2, sort_keys=True))
        return
    args.output.mkdir(parents=True, exist_ok=True)
    shard_root = args.output / "shards"
    shard_root.mkdir(exist_ok=True)
    dataset = config["datasets"][args.dataset]
    methods = method_names(config["control_seeds"])
    started = time.perf_counter()
    started_utc = datetime.now(UTC).isoformat()
    base = read_hdf5_rows(
        REPO / dataset["source"],
        dataset["source_member"],
        slice(0, config["base_vectors"]),
        role="construction",
    ).astype(np.float32, copy=False)
    if dataset["normalized"]:
        base /= np.linalg.norm(base, axis=1, keepdims=True)
    order = np.random.default_rng(args.build_seed).permutation(len(base))
    index = hnswlib.Index(
        space="cosine" if dataset["normalized"] else "l2", dim=base.shape[1]
    )
    index.init_index(
        max_elements=len(base),
        M=config["build"]["M"],
        ef_construction=config["build"]["ef_construction"],
        random_seed=args.build_seed,
    )
    index.set_num_threads(config["build"]["threads"])
    build_started = time.perf_counter()
    index.add_items(base[order], order, num_threads=config["build"]["threads"])
    build_seconds = time.perf_counter() - build_started
    index.set_ef(config["ggr"]["candidate_count"] + 1)
    candidate_started = time.perf_counter()
    labels, _ = index.knn_query(
        base,
        k=config["ggr"]["candidate_count"] + 1,
        num_threads=config["build"]["threads"],
    )
    construction_neighbors = np.empty(
        (len(base), config["ggr"]["candidate_count"]), dtype=np.int64
    )
    for node, row in enumerate(labels):
        filtered = row[row != node][: config["ggr"]["candidate_count"]]
        if len(filtered) != config["ggr"]["candidate_count"]:
            raise RuntimeError("candidate query returned too few non-self labels")
        construction_neighbors[node] = filtered
    candidate_seconds = time.perf_counter() - candidate_started
    candidate_hash = array_sha256(construction_neighbors)
    process = psutil.Process()
    peak_rss = process.memory_info().rss
    selection_started = time.perf_counter()

    for start in range(0, count, args.shard_size):
        stop = min(start + args.shard_size, count)
        if not worker_owns_shard(
            start,
            args.shard_size,
            args.selection_worker_index,
            args.selection_worker_count,
        ):
            continue
        if shard_complete(shard_root, start, stop, methods):
            continue
        plan_rows = {method: [] for method in methods}
        audit_rows = []
        for center in range(start, stop):
            candidates = construction_neighbors[center]
            leverage = local_scheme_a(base, center, candidates, construction_neighbors)
            common = {
                "epsilon": config["ggr"]["epsilon"],
                "geometry_tolerance": config["ggr"]["geometry_tolerance"],
            }
            ggr = geometry_guarded_resistance_selection(
                base[center],
                base[candidates],
                leverage,
                config["build"]["M"],
                leverage_tolerance=config["ggr"]["leverage_tolerance"],
                **common,
            )
            results = {"geometry": ggr.geometry_selected, "ggr_0": ggr.selected}
            audit = {
                "geometry": (0, ggr.geometry_base, ggr.geometry_base),
                "ggr_0": (len(ggr.swaps), ggr.geometry_base, ggr.geometry_final),
            }
            for control_seed in config["control_seeds"]:
                offset_seed = control_seed + args.build_seed * 1_000_000 + center
                random_result = geometry_safe_random_selection(
                    base[center],
                    base[candidates],
                    config["build"]["M"],
                    requested_swaps=len(ggr.swaps),
                    seed=offset_seed,
                    **common,
                )
                shuffled_result = shuffled_resistance_selection(
                    base[center],
                    base[candidates],
                    leverage,
                    config["build"]["M"],
                    seed=offset_seed,
                    leverage_tolerance=config["ggr"]["leverage_tolerance"],
                    **common,
                ).selection
                random_name = f"geometry_safe_random_c{control_seed}"
                shuffled_name = f"shuffled_resistance_c{control_seed}"
                results[random_name] = random_result.selected
                results[shuffled_name] = shuffled_result.selected
                audit[random_name] = (
                    len(random_result.swaps),
                    random_result.geometry_base,
                    random_result.geometry_final,
                )
                audit[shuffled_name] = (
                    len(shuffled_result.swaps),
                    shuffled_result.geometry_base,
                    shuffled_result.geometry_final,
                )
            for method, selected in results.items():
                selected_array = np.asarray(selected, dtype=np.int64)
                target_labels = candidates[selected_array]
                plan_rows[method].extend(f"{center},{int(target)}\n" for target in target_labels)
                swap_steps, geometry_base, geometry_final = audit[method]
                audit_rows.append(
                    ",".join(
                        [
                            str(center),
                            method,
                            str(swap_steps),
                            str(len(set(selected) - set(ggr.geometry_selected))),
                            repr(geometry_base),
                            repr(geometry_final),
                            repr(float(leverage[selected_array].sum())),
                        ]
                    )
                    + "\n"
                )
        prefix = f"{start:06d}_{stop:06d}"
        for method, rows in plan_rows.items():
            temporary = shard_root / f".{prefix}_{method}.tmp"
            final = shard_root / f"{prefix}_{method}.csv"
            temporary.write_text("".join(rows), encoding="utf-8", newline="")
            os.replace(temporary, final)
        audit_temporary = shard_root / f".{prefix}_audit.tmp"
        audit_final = shard_root / f"{prefix}_audit.csv"
        audit_temporary.write_text("".join(audit_rows), encoding="utf-8", newline="")
        os.replace(audit_temporary, audit_final)
        peak_rss = max(peak_rss, process.memory_info().rss)
        print(f"completed centers [{start},{stop}) peak_rss={peak_rss}", flush=True)

    if args.selection_worker_count > 1:
        print(
            json.dumps(
                {
                    "selection_worker_index": args.selection_worker_index,
                    "selection_worker_count": args.selection_worker_count,
                    "worker_shards_complete": True,
                    "formal_test_members_accessed": False,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return

    plans_root = args.output / "plans"
    plans_root.mkdir(exist_ok=True)
    for method in methods:
        final = plans_root / f"{method}.csv"
        if final.exists():
            raise FileExistsError(f"final plan already exists without complete marker: {final}")
        with final.open("w", encoding="utf-8", newline="") as destination:
            for start in range(0, count, args.shard_size):
                stop = min(start + args.shard_size, count)
                destination.write(
                    (shard_root / f"{start:06d}_{stop:06d}_{method}.csv").read_text(
                        encoding="utf-8"
                    )
                )
    audit_path = args.output / "per_center.csv"
    with audit_path.open("w", encoding="utf-8", newline="") as destination:
        destination.write(
            "center,method,swap_steps,terminal_changed_edges,geometry_base,geometry_final,"
            "true_frozen_leverage_total\n"
        )
        for start in range(0, count, args.shard_size):
            stop = min(start + args.shard_size, count)
            destination.write(
                (shard_root / f"{start:06d}_{stop:06d}_audit.csv").read_text(
                    encoding="utf-8"
                )
            )
    complete = {
        "dataset": args.dataset,
        "build_seed": args.build_seed,
        "centers": count,
        "full_frozen_center_count": count == config["base_vectors"],
        "config_sha256": config_hash,
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "candidate_pool_sha256": candidate_hash,
        "build_seconds": build_seconds,
        "candidate_seconds": candidate_seconds,
        "selection_seconds": time.perf_counter() - selection_started,
        "total_seconds": time.perf_counter() - started,
        "peak_rss_bytes": peak_rss,
        "available_ram_gib_at_start": available_gib,
        "started_utc": started_utc,
        "completed_utc": datetime.now(UTC).isoformat(),
        "formal_test_members_accessed": False,
        "accessed_hdf5_members": ["train"],
        "plans": {
            method: {
                "path": str((plans_root / f"{method}.csv").relative_to(REPO)),
                "sha256": hashlib.sha256(
                    (plans_root / f"{method}.csv").read_bytes()
                ).hexdigest(),
            }
            for method in methods
        },
    }
    complete_path.write_text(
        json.dumps(complete, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(complete, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
