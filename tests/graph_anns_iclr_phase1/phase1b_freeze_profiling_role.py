#!/usr/bin/env python3
"""Freeze a cost-only query role without dereferencing any sealed future vectors."""
from __future__ import annotations

import csv
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

import h5py
import numpy as np

REPO = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
SCRATCH = Path("/home/wlk/data500/graph_anns_iclr_phase1_scratch")
FAISS_ROLES = Path("/home/wlk/data500/graph_anns_faiss_external_validity/run/roles")
VAMANA_ROOTS = {
    "sift_100k": Path("/home/wlk/data500/icba_vamana_stage1"),
    "arxiv_nomic_100k": Path("/home/wlk/data500/icba_vamana_stage1_arxiv"),
}
H5 = {
    "sift_100k": REPO / "data/raw/sift-128-euclidean.hdf5",
    "arxiv_nomic_100k": REPO / "data/raw/arxiv-nomic-768-normalized.hdf5",
}
PARENT = "d2ad714541d73bedcd48580347b67880d37580f8"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def identity_hash(dataset_sha: str, source_id: int) -> str:
    return sha_bytes(f"{dataset_sha}:train:{source_id}".encode())


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_json(spec: str) -> dict:
    raw = subprocess.check_output(["git", "show", spec], cwd=REPO, text=True)
    return json.loads(raw)


def all_historical_ids(dataset: str) -> tuple[set[int], dict[str, set[int]]]:
    by_role: dict[str, set[int]] = {}
    with (FAISS_ROLES / dataset / "role_ids.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            by_role.setdefault(f"faiss:{row['role']}", set()).add(int(row["source_id"]))
    e4 = git_json(f"{PARENT}:manifests/graph_anns_e4_role_manifest.json")["roles"][dataset]
    for role, values in e4.items():
        if isinstance(values, list):
            by_role[f"e4:{role}"] = set(map(int, values))
    vr = json.loads((VAMANA_ROOTS[dataset] / "query_role_ids.json").read_text())
    for role, values in vr.items():
        by_role[f"vamana:{role}"] = set(map(int, values))
    forbidden_roles = {
        name: ids for name, ids in by_role.items()
        if "runtime" not in name
    }
    return set().union(*forbidden_roles.values()), by_role


def write_f32bin(path: Path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(struct.pack("<QQ", *values.shape))
        np.asarray(values, dtype="<f4").tofile(handle)


def main() -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    out_rows = []
    summary = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        forbidden, by_role = all_historical_ids(dataset)
        vamana = json.loads((VAMANA_ROOTS[dataset] / "query_role_ids.json").read_text())
        original_runtime = list(map(int, vamana["vamana_runtime"]))
        selected = [source_id for source_id in original_runtime if source_id not in forbidden]
        excluded = [source_id for source_id in original_runtime if source_id in forbidden]

        # Fill only from unassigned train rows. Candidate IDs are chosen before vector access.
        with h5py.File(H5[dataset], "r") as handle:
            dataset_sha = sha_bytes(
                f"{H5[dataset].resolve()}:{handle['train'].shape}:{handle['train'].dtype}".encode()
            )
            used = set().union(*by_role.values())
            for source_id in range(handle["train"].shape[0] - 1, -1, -1):
                if len(selected) >= 750:
                    break
                if source_id not in used:
                    selected.append(source_id)
                    used.add(source_id)
            if len(selected) != 750:
                raise RuntimeError(f"unable to freeze 750 profiling rows for {dataset}")
            ordered = np.asarray(selected, dtype=np.int64)
            sort_order = np.argsort(ordered)
            sorted_vectors = np.asarray(handle["train"][ordered[sort_order]], dtype="<f4")
            inverse = np.empty_like(sort_order)
            inverse[sort_order] = np.arange(len(sort_order))
            vectors = sorted_vectors[inverse]

        vector_hashes = [sha_bytes(row.tobytes()) for row in vectors]
        if len(vector_hashes) != len(set(vector_hashes)):
            raise RuntimeError(f"duplicate content inside profiling role for {dataset}")
        data_path = SCRATCH / "profiling_roles" / f"{dataset}.f32bin"
        write_f32bin(data_path, vectors)
        for pos, (source_id, vector_sha) in enumerate(zip(selected, vector_hashes)):
            out_rows.append({
                "dataset": dataset,
                "role": "profiling_cost_only",
                "position": pos,
                "source_id": source_id,
                "frozen_source_identity_sha256": identity_hash(dataset_sha, source_id),
                "vector_sha256": vector_sha,
            })
        overlaps = {
            role: len(set(selected).intersection(ids))
            for role, ids in sorted(by_role.items())
            if "runtime" not in role
        }
        if any(overlaps.values()):
            raise RuntimeError(f"role overlap remains for {dataset}: {overlaps}")
        summary.append({
            "dataset": dataset,
            "count": 750,
            "original_runtime_retained": 750 - len(excluded),
            "excluded_cross_role_ids": excluded,
            "replacement_count": len(excluded),
            "source_identity_overlap_counts": overlaps,
            "source_identity_overlap_all_zero": True,
            "profiling_vector_file": str(data_path),
            "profiling_vector_file_sha256": file_sha(data_path),
            "future_vector_content_dereferenced": False,
            "proof_scope": "frozen dataset identity plus train source row; sealed future vectors were not opened",
        })

    result_dir = REPO / "results/graph_anns_iclr_phase1"
    result_dir.mkdir(parents=True, exist_ok=True)
    csv_path = result_dir / "profiling_cost_only_role.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)
    manifest = {
        "role": "profiling_cost_only",
        "purpose": "runtime and resource measurement only",
        "science_use_prohibited": True,
        "selection_or_threshold_use_prohibited": True,
        "sealed_future_vectors_or_truth_accessed": False,
        "datasets": summary,
        "role_csv_sha256": file_sha(csv_path),
    }
    (result_dir / "profiling_cost_only_role_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
