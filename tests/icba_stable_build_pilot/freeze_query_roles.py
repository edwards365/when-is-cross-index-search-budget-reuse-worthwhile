#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
QUERY_PATH = ROOT / "results/hardness_portability_100k/query_inputs/sift_100k_queries.npy"
OUT = ROOT / "results/icba_stable_build_pilot/query_roles"
MANIFEST = ROOT / "manifests/icba_stable_build_pilot_query_roles.json"
SEED = 991
ROLES = (
    "design",
    "bridge_calibration",
    "certification_reserved",
    "evaluation_reserved",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


queries = np.load(QUERY_PATH, mmap_mode="r")
if queries.shape[0] != 1000:
    raise SystemExit(f"expected 1000 frozen queries, got {queries.shape}")

permutation = np.random.Generator(np.random.PCG64(SEED)).permutation(1000)
splits = {
    role: sorted(int(value) for value in permutation[index * 250 : (index + 1) * 250])
    for index, role in enumerate(ROLES)
}
sets = {role: set(ids) for role, ids in splits.items()}
if set().union(*sets.values()) != set(range(1000)):
    raise SystemExit("role split does not cover exactly IDs 0..999")
if any(sets[a] & sets[b] for i, a in enumerate(ROLES) for b in ROLES[i + 1 :]):
    raise SystemExit("role overlap detected")

OUT.mkdir(parents=True, exist_ok=True)
ids_path = OUT / "query_role_ids.csv"
with ids_path.open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(("role", "query_id"))
    for role in ROLES:
        writer.writerows((role, query_id) for query_id in splits[role])

overlap_path = OUT / "query_role_overlap.csv"
with overlap_path.open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(("left_role", "right_role", "overlap_count"))
    for left in ROLES:
        for right in ROLES:
            writer.writerow((left, right, len(sets[left] & sets[right])))

access_path = OUT / "truth_access_log.csv"
with access_path.open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(("role", "truth_access_permitted", "truth_accessed_at_freeze", "purpose"))
    writer.writerow(("design", 1, 0, "repair design traces"))
    writer.writerow(("bridge_calibration", 1, 0, "dual-endpoint empirical bridge calibration"))
    writer.writerow(("certification_reserved", 0, 0, "sealed until authorized certification"))
    writer.writerow(("evaluation_reserved", 0, 0, "sealed until authorized evaluation"))

manifest = {
    "schema_version": 1,
    "protocol": "ICBA_STABLE_BUILD_DUAL_ENDPOINT_PILOT",
    "status": "FROZEN_BEFORE_STABLE_RESULTS",
    "seed": SEED,
    "rng": "numpy.random.Generator(PCG64)",
    "query_source": str(QUERY_PATH.relative_to(ROOT)),
    "query_source_sha256": sha256(QUERY_PATH),
    "query_shape": list(queries.shape),
    "roles": splits,
    "role_sizes": {role: len(ids) for role, ids in splits.items()},
    "permutation_sha256": hashlib.sha256(permutation.astype("<u8").tobytes()).hexdigest(),
    "non_diagonal_overlap": 0,
    "truth_firewall": {
        "permitted_now": ["design", "bridge_calibration"],
        "sealed": ["certification_reserved", "evaluation_reserved"],
    },
    "artifacts": {
        "query_role_ids": str(ids_path.relative_to(ROOT)),
        "query_role_overlap": str(overlap_path.relative_to(ROOT)),
        "truth_access_log": str(access_path.relative_to(ROOT)),
    },
}
MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "PASS", "sizes": manifest["role_sizes"], "overlap": 0}))
