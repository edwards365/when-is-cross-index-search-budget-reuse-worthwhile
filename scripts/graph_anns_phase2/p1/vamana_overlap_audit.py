#!/usr/bin/env python
"""P1: Vamana-style query/base overlap audit at the same standard as the clean Faiss-100K
forensics (content_overlap_forensics.csv). Read-only: hashes only, no file is rewritten.

fbin layout: int32 n, int32 dim, then n*dim float32 (row-major).

Outputs (results/graph_anns_phase2_p1/):
  vamana_overlap_forensics.csv   — per-dataset gate row, same column semantics as Faiss
  vamana_base_identity.csv       — per-build base.fbin sha256 vs stage/E4-input base
  vamana_overlap_events.csv      — per-query event counts (raw/normalized hits)
"""
import csv
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

DATA500 = Path("/home/wlk/data500")
STAGES = {
    "sift_100k": DATA500 / "icba_vamana_stage1",
    "arxiv_nomic_100k": DATA500 / "icba_vamana_stage1_arxiv",
}
E4_INPUTS = DATA500 / "graph_anns_e4" / "inputs"
OUT = Path(__file__).resolve().parents[3] / "results" / "graph_anns_phase2_p1"
OUT.mkdir(parents=True, exist_ok=True)


def read_fbin(path):
    with open(path, "rb") as f:
        n, d = struct.unpack("<ii", f.read(8))
        a = np.frombuffer(f.read(n * d * 4), dtype="<f4")
    return a.reshape(n, d)


