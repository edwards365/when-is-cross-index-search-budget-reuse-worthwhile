#!/usr/bin/env python3
import hashlib
import json
import struct
import csv
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
MAIN = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
RAW = MAIN / "data/raw/sift-128-euclidean.hdf5"
ROLES = json.loads((ROOT / "manifests/icba_stable_build_pilot_query_roles.json").read_text())
QUERIES = ROOT / "results/hardness_portability_100k/query_inputs/sift_100k_queries.npy"
TRUTH = ROOT / "results/hardness_portability_100k/query_inputs/sift_100k_truth.npy"
OUT = ROOT / "build_inputs/icba_stable_build_pilot/sift_100k"


def write_matrix(path: Path, values: np.ndarray) -> None:
    values = np.ascontiguousarray(values, dtype="<f4")
    with path.open("wb") as handle:
        handle.write(struct.pack("<QQ", *values.shape))
        handle.write(values.tobytes())


def write_truth(path: Path, values: np.ndarray) -> None:
    values = np.ascontiguousarray(values, dtype="<u4")
    with path.open("wb") as handle:
        handle.write(struct.pack("<QQ", *values.shape))
        handle.write(values.tobytes())


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


OUT.mkdir(parents=True, exist_ok=True)
with h5py.File(RAW, "r") as handle:
    points = np.asarray(handle["train"][:100000], dtype="<f4")
write_matrix(OUT / "points.f32bin", points)
with (OUT / "order.u32bin").open("wb") as handle:
    handle.write(struct.pack("<Q", 100000))
    handle.write(np.arange(100000, dtype="<u4").tobytes())

queries = np.load(QUERIES, mmap_mode="r")
truth = np.load(TRUTH, mmap_mode="r")
for role in ("design", "bridge_calibration"):
    ids = np.asarray(ROLES["roles"][role], dtype=np.int64)
    write_matrix(OUT / f"{role}_queries.f32bin", queries[ids])
    write_truth(OUT / f"{role}_truth.u32bin", truth[ids, :10])
    write_matrix(OUT / f"{role}_smoke100_queries.f32bin", queries[ids[:100]])
    write_truth(OUT / f"{role}_smoke100_truth.u32bin", truth[ids[:100], :10])

files = sorted(path for path in OUT.iterdir() if path.is_file())
manifest = {
    "schema_version": 1,
    "status": "PREPARED_FROM_FROZEN_INPUTS",
    "raw_hdf5": str(RAW),
    "raw_hdf5_sha256": digest(RAW),
    "points": 100000,
    "dimensions": 128,
    "insertion_order": "natural_external_label_0_to_99999",
    "roles_accessed": ["design", "bridge_calibration"],
    "roles_sealed": ["certification_reserved", "evaluation_reserved"],
    "artifacts": {path.name: {"bytes": path.stat().st_size, "sha256": digest(path)} for path in files},
    "created_utc": datetime.now(timezone.utc).isoformat(),
}
(OUT / "input_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
access_log = ROOT / "results/icba_stable_build_pilot/query_roles/truth_access_log.csv"
with access_log.open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(("role", "truth_access_permitted", "truth_accessed", "purpose"))
    writer.writerow(("design", 1, 1, "repair design traces and first-safe checkpoints"))
    writer.writerow(("bridge_calibration", 1, 1, "dual-endpoint empirical bridge calibration"))
    writer.writerow(("certification_reserved", 0, 0, "sealed until authorized certification"))
    writer.writerow(("evaluation_reserved", 0, 0, "sealed until authorized evaluation"))
print(json.dumps({"status": "PASS", "bytes": sum(path.stat().st_size for path in files)}))
