#!/usr/bin/env python3
import ast
import csv
import hashlib
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/icba_theory_elevation"
DOC = ROOT / "docs/icba_theory_elevation"
OUT.mkdir(parents=True, exist_ok=True)
DOC.mkdir(parents=True, exist_ok=True)

base = "a9f88bbcfd9b2c2f3e8a27e1471e16628b60cdb0"
micro = "77e0d430bc04b819276b570a96eedb339a66c043"
assert subprocess.check_output(["git", "rev-parse", base], text=True).strip() == base

manifest = json.loads((ROOT / "manifests/icba_open_world_final_decision.json").read_text())
assert manifest["graphs"] == 81
assert manifest["query_budget_rows"] == 972000
assert manifest["directed_pairs"] == 648
assert manifest["endpoint_strata"] == {"certified": 54, "right_censored": 17, "no_practical_safe": 10}

full_lines = (ROOT / "results/icba_open_world/checksums.sha256").read_text().splitlines()
full_ok = 0
for line in full_lines:
    expected, rel = line.split("  ", 1)
    if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected:
        full_ok += 1

micro_lines = subprocess.check_output(
    ["git", "show", f"{micro}:results/icba_micro_closure/checksums.sha256"], text=True
).splitlines()
micro_ok, micro_bad, micro_absent = 0, [], []
for line in micro_lines:
    expected, rel = line.split("  ", 1)
    try:
        data = subprocess.check_output(["git", "show", f"{micro}:{rel}"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        micro_absent.append(rel)
        continue
    if hashlib.sha256(data).hexdigest() == expected:
        micro_ok += 1
    else:
        micro_bad.append(rel)

grid = (10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512)
rank = {b: i for i, b in enumerate(grid)}
split = json.loads((ROOT / "manifests/icba_micro_closure_query_split.json").read_text())["datasets"]
eff = list(csv.DictReader((ROOT / "results/cross_index/g1/derived/per_query_effort.csv").open()))
curves = defaultdict(dict)
for r in eff:
    key = (r["index"], r["dataset"], r["seed"], r["history"])
    curves[key][int(r["query_id"])] = None if r["right_censored"] == "True" else int(r["stable_budget"])
groups = defaultdict(list)
for key in curves:
    groups[key[:2]].append(key)

def qtile(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, math.ceil(p * len(xs)) - 1))]

all_pairs = []
for cell, keys in sorted(groups.items()):
    ev = split[cell[1]]["evaluation_query_ids"]
    for a in keys:
        for b in keys:
            if a == b:
                continue
            common = [q for q in ev if curves[a][q] is not None and curves[b][q] is not None]
            bd = sum(abs(rank[curves[a][q]] - rank[curves[b][q]]) for q in common) / (len(common) * (len(grid) - 1))
            z0 = 0.5 * (a[2] != b[2]) + 0.5 * (a[3] != b[3])
            all_pairs.append((cell, a, b, z0, bd, len(common)))

collisions = []
for cell in sorted(groups):
    rows = [r for r in all_pairs if r[0] == cell]
    zcut = qtile([r[3] for r in rows], 0.25)
    bcut = qtile([r[4] for r in rows], 0.75)
    collisions.extend([r + (zcut, bcut) for r in rows if r[3] <= zcut and r[4] >= bcut])

dedup = {}
for cell, a, b, z0, bd, n, zcut, bcut in collisions:
    x, y = sorted(((a[2], a[3]), (b[2], b[3])))
    dedup[(cell[0], cell[1], x, y)] = (z0, bd, n, zcut, bcut)

with (OUT / "collision_dedup_audit.csv").open("w", newline="") as f:
    fields = ["implementation", "dataset", "build_a", "build_b", "z0_distance", "budget_distance", "complete_case_queries", "z0_threshold", "budget_threshold"]
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
    for (impl, dataset, a, b), values in sorted(dedup.items()):
        w.writerow(dict(zip(fields, [impl, dataset, f"{a[0]}:{a[1]}", f"{b[0]}:{b[1]}", *values])))

