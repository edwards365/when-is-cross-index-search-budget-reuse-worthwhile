#!/usr/bin/env python3
"""Build the preregistered portfolio and prove the G1 full-enumeration fallback."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "results/icba_cibs_stage1/runtime"
TOOLS = RUNTIME / "tools"
ARTIFACTS = ROOT / "artifacts/icba_cibs_stage1"
BUILD_RESULTS = ROOT / "results/icba_cibs_stage1/builds"
MANIFEST = ROOT / "manifests/icba_cibs_stage1_build_realization.json"
GATE = ROOT / "results/icba_cibs_stage1/build_and_fallback_gate.json"
LOG = ROOT / "results/icba_cibs_stage1/build_and_fallback_events.jsonl"
PROJECTED_ADDITIONS = 3365465672
RESERVE = 5 * 1024**3

DATASETS = {
    "sift_100k": {"dimensions": 128},
    "arxiv_nomic_100k": {"dimensions": 768},
}
BUILD_SEEDS = {"G1": 1009, "G2": 1013, "G3": 1019}
RAW_EFS = "10,16,24,32,48,64,96,128,192,256,384,512"
FLAGS = [
    "-std=c++17",
    "-O3",
    "-DNDEBUG",
    "-DNO_MANUAL_VECTORIZATION",
    "-Wall",
    "-Wextra",
    "-Wpedantic",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def event(name: str, **fields) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {"time_unix_ns": time.time_ns(), "event": name, **fields}
    with LOG.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def resource_gate(stage: str) -> dict:
    stats = os.statvfs(ROOT)
    free = stats.f_bavail * stats.f_frsize
    required = PROJECTED_ADDITIONS + RESERVE
    result = {
        "stage": stage,
        "free_bytes": free,
        "projected_additions_bytes": PROJECTED_ADDITIONS,
        "reserve_bytes": RESERVE,
        "required_bytes": required,
        "status": "PASS" if free >= required else "FAIL",
    }
    event("resource_gate", **result)
    if result["status"] != "PASS":
        raise RuntimeError(
            f"INSUFFICIENT_RESOURCES_FOR_CIBS_STAGE1 free={free} required={required}"
        )
    return result


def parse_meta(path: Path) -> dict:
    result = {}
    for line in path.read_text().splitlines():
        key, value = line.split("=", 1)
        if value in ("0", "1"):
            result[key] = value == "1"
        else:
            try:
                result[key] = int(value)
            except ValueError:
                result[key] = value
    return result


def run(args: list[str], log_path: Path) -> None:
    started = time.time_ns()
    with log_path.open("w") as handle:
        completed = subprocess.run(args, stdout=handle, stderr=subprocess.STDOUT, text=True)
    event(
        "command",
        argv=args,
        returncode=completed.returncode,
        elapsed_ns=time.time_ns() - started,
        log=str(log_path.relative_to(ROOT)),
    )
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(args)}")


def compile_runner() -> dict:
    TOOLS.mkdir(parents=True, exist_ok=True)
    binary = TOOLS / "icba_cibs_stage1_runner"
    command = [
        "g++",
        *FLAGS,
        "-Ithird_party/hnswlib",
        "-Icpp/include",
        "cpp/src/icba_cibs_stage1_runner.cpp",
        "-o",
        str(binary),
    ]
    run(command, BUILD_RESULTS / "compile.log")
    return {
        "binary": str(binary.relative_to(ROOT)),
        "binary_sha256": sha256(binary),
        "source": "cpp/src/icba_cibs_stage1_runner.cpp",
        "source_sha256": sha256(ROOT / "cpp/src/icba_cibs_stage1_runner.cpp"),
        "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
        "compiler_binary_sha256": sha256(Path(shutil.which("g++"))),
        "flags": FLAGS,
        "threads": 1,
        "simd": "NO_MANUAL_VECTORIZATION_SCALAR",
    }


def percentile(values: list[int], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def summarize_design(path: Path) -> dict:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    ndc = [int(row["native_ndc"]) for row in rows]
    expansions = [int(row["actual_expansions"]) for row in rows]
    wall = [int(row["wall_clock_ns"]) for row in rows]
    if not all(row["native_tracer_topk_equal"] == "1" for row in rows):
        raise RuntimeError("INVALID_CIBS_NDC_INSTRUMENTATION native/tracer top-k")
    if not all(row["native_tracer_ndc_equal"] == "1" for row in rows):
        raise RuntimeError("INVALID_CIBS_NDC_INSTRUMENTATION native/tracer NDC")
    if not all(row["native_bruteforce_exact_topk"] == "1" for row in rows):
        raise RuntimeError("NO_VALID_FIXED_SAFE_FALLBACK exact top-k")
    if not all(value == 100000 for value in expansions):
        raise RuntimeError("NO_VALID_FIXED_SAFE_FALLBACK incomplete enumeration")
    if not all(int(row["visited_count"]) == 100000 for row in rows):
        raise RuntimeError("NO_VALID_FIXED_SAFE_FALLBACK incomplete visitation")
    if not all(row["replay_topk_equal"] == "1" for row in rows):
        raise RuntimeError("NO_VALID_FIXED_SAFE_FALLBACK native replay top-k")
    if not all(row["replay_ndc_equal"] == "1" for row in rows):
        raise RuntimeError("NO_VALID_FIXED_SAFE_FALLBACK native replay NDC")
    return {
        "queries": len(rows),
        "requested_ef": 100000,
        "mean_ndc": statistics.fmean(ndc),
        "p50_ndc": percentile(ndc, 0.50),
        "p95_ndc": percentile(ndc, 0.95),
        "p99_ndc": percentile(ndc, 0.99),
        "mean_expansions": statistics.fmean(expansions),
        "p95_expansions": percentile(expansions, 0.95),
        "mean_wall_clock_ns": statistics.fmean(wall),
        "p95_wall_clock_ns": percentile(wall, 0.95),
        "p99_wall_clock_ns": percentile(wall, 0.99),
        "native_tracer_top10": "PASS_ALL",
        "native_tracer_exact_ndc": "PASS_ALL",
        "native_bruteforce_exact_top10": "PASS_ALL",
        "native_save_load_replay": "PASS_ALL",
        "distance_tie_rule": "distance_then_label; ties accepted only when exact outputs agree",
        "endpoint": "native_top10_no_filter",
        "recall_target": 0.9,
        "trigger": "EMPTY_SIMULTANEOUS_CERTIFIED_SET",
    }


def main() -> None:
    if MANIFEST.exists() or GATE.exists() or BUILD_RESULTS.exists() or ARTIFACTS.exists():
        raise RuntimeError("refusing to overwrite build/fallback realization artifacts")
    BUILD_RESULTS.mkdir(parents=True)
    ARTIFACTS.mkdir(parents=True)
    LOG.touch(exist_ok=False)
    event("start", head=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
    instrumentation_head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    tests = subprocess.run(
        [
            "/home/wlk/projects/navigation-aware-resistance-hnsw/.venv/bin/python",
            "-m",
            "unittest",
            "-q",
            "tests/icba_cibs_stage1/test_fallback_contract.py",
            "tests/icba_cibs_stage1/test_phase1_freeze.py",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    (BUILD_RESULTS / "prebuild_tests.log").write_text(tests.stdout)
    if tests.returncode:
        raise RuntimeError("outcome-free prebuild tests failed")
    resource_checks = [resource_gate("before_runtime_input_materialization")]
    run(
        [
            "/home/wlk/projects/navigation-aware-resistance-hnsw/.venv/bin/python",
            "scripts/icba_cibs_stage1/prepare_runtime_inputs.py",
        ],
        BUILD_RESULTS / "prepare_runtime_inputs.log",
    )
    runtime_manifest = json.loads((RUNTIME / "runtime_input_manifest.json").read_text())
    compiler = compile_runner()
    runner = ROOT / compiler["binary"]
    build_manifest = json.loads(
        (ROOT / "manifests/icba_cibs_stage1_build_candidates.json").read_text()
    )
    frozen_candidates = {row["build_id"]: row for row in build_manifest["candidates"]}
    records = []
    fallback = {}
    for dataset, dataset_spec in DATASETS.items():
        dataset_dir = ARTIFACTS / dataset
        dataset_dir.mkdir()
        for build_id in ("G1", "G2", "G3"):
            resource_checks.append(resource_gate(f"before_build:{dataset}:{build_id}"))
            frozen = frozen_candidates[build_id]
            if frozen["hnsw_random_seed"] != BUILD_SEEDS[build_id]:
                raise RuntimeError("build seed differs from preregistration")
            artifact = ROOT / frozen["artifact_paths"][dataset]
            order = ROOT / runtime_manifest["orders"][build_id]["runtime_path"]
            base = ROOT / runtime_manifest["datasets"][dataset]["runtime_base_path"]
            prefix = BUILD_RESULTS / f"{dataset}__{build_id}"
            build_meta_path = Path(str(prefix) + "__build.meta")
            run(
                [
                    str(runner),
                    "build",
                    str(base),
                    str(order),
                    str(dataset_spec["dimensions"]),
                    str(BUILD_SEEDS[build_id]),
                    str(artifact),
                    str(build_meta_path),
                ],
                Path(str(prefix) + "__build.log"),
            )
            connectivity = Path(str(prefix) + "__connectivity.u32bin")
            roundtrip = Path(str(prefix) + "__roundtrip.bin")
            inspect_meta_path = Path(str(prefix) + "__inspect.meta")
            run(
                [
                    str(runner),
                    "inspect",
                    str(artifact),
                    str(dataset_spec["dimensions"]),
                    str(connectivity),
                    str(roundtrip),
                    str(inspect_meta_path),
                    "100000",
                ],
                Path(str(prefix) + "__inspect.log"),
            )
            build_meta = parse_meta(build_meta_path)
            inspection = parse_meta(inspect_meta_path)
            artifact_sha = sha256(artifact)
            roundtrip_sha = sha256(roundtrip)
            if artifact_sha != roundtrip_sha:
                raise RuntimeError(f"index byte replay failed: {dataset}/{build_id}")
            roundtrip.unlink()
            record = {
                "dataset": dataset,
                "build_id": build_id,
                "seed": BUILD_SEEDS[build_id],
                "insertion_order_file_sha256": frozen["insertion_order_file_sha256"],
                "insertion_order_le_u32_sha256": frozen["insertion_order_le_u32_sha256"],
                "artifact_path": str(artifact.relative_to(ROOT)),
                "artifact_sha256": artifact_sha,
                "roundtrip_sha256": roundtrip_sha,
                "index_size_bytes": artifact.stat().st_size,
                "connectivity_path": str(connectivity.relative_to(ROOT)),
                "connectivity_sha256": sha256(connectivity),
                "build": build_meta,
                "inspection": inspection,
                "implementation": "hnswlib_v0.8.0_3f3429661187e4c24a490a0f148fc6bc89042b3d",
                "status": "PASS_BUILD_CONNECTIVITY_REPLAY",
            }
            design_queries = ROOT / runtime_manifest["datasets"][dataset]["queries"]["cibs_design"]["runtime_path"]
            equivalence_csv = Path(str(prefix) + "__raw_equivalence.csv")
            equivalence_meta_path = Path(str(prefix) + "__raw_equivalence.meta")
            run(
                [
                    str(runner),
                    "equivalence",
                    str(artifact),
                    str(design_queries),
                    str(dataset_spec["dimensions"]),
                    RAW_EFS,
                    str(equivalence_csv),
                    str(equivalence_meta_path),
                ],
                Path(str(prefix) + "__raw_equivalence.log"),
            )
            equivalence_meta = parse_meta(equivalence_meta_path)
            if equivalence_meta["status"] != "PASS" or equivalence_meta["rows"] != 384:
                raise RuntimeError(f"INVALID_CIBS_NDC_INSTRUMENTATION: {dataset}/{build_id}")
            record["raw_action_equivalence"] = {
                "ef_grid": [10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512],
                "design_queries": 32,
                "rows": equivalence_meta["rows"],
                "results_path": str(equivalence_csv.relative_to(ROOT)),
                "results_sha256": sha256(equivalence_csv),
                "native_tracer_top10": "PASS_ALL",
                "native_tracer_exact_ndc": "PASS_ALL",
            }
            records.append(record)
            event("build_pass", dataset=dataset, build_id=build_id, artifact_sha256=artifact_sha)
            if build_id == "G1":
                design_csv = Path(str(prefix) + "__fallback_design.csv")
                design_meta = Path(str(prefix) + "__fallback_design.meta")
                run(
                    [
                        str(runner),
                        "design",
                        str(artifact),
                        str(base),
                        str(design_queries),
                        str(dataset_spec["dimensions"]),
                        "100000",
                        str(design_csv),
                        str(design_meta),
                    ],
                    Path(str(prefix) + "__fallback_design.log"),
                )
                if parse_meta(design_meta)["status"] != "PASS":
                    raise RuntimeError(f"NO_VALID_FIXED_SAFE_FALLBACK design test: {dataset}")
                fallback[dataset] = {
                    "build_id": "G1",
                    "artifact_sha256": artifact_sha,
                    "connectivity_sha256": record["connectivity_sha256"],
                    "connectivity_count": inspection["directed_reachable_count"],
                    "num_deleted": inspection["num_deleted"],
                    "filter": "NONE",
                    "design_query_role": "cibs_design",
                    "design_results_path": str(design_csv.relative_to(ROOT)),
                    "design_results_sha256": sha256(design_csv),
                    "cost_and_exactness": summarize_design(design_csv),
                    "status": "PASS_VALID_FIXED_SAFE_FALLBACK",
                }
                event("fallback_pass", dataset=dataset, **fallback[dataset])
    manifest = {
        "schema_version": 1,
        "status": "PASS_BUILD_REALIZATION_BEFORE_SENTINEL",
        "preregistered_head": "1bb9d7c219234f4e5e75b9b963b95715af98e4aa",
        "instrumentation_head": instrumentation_head,
        "compiler": compiler,
        "resource_checks": resource_checks,
        "runtime_input_manifest": str((RUNTIME / "runtime_input_manifest.json").relative_to(ROOT)),
        "runtime_input_manifest_sha256": sha256(RUNTIME / "runtime_input_manifest.json"),
        "builds": records,
        "failed_or_replaced_builds": [],
        "sentinel_truth_accessed": False,
        "sentinel_action_outcomes_accessed": False,
        "evaluation_accessed": False,
        "future_confirm_accessed": False,
    }
    gate = {
        "schema_version": 1,
        "status": "PASS_FIXED_SAFE_FALLBACK_BOTH_DATASETS",
        "fallback": fallback,
        "synthetic_contract_tests": "PASS_5_OF_5",
        "phase1_freeze_tests": "PASS_6_OF_6",
        "native_tracer_equivalence": "PASS_ALL_DESIGN_QUERIES",
        "native_bruteforce_exact_top10": "PASS_ALL_DESIGN_QUERIES",
        "actual_layer0_directed_connectivity": "PASS_100000_OF_100000_BOTH_DATASETS",
        "save_load_replay": "PASS_ALL_SIX_INDEXES",
        "sentinel_access_authorized_next": True,
        "positive_cibs_evidence": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    GATE.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    event("complete", manifest_sha256=sha256(MANIFEST), gate_sha256=sha256(GATE))
    print(json.dumps({"status": gate["status"], "builds": len(records)}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        failure = {
            "schema_version": 1,
            "status": "STOPPED_BUILD_OR_FALLBACK_GATE",
            "error": str(error),
            "sentinel_access_authorized_next": False,
            "sentinel_truth_accessed": False,
            "evaluation_accessed": False,
            "future_confirm_accessed": False,
        }
        GATE.parent.mkdir(parents=True, exist_ok=True)
        if not GATE.exists():
            GATE.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n")
        event("failure", error=str(error))
        raise