def row_hashes(a, normalize=False):
    if normalize:
        norms = np.linalg.norm(a, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        a = a / norms
    b = np.ascontiguousarray(a, dtype="<f4").view(np.uint8).reshape(len(a), -1)
    return {hashlib.sha256(row).hexdigest() for row in b}, \
        [hashlib.sha256(row.tobytes()).hexdigest() for row in b]


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


forensics, base_rows, event_rows = [], [], []
for ds, stage in STAGES.items():
    q = read_fbin(stage / "evaluation_queries.fbin")
    base_ref = read_fbin(stage / "data" / "V01" / "base.fbin")
    e4_dir = E4_INPUTS / ds
    e4_base_files = sorted(e4_dir.glob("*.fbin")) + sorted(e4_dir.glob("*base*"))
    # E4 input base: first fbin whose row count matches base_ref
    e4_base = None
    for cand in e4_dir.glob("**/*"):
        if cand.is_file() and cand.suffix in (".fbin", ".bin"):
            try:
                with open(cand, "rb") as f:
                    n, d = struct.unpack("<ii", f.read(8))
                if n == base_ref.shape[0] and d == base_ref.shape[1]:
                    e4_base = cand
                    break
            except Exception:
                continue

    # per-build base identity: byte hash (order-sensitive) + content multiset (order-insensitive)
    def content_fingerprint(arr):
        b = np.ascontiguousarray(arr, dtype="<f4").view(np.uint8).reshape(len(arr), -1)
        hs = sorted(hashlib.sha256(row.tobytes()).hexdigest() for row in b)
        return hashlib.sha256("\n".join(hs).encode()).hexdigest()

    e4_base_path = e4_dir / "base.f32bin"
    e4_base = e4_base_path if e4_base_path.exists() else None
    v01 = read_fbin(stage / "data" / "V01" / "base.fbin")
    v01_fp = content_fingerprint(v01)
    e4_fp = content_fingerprint(read_fbin(e4_base)) if e4_base is not None else None
    for vb in sorted((stage / "data").glob("V*")):
        bf = vb / "base.fbin"
        arr = read_fbin(bf)
        row = {"dataset": ds, "build": vb.name,
               "base_shape": "x".join(map(str, arr.shape)),
               "content_sha256": sha256_file(bf),
               "content_multiset_sha256": content_fingerprint(arr)}
        row["identical_to_V01"] = row["content_sha256"] == sha256_file(stage / "data" / "V01" / "base.fbin")
        row["same_content_multiset_as_V01"] = row["content_multiset_sha256"] == v01_fp
        if e4_base is not None:
            row["e4_input_file"] = e4_base.name
            row["same_content_multiset_as_e4_input"] = row["content_multiset_sha256"] == e4_fp
        else:
            row["e4_input_file"] = "NOT_FOUND"
            row["same_content_multiset_as_e4_input"] = "NOT_ESTIMABLE"
        base_rows.append(row)

    # role IDs (historical roles = non-evaluation roles in frozen registry)
    roles = json.loads((stage / "query_role_ids.json").read_text())
    eval_ids = set(roles.get("vamana_evaluation", []))
    historical_ids = set()
    for k, v in roles.items():
        if k != "vamana_evaluation":
            historical_ids |= set(v)

    q_raw_set, q_raw_list = row_hashes(q)
    q_nrm_set, q_nrm_list = row_hashes(q, normalize=True)
    b_raw_set, _ = row_hashes(base_ref)
    b_nrm_set, _ = row_hashes(base_ref, normalize=True)

    qb_raw = len(q_raw_set & b_raw_set)
    qb_nrm = len(q_nrm_set & b_nrm_set)
    internal_id_dup = len(q) - len(range(len(q)))  # positional IDs: 0 by construction
    internal_raw_dup = len(q_raw_list) - len(q_raw_set)

    # cross-stage leakage: Vamana evaluation queries vs the E4 (hnswlib) registered base
    if e4_base is not None:
        e4_arr = read_fbin(e4_base)
        e4_raw_set, _ = row_hashes(e4_arr)
        e4_nrm_set, _ = row_hashes(e4_arr, normalize=True)
        xs_raw = len(q_raw_set & e4_raw_set)
        xs_nrm = len(q_nrm_set & e4_nrm_set)
    else:
        xs_raw = xs_nrm = -1

    forensics.append({
        "dataset": ds,
        "evaluation_n": len(q),
        "query_base_id_overlap": "POSITIONAL_NA_QUERIES_ARE_ROLE_INDEXED",
        "query_base_raw_overlap": qb_raw,
        "query_base_normalized_overlap": qb_nrm,
        "historical_role_id_overlap": len(eval_ids & historical_ids),
        "historical_role_raw_overlap": "NOT_ESTIMABLE_ROLE_VECTORS_NOT_RETAINED",
        "historical_role_normalized_overlap": "NOT_ESTIMABLE_ROLE_VECTORS_NOT_RETAINED",
        "evaluation_internal_id_duplicates": internal_id_dup,
        "evaluation_internal_raw_duplicates": internal_raw_dup,
        "evaluation_internal_normalized_duplicates": len(q_nrm_list) - len(q_nrm_set),
        "crossstage_query_e4base_raw_overlap": xs_raw,
        "crossstage_query_e4base_normalized_overlap": xs_nrm,
        "gate_a": "PASS" if qb_raw == 0 and qb_nrm == 0 and internal_raw_dup == 0 and xs_raw == 0 and xs_nrm == 0 else "FAIL",
    })
    event_rows.append({"dataset": ds, "event": "query_base_raw_overlap", "count": qb_raw})
    event_rows.append({"dataset": ds, "event": "query_base_normalized_overlap", "count": qb_nrm})

with open(OUT / "vamana_overlap_forensics.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(forensics[0].keys()))
    w.writeheader()
    w.writerows(forensics)
with open(OUT / "vamana_base_identity.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(base_rows[0].keys()))
    w.writeheader()
    w.writerows(base_rows)
with open(OUT / "vamana_overlap_events.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["dataset", "event", "count"])
    w.writeheader()
    w.writerows(event_rows)

for r in forensics:
    print(r)
n_same = sum(1 for r in base_rows if r["same_content_multiset_as_V01"] is True)
n_e4 = sum(1 for r in base_rows if r["same_content_multiset_as_e4_input"] is True)
print(f"base identity: {n_same}/{len(base_rows)} identical to stage V01; "
      f"{n_e4}/{len(base_rows)} identical to E4 input base")