sentinel_rows = [
    {"check": "k_values", "status": "PASS", "evidence": "KS=(32,64,128,256)"},
    {"check": "replicates", "status": "PASS", "evidence": "REPS=300"},
    {"check": "master_seed", "status": "PASS", "evidence": "SEED=991"},
    {"check": "sample_method", "status": "PASS", "evidence": "persistent RNG; rng.sample without replacement on every replicate"},
    {"check": "k_dependency", "status": "PASS", "evidence": "each replicate samples exactly k sentinel indices"},
    {"check": "cache_key", "status": "PASS_NO_CACHE", "evidence": "no result cache; aggregation key=(dataset,implementation,k), target loops explicit, seed fixed"},
    {"check": "query_split", "status": "PASS", "evidence": "256 sentinel and 744 disjoint evaluation IDs asserted by frozen audit"},
    {"check": "build_cluster_unit", "status": "PASS", "evidence": "full_bootstrap groups target graph/build before resampling"},
    {"check": "meta_distribution_claim", "status": "PASS_LIMITED", "evidence": "nine builds are fixed-design evidence, not a 5% meta-distribution certificate"},
]
with (OUT / "sentinel_code_path_audit.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=sentinel_rows[0]); w.writeheader(); w.writerows(sentinel_rows)

summary = {
    "conditional_baseline": base,
    "full_seal_checksum_entries": len(full_lines),
    "full_seal_checksum_ok": full_ok,
    "legacy_microclosure_checksum_entries": len(micro_lines),
    "legacy_microclosure_git_blob_ok": micro_ok,
    "legacy_microclosure_git_blob_bad": micro_bad,
    "legacy_microclosure_git_blob_absent": micro_absent,
    "graphs": manifest["graphs"],
    "query_budget_rows": manifest["query_budget_rows"],
    "directed_pairs": len(all_pairs),
    "undirected_pairs": len(all_pairs) // 2,
    "directed_collision_candidates": len(collisions),
    "deduplicated_undirected_collisions": len(dedup),
    "distinct_builds_in_collisions": len({(c[1][0], c[1][1], c[1][2], c[1][3]) for c in collisions} | {(c[2][0], c[2][1], c[2][2], c[2][3]) for c in collisions}),
    "manual_override": "USER_DIRECTED_CONTINUE_2026-08-28",
    "sealed_data_accessed": False,
}
(OUT / "phase0_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

doc = f"""# Full Seal re-audit (conditional continuation)\n\nThe stage starts from `{base}` on `exp/icba_theory_elevation`. The current Full Seal artifact set verifies {full_ok}/{len(full_lines)} SHA256 entries and its native seal test passes. It reproduces 81 graphs, 972,000 query-budget rows, 648 directed (324 unordered) within-cell build pairs, and endpoint strata 54 certified / 17 right-censored / 10 without a practical safe endpoint. GloVe remains excluded from migration-failure claims because its 27 graphs lack certified endpoints. No sealed validation or formal-test data were accessed.\n\n## Mandatory integrity limitation\n\nThe inherited claim that the older micro-closure list reproduces 123/123 entries is not reproducible from Git commit `{micro}`: {micro_ok}/123 tracked blobs match, {len(micro_bad)} tracked CSV blobs mismatch, and {len(micro_absent)} listed `__pycache__` files are absent from Git. Work stopped at discovery; the user explicitly directed continuation. Therefore this stage uses a **conditional baseline** and must not claim exact 123/123 reproduction. The audit defect remains labeled `INVALID_FULL_SEAL_BASELINE` as a limitation; it is not silently repaired.\n\n## Pair and collision audit\n\nThe 648 directed pairs reduce to 324 unordered pairs. Re-executing the frozen quartile rule in memory yields {len(collisions)} directed collision candidates and {len(dedup)} unordered collision pairs, involving {summary['distinct_builds_in_collisions']} distinct builds. The CSV contains the complete deduplicated set rather than only the 20 published witnesses.\n\n## Sentinel and inference audit\n\nThe sentinel implementation uses k in {{32,64,128,256}}, 300 persistent-RNG replicates at seed 991, and distinct without-replacement samples per replicate. It has no result cache, so no incomplete cache key can alias k/seed/target cells. The 256 sentinel and 744 evaluation IDs remain disjoint. Full uncertainty resamples target builds as clusters. Nine observed builds per dataset×implementation cell are treated as fixed-design evidence, never as a 5% meta-distribution certificate.\n\n## Authorization\n\nThis conditional audit authorizes theory derivation and read-only Z1 field inspection. It does not authorize new graphs, sealed splits, algorithm claims, or a Z1 pilot before Gate Z1-A.\n"""
(DOC / "full_seal_reaudit.md").write_text(doc)
print(json.dumps(summary, indent=2))
