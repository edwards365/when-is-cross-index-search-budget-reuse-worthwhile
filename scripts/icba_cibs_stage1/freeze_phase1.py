#!/usr/bin/env python3
"""Freeze Stage-I query roles, insertion orders, and preregistration without truth access."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
PRIMARY = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
HARDNESS = Path("/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k")
OUT = ROOT / "results/icba_cibs_stage1/phase1"
QUERY_OUT = OUT / "query_roles"
BUILD_OUT = OUT / "build_preregistration"
MANIFEST = ROOT / "manifests/icba_cibs_stage1_phase1_preregistration.json"
ROLE_MANIFEST = ROOT / "manifests/icba_cibs_stage1_query_roles.json"
BUILD_MANIFEST = ROOT / "manifests/icba_cibs_stage1_build_candidates.json"

MASTER_SEED = 20260831
BASE_COUNT = 100000
ROLE_SIZES = {
    "cibs_design": 32,
    "cibs_sentinel": 256,
    "cibs_evaluation": 500,
    "cibs_future_confirm": 244,
}
ROLE_ORDER = tuple(ROLE_SIZES)
BUILD_SEEDS = (1009, 1013, 1019)
INSERTION_SEEDS = (2026083101, 2026083102, 2026083103)
RAW_EF_GRID = (10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512)
PROJECTED_ADDITIONS = 3365465672
RESERVE = 5 * 1024**3

DATASETS = {
    "sift_100k": {
        "source": PRIMARY / "data/raw/sift-128-euclidean.hdf5",
        "source_manifest_sha256": "dd6f0a6ed6b7ebb8934680f861a33ed01ff33991eaee4fd60914d854a0ca5984",
        "train_count": 1000000,
        "dimensions": 128,
        "normalized": False,
        "base_content_sha256": "d0ad618c42429e9e2261e37e7ecaf042af58e47117ad62d5935457e129d0ab21",
        "historical_source_ids": [
            ROOT / "results/hardness_portability_100k/query_inputs/sift_100k_source_ids.npy",
            HARDNESS / "results/cross_index/g1/query_inputs/sift_100k_source_ids.npy",
            HARDNESS / "results/rebuild_tax/validation_inputs/sift_100k_source_ids.npy",
            PRIMARY / "results/raw/phase2_gatea_development_data_v2/sift-128-euclidean_query_source_ids.npy",
        ],
    },
    "arxiv_nomic_100k": {
        "source": PRIMARY / "data/raw/arxiv-nomic-768-normalized.hdf5",
        "source_manifest_sha256": "8be0993b978b0d0ef023d21d878251a5ed09e058adb25994553c08388d37d414",
        "train_count": 1344643,
        "dimensions": 768,
        "normalized": True,
        "base_content_sha256": "9fc6c6e71329832643a6c1e57eecd32e632bf90b1a5a4bed83587dbab70de107",
        "historical_source_ids": [
            ROOT / "results/hardness_portability_100k/query_inputs/arxiv_nomic_100k_source_ids.npy",
            HARDNESS / "results/cross_index/g1/query_inputs/arxiv_nomic_100k_source_ids.npy",
            HARDNESS / "results/rebuild_tax/validation_inputs/arxiv_nomic_100k_source_ids.npy",
            PRIMARY / "results/raw/phase2_gatea_development_data_v2/arxiv-nomic-768-normalized_query_source_ids.npy",
        ],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def payload_sha_i64(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values, dtype="<i8").tobytes()).hexdigest()


def payload_sha_u32(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values, dtype="<u4").tobytes()).hexdigest()


def relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def save_npy_new(path: Path, value: np.ndarray) -> None:
    if path.exists():
        raise RuntimeError(f"refusing to overwrite frozen artifact: {path}")
    np.save(path, value, allow_pickle=False)


def resource_gate() -> dict:
    stats = os.statvfs(ROOT)
    free = stats.f_bavail * stats.f_frsize
    required = PROJECTED_ADDITIONS + RESERVE
    if free < required:
        raise RuntimeError(
            f"INSUFFICIENT_RESOURCES_FOR_CIBS_STAGE1 free={free} required={required}"
        )
    return {
        "free_bytes": free,
        "projected_additions_bytes": PROJECTED_ADDITIONS,
        "reserve_bytes": RESERVE,
        "required_bytes": required,
        "headroom_bytes": free - required,
        "status": "PASS",
    }


def freeze_query_roles() -> dict:
    QUERY_OUT.mkdir(parents=True, exist_ok=False)
    records = {}
    total_needed = sum(ROLE_SIZES.values())
    for dataset_offset, (dataset, spec) in enumerate(DATASETS.items()):
        historical = set()
        historical_records = []
        for path in spec["historical_source_ids"]:
            if not path.is_file():
                raise RuntimeError(f"historical source-ID artifact missing: {path}")
            ids = np.load(path, allow_pickle=False).astype(np.int64)
            historical.update(map(int, ids))
            historical_records.append(
                {
                    "path": str(path),
                    "sha256": sha256(path),
                    "count": int(ids.size),
                }
            )

        source = spec["source"]
        with h5py.File(source, "r") as handle:
            shape = tuple(handle["train"].shape)
            if shape != (spec["train_count"], spec["dimensions"]):
                raise RuntimeError(f"unexpected train shape for {dataset}: {shape}")
            eligible = np.setdiff1d(
                np.arange(BASE_COUNT, spec["train_count"], dtype=np.int64),
                np.fromiter(historical, dtype=np.int64),
                assume_unique=False,
            )
            rng = np.random.Generator(np.random.PCG64(MASTER_SEED + dataset_offset))
            selected = rng.choice(eligible, total_needed, replace=False).astype(np.int64)
            vectors = np.asarray(handle["train"][np.sort(selected)], dtype=np.float32)
            reorder = np.searchsorted(np.sort(selected), selected)
            vectors = vectors[reorder]

        if spec["normalized"]:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise RuntimeError(f"zero norm query in {dataset}")
            vectors = np.asarray(vectors / norms, dtype=np.float32)
        vector_hashes = [
            hashlib.sha256(np.ascontiguousarray(row).tobytes()).hexdigest()
            for row in vectors
        ]
        if len(set(map(int, selected))) != total_needed:
            raise RuntimeError(f"duplicate source IDs in {dataset}")
        if len(set(vector_hashes)) != total_needed:
            raise RuntimeError(f"duplicate query vectors in {dataset}")
        if set(map(int, selected)) & historical:
            raise RuntimeError(f"historical source-ID overlap in {dataset}")
        if np.any(selected < BASE_COUNT):
            raise RuntimeError(f"base/query source-ID overlap in {dataset}")

        cursor = 0
        role_records = {}
        role_sets = {}
        for role in ROLE_ORDER:
            size = ROLE_SIZES[role]
            role_ids = selected[cursor : cursor + size]
            role_vectors = vectors[cursor : cursor + size]
            cursor += size
            ids_path = QUERY_OUT / f"{dataset}__{role}__source_ids.npy"
            query_path = QUERY_OUT / f"{dataset}__{role}__queries.npy"
            save_npy_new(ids_path, role_ids.astype(np.int64))
            save_npy_new(query_path, role_vectors.astype(np.float32))
            role_sets[role] = set(map(int, role_ids))
            role_records[role] = {
                "count": size,
                "source_ids_path": relative_or_absolute(ids_path),
                "source_ids_file_sha256": sha256(ids_path),
                "ordered_source_ids_le_i64_sha256": payload_sha_i64(role_ids),
                "queries_path": relative_or_absolute(query_path),
                "queries_file_sha256": sha256(query_path),
                "dimensions": spec["dimensions"],
                "truth_accessed_at_freeze": False,
                "action_outcome_accessed_at_freeze": False,
            }
        overlaps = {
            f"{left}__{right}": len(role_sets[left] & role_sets[right])
            for i, left in enumerate(ROLE_ORDER)
            for right in ROLE_ORDER[i + 1 :]
        }
        if any(overlaps.values()):
            raise RuntimeError(f"role overlap in {dataset}: {overlaps}")
        records[dataset] = {
            "source_hdf5": str(source),
            "source_member_read": "train",
            "source_sha256_provenance": "frozen manifest; physical HDF5 not rehashed because sealed members share container",
            "source_manifest_sha256": spec["source_manifest_sha256"],
            "base_content_sha256": spec["base_content_sha256"],
            "base_source_id_range": [0, BASE_COUNT - 1],
            "normalization": "unit_l2_float32" if spec["normalized"] else "none_float32",
            "historical_source_id_artifacts": historical_records,
            "known_historical_source_id_union_count": len(historical),
            "selected_historical_source_id_overlap": 0,
            "selected_base_source_id_overlap": 0,
            "roles": role_records,
            "pairwise_source_id_overlap": overlaps,
        }

    access_log = QUERY_OUT / "truth_access_log.csv"
    with access_log.open("x", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "dataset",
                "role",
                "query_vectors_materialized",
                "truth_accessed",
                "action_outcome_accessed",
                "next_permitted_access",
            )
        )
        for dataset in DATASETS:
            for role in ROLE_ORDER:
                next_access = {
                    "cibs_design": "FALLBACK_DESIGN_TEST_ONLY",
                    "cibs_sentinel": "AFTER_BUILD_AND_FALLBACK_GATES",
                    "cibs_evaluation": "AFTER_SELECTED_ACTION_MANIFEST_FREEZE",
                    "cibs_future_confirm": "NEVER_IN_STAGE_I",
                }[role]
                writer.writerow((dataset, role, 1, 0, 0, next_access))
    return {
        "schema_version": 1,
        "status": "FROZEN_BEFORE_STAGE1_TRUTH_OR_ACTION_OUTCOMES",
        "master_seed": MASTER_SEED,
        "rng": "numpy.random.Generator(PCG64)",
        "semantics": "FROZEN_FINITE_POOL_WITHOUT_REPLACEMENT",
        "inference_scope": "conditional_on_the_frozen_finite_query_pool_and_one_registered_build_portfolio",
        "role_sizes": ROLE_SIZES,
        "datasets": records,
        "truth_access_log": relative_or_absolute(access_log),
        "truth_access_log_sha256": sha256(access_log),
        "historical_action_results_consulted": False,
        "validation_dev_accessed": False,
        "formal_test_accessed": False,
        "certification_reserved_accessed": False,
        "evaluation_reserved_accessed": False,
        "future_confirm_accessed": False,
    }


def freeze_builds() -> dict:
    BUILD_OUT.mkdir(parents=True, exist_ok=False)
    candidates = []
    for index, (build_seed, insertion_seed) in enumerate(
        zip(BUILD_SEEDS, INSERTION_SEEDS), start=1
    ):
        build_id = f"G{index}"
        order = np.random.Generator(np.random.PCG64(insertion_seed)).permutation(
            BASE_COUNT
        ).astype(np.uint32)
        order_path = BUILD_OUT / f"{build_id}__insertion_order.npy"
        save_npy_new(order_path, order)
        candidates.append(
            {
                "build_id": build_id,
                "hnsw_random_seed": build_seed,
                "insertion_order_seed": insertion_seed,
                "insertion_order_rng": "numpy.random.Generator(PCG64)",
                "insertion_order_path": relative_or_absolute(order_path),
                "insertion_order_file_sha256": sha256(order_path),
                "insertion_order_le_u32_sha256": payload_sha_u32(order),
                "artifact_paths": {
                    dataset: f"artifacts/icba_cibs_stage1/{dataset}/{build_id}.bin"
                    for dataset in DATASETS
                },
                "artifact_sha256_at_preregistration": "PENDING_BUILD_REALIZATION_BEFORE_SENTINEL",
                "build_failure_policy": "RECORD_AND_STOP_NO_REPLACEMENT",
            }
        )
    random_build_index = int(
        np.random.Generator(np.random.PCG64(MASTER_SEED + 700)).integers(0, 3)
    )
    return {
        "schema_version": 1,
        "status": "FROZEN_BEFORE_BUILD_AND_STAGE1_OUTCOMES",
        "candidate_count": 3,
        "allowed_variation": ["hnsw_random_seed", "insertion_order"],
        "frozen_equal_fields": {
            "base_count": BASE_COUNT,
            "M": 16,
            "efConstruction": 100,
            "k": 10,
            "metric": "squared_l2",
            "implementation": "hnswlib_v0.8.0_commit_3f3429661187e4c24a490a0f148fc6bc89042b3d",
            "compiler": "GCC_9.4.0",
            "language_standard": "c++17",
            "compiler_flags": [
                "-O3",
                "-DNDEBUG",
                "-DNO_MANUAL_VECTORIZATION",
                "-Wall",
                "-Wextra",
                "-Wpedantic",
            ],
            "build_threads": 1,
            "query_threads": 1,
            "simd": "NO_MANUAL_VECTORIZATION_SCALAR",
        },
        "candidates": candidates,
        "fallback_build_id": "G1",
        "random_single_build_baseline": candidates[random_build_index]["build_id"],
        "no_seed_replacement": True,
        "no_failed_build_discard": True,
        "artifact_hash_required_before_sentinel": True,
    }


def main() -> None:
    if any(path.exists() for path in (OUT, MANIFEST, ROLE_MANIFEST, BUILD_MANIFEST)):
        raise RuntimeError("refusing to overwrite a Phase-I freeze artifact")
    gate = resource_gate()
    roles = freeze_query_roles()
    builds = freeze_builds()
    ROLE_MANIFEST.write_text(json.dumps(roles, indent=2, sort_keys=True) + "\n")
    BUILD_MANIFEST.write_text(json.dumps(builds, indent=2, sort_keys=True) + "\n")
    prereg = {
        "schema_version": 1,
        "protocol": "ICBA_CIBS_FIXED_STAGE_I_REAL_NDC_PILOT",
        "status": "PHASE1_PREREGISTERED_BEFORE_TRUTH_OR_ACTION_OUTCOMES",
        "evidence_level": "EXPLORATORY_FIXED_TARGET_STAGE_I",
        "frozen_base": "b0190169cdb758aa5311c7d13fbfd4fd724020f0",
        "contract_amendment_commit": "31ca05fcc40eb2ec1705f51fb0a66a9e95052f85",
        "quality_target": {"metric": "Recall@10", "operator": ">=", "value": 0.9},
        "risk": {"delta": 0.05, "alpha": 0.05, "family_size": 36, "one_sided": True},
        "raw_fixed_ef_grid": list(RAW_EF_GRID),
        "main": {"K": 3, "L": 12, "M": 36, "sentinel_n": 256, "maximum_execution_failures": 3},
        "ablation": {"authorized_after_main_completion_only": True, "K": 2, "L": 12, "M": 24, "sentinel_n": 128, "maximum_failures_for_certificate": 0},
        "failure_event": "Z_abs=1 iff Recall@10<0.90 or endpoint infeasible or query execution fails",
        "multiplicity": "one-sided exact Clopper-Pearson UCB at alpha/M independently for every action; certify iff UCB<=0.05",
        "main_failure_thresholds": {"n_256_max_certifiable_failures": 3, "n_250_max_certifiable_failures": 3, "fourth_failure_forbids_certification": True},
        "selection": {
            "certified_set": "actions with simultaneous CP UCB<=0.05",
            "primary": "minimum sentinel mean NDC",
            "tie_break": ["lower_sentinel_p95_NDC", "lower_raw_ef", "lower_build_id"],
            "empty_set": "fixed-safe G1 raw ef=100000 fallback after all fallback gates pass",
            "raw_recall_monotonicity_assumed": False,
            "right_censoring_counted_as_success": False,
        },
        "measurements_per_action": [
            "raw_Recall@10",
            "Z_abs",
            "endpoint_status",
            "exact_NDC",
            "actual_expansions",
            "requested_raw_ef",
            "wall_clock_ns",
        ],
        "baselines": {
            "B0": "fixed-safe G1 raw ef=100000 full enumeration",
            "B1": "G1-only fair certification across L=12 using alpha/L; same cost-aware tie-break; B0 if empty",
            "B2": "registered single action G1 raw ef=512",
            "B3": f"one frozen random build {builds['random_single_build_baseline']} raw ef=512",
            "B4": "CIBS-Fixed selected once from all 36 actions",
            "B5": "post-hoc per-query oracle over all 36 actions; nondeployable",
        },
        "evaluation_rule": "freeze selected-action manifest and hash before evaluation truth; evaluation cannot reselect",
        "certificate_semantics": {
            "sentinel": "PROCEDURE_CERTIFICATE",
            "evaluation": "HELD_OUT_RISK_DIAGNOSTIC",
            "report_condition": "CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO",
        },
        "statistics": {
            "paired_query_bootstrap_replicates": 5000,
            "bootstrap_seed": 991,
            "interval": "paired percentile 95%",
            "report": ["Recall@10", "risk_CP", "endpoint", "mean_NDC", "p50_NDC", "p95_NDC", "p99_NDC", "expansions", "raw_ef", "wall_clock", "index_size", "peak_memory"],
            "relative_to": ["B0", "B1"],
            "robustness": ["delete_top_1_percent_largest_per_query_NDC_gains", "build_effects", "leave_one_build_out", "remove_selected_build", "selection_stability"],
        },
        "minimum_gate_both_datasets": {
            "recall_delta_min": -0.001,
            "mean_ndc_gain_relative_B1_min": 0.01,
            "p95_ndc_delta_max": 0,
            "certificate_valid": True,
            "evaluation_no_clear_conflict": True,
            "endpoint_not_worse": True,
            "delete_top_1_percent_gain_positive": True,
            "finite_break_even": True,
        },
        "promotion_gate": [
            "recall_noninferiority_interval_support",
            "mean_gain_CI_lower_bound_gt_0",
            "p95_delta_CI_upper_bound_le_0_or_no_clear_worsening",
            "same_direction_both_datasets",
            "no_contamination_or_replay_failure",
            "complete_cost_break_even_reasonable",
        ],
        "costs": {
            "include": ["per_build_construction", "peak_memory", "index_storage", "truth", "36_action_search", "selection", "certification", "serialization", "storage", "fallback"],
            "truth_channels": ["truth_available", "truth_acquisition_included"],
            "workload_N": [1000, 10000, 100000, 1000000, 10000000],
            "fallback_enters_mean_and_tail": True,
        },
        "required_machine_tests": [
            "frozen_lock_28_of_28",
            "query_role_pairwise_overlap_zero",
            "historical_source_id_overlap_zero",
            "truth_firewall_access_log",
            "build_set_immutability",
            "insertion_order_hash_and_replay",
            "resource_gate_before_every_build",
            "compiler_flags_and_scalar_mode_replay",
            "native_tracer_top10_equivalence",
            "native_tracer_exact_ndc_equivalence",
            "synthetic_fallback_full_enumeration",
            "actual_G1_layer0_directed_connectivity",
            "fallback_native_bruteforce_exact_top10",
            "index_save_load_replay",
            "CP_reference_vectors",
            "Bonferroni_family_size",
            "action_matrix_36_cells_per_query",
            "requested_ef_ndc_expansion_separation",
            "selection_tie_break_replay",
            "evaluation_sealed_until_action_hash",
            "cost_ledger_completeness",
            "artifact_checksum_replay",
            "query_failure_boundary",
            "baseline_action_equivalence",
        ],
        "forbidden": ["validation_dev", "formal_test", "certification_reserved", "future_confirm", "glove", "GPU_method_search", "outcome_driven_tuning", "raw_recall_envelope", "open_world_claim", "confirmatory_claim", "SOTA_claim", "CIBS_Race_claim"],
        "resource_gate": gate,
        "query_role_manifest": relative_or_absolute(ROLE_MANIFEST),
        "query_role_manifest_sha256": sha256(ROLE_MANIFEST),
        "build_manifest": relative_or_absolute(BUILD_MANIFEST),
        "build_manifest_sha256": sha256(BUILD_MANIFEST),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "compiler_version": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
            "GPU_authorized": False,
        },
        "truth_or_action_outcomes_read_during_freeze": False,
    }
    MANIFEST.write_text(json.dumps(prereg, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": prereg["status"],
                "resource_gate": gate,
                "role_sizes": ROLE_SIZES,
                "random_single_build": builds["random_single_build_baseline"],
                "query_manifest_sha256": prereg["query_role_manifest_sha256"],
                "build_manifest_sha256": prereg["build_manifest_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
