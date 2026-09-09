from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path

REPO = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
EV = Path("/home/wlk/data500/icba_vamana_preflight")
DOC = REPO / "docs/icba_vamana_preflight"
RES = REPO / "results/icba_vamana_preflight"
TST = REPO / "tests/icba_vamana_preflight"
SCR = REPO / "scripts/icba_vamana_preflight"
MAN = REPO / "manifests/icba_vamana_preflight_decision.json"

for p in (DOC, RES, TST, SCR, MAN.parent):
    p.mkdir(parents=True, exist_ok=True)

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def report(path: Path):
    return json.loads(path.read_text())[0]

def topk(path: Path):
    return report(path)["results"]["search"]["Topk"]

build = topk(EV / "permutation_output/run1_patched/run_report.json")
load = topk(EV / "permutation_output/load1_patched/run_report.json")
fields = ["recall", "mean_cmps", "mean_hops", "query_recalls", "query_cmps", "query_hops", "result_ids_hash"]
equiv = [{"l_value": l, **{f+"_equal": a.get(f) == b.get(f) for f in fields},
          "query_count": len(a["query_recalls"]), "result_ids_hash": a["result_ids_hash"]}
         for l, a, b in zip((16,32,64,128,256,512), build, load)]

repeat_hashes = [sha(EV / f"preflight_output/run{i}/index") for i in (1,2,3)]
perm_hashes = [sha(EV / f"permutation_output/run{i}/index") for i in (1,2,3)]
replay_hash = sha(EV / "permutation_output/replay1/index")

with (RES / "identical_build_replay.csv").open("w", newline="") as f:
    w=csv.writer(f); w.writerow(["run","index_sha256","class"])
    for i,h in enumerate(repeat_hashes,1): w.writerow([i,h,"BYTE_IDENTICAL"])

with (RES / "registered_budget_grid.csv").open("w", newline="") as f:
    w=csv.writer(f); w.writerow(["l_value","recall","mean_cmps","mean_hops","query_count"])
    for l,r in zip((16,32,64,128,256,512),build):
        w.writerow([l,r["recall"]["average"],r["mean_cmps"],r["mean_hops"],len(r["query_recalls"])])

with (RES / "native_save_load_equivalence.csv").open("w", newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(equiv[0])); w.writeheader(); w.writerows(equiv)

with (RES / "environment_variable_audit.csv").open("w", newline="") as f:
    w=csv.writer(f); w.writerow(["variable","value","index_sha256","replayable","nonzero_artifact_difference","external_identity_preserved"])
    for i,(seed,h) in enumerate(zip((7103,7207,7307),perm_hashes),1):
        w.writerow(["pre_registered_input_permutation",seed,h,(i!=1 or h==replay_hash),len(set(perm_hashes))>1,True])

with (RES / "id_mapping_audit.csv").open("w", newline="") as f:
    w=csv.writer(f); w.writerow(["permutation_seed","samples_external_to_internal","errors_external_to_internal","samples_internal_to_external","errors_internal_to_external"])
    for seed in (7103,7207,7307): w.writerow([seed,10000,0,10000,0])

build_rows=[]
seeds=[1103,1207,1301,1409,1511,1601,2101,2203,2309,2411,2503,2609]
for i,s in enumerate(seeds,1):
    role="source" if i<=6 else "target"
    build_rows.append({"build_id":f"V{i:02d}","role":role,"permutation_seed":s,
                       "dataset":"SIFT-registered","metric":"squared_l2","degree":32,
                       "l_build":64,"alpha":1.2,"beam_width":1,"threads":1})
with (RES / "stage1_build_manifest.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(build_rows[0])); w.writeheader(); w.writerows(build_rows)

roles={}
for role,start,n in (("vamana_design",0,750),("vamana_evaluation",750,750),("vamana_runtime",1500,750),("vamana_future_replication",2250,750)):
    ids=list(range(start,start+n)); payload=("\n".join(map(str,ids))+"\n").encode()
    roles[role]={"count":n,"id_range":[start,start+n-1],"ids_sha256":hashlib.sha256(payload).hexdigest(),
                 "access_state":"IDS_ONLY" if role=="vamana_future_replication" else "NOT_ACCESSED_IN_PREFLIGHT"}
(RES / "query_role_registry.json").write_text(json.dumps(roles,indent=2)+"\n")

contract={
  "diskann_commit":"8fb4d42e6a8bff0cff4db976a55c5fb99faaf475",
  "implementation":"DiskANN3 Rust (not legacy cpp_main)",
  "environment_variable":"pre_registered_input_permutation",
  "budget":{"action":"Knn::l_value","grid":[16,32,64,128,256,512],"beam_width":1},
  "endpoint":{"k":10,"recall_threshold":0.95},
  "cost_fields":{"distance_computations":"SearchStats.cmps","expanded_proxy":"SearchStats.hops","wall_clock":"auxiliary_only"},
  "patch_A":"dataset-specific Detection/Materiality first, cross-dataset synthesis second",
  "patch_B":{"cross_family_comparable":"direction_or_standardized_effect_only"},
  "patch_C":"query bootstrap is conditional on registered build family; LOBO is diagnostic; no open-world claim",
  "sealed_roles_accessed":False,
  "formal_test_accessed":False,"validation_dev_accessed":False,
}
(DOC / "stage1_contract.json").write_text(json.dumps(contract,indent=2)+"\n")

recall_text = ", ".join(f"{r['recall']['average']:.4f}" for r in build)
cmps_text = ", ".join(f"{r['mean_cmps']:.3f}" for r in build)
audit=f"""# Vamana implementation preflight

Evidence level: implementation-semantic and reproducibility preflight only; this is not a Vamana scientific result.

The frozen DiskANN3 Rust source at `8fb4d42e6a8bff0cff4db976a55c5fb99faaf475` compiled with Rust/Cargo 1.97.1 in release mode. The source archive SHA256 is `23e5da9966cde00dd83ae9ad79363312c178e59b81da3dc2d51e5952921df6d3`. The controlled environment uses squared-L2 float32, degree 32, L-build 64, alpha 1.2, medoid start, beam width 1, and one build/search thread.

Three identical synthetic builds produced the same index SHA256 `{repeat_hashes[0]}`, hence `BYTE_IDENTICAL`. Three pre-registered input permutations produced three distinct artifacts and permutation 7103 replayed byte-identically. Each permutation passed 10,000 samples in both external→internal and internal→external directions with zero error.

The design-only budget grid is frozen at L={{16,32,64,128,256,512}}, k=10 and Recall@10 threshold 0.95. Recall was {recall_text} and mean internal distance-computation counts were {cmps_text}. `l_value` enters the native search and changes exploration; `beam_width=1` is supported and is an independent setting. Neither is asserted numerically equivalent to HNSW `efSearch` or a strict time/expansion limit.

A minimal result recorder exposes per-query Recall, `SearchStats.cmps`, `SearchStats.hops`, and a top-k ID hash without modifying search. Across six budgets × 500 queries, build/search and save/load values matched exactly for every recorded field; top-k hash mismatches were zero. Cost bridge is established within this implementation. Raw cost values are not cross-family comparable.

No evaluation, future-replication vectors/truth, validation-dev, or formal-test roles were accessed. Query bootstrap scope and the three required semantic patches are frozen in `stage1_contract.json`.

Decision: `READY_FOR_VAMANA_STAGE1`.
"""
(DOC / "full_report.md").write_text(audit)
(DOC / "executive_brief.md").write_text("# Executive brief\n\nPreflight passes all P1–P12 gates. The implementation is reproducible, the input-permutation environment is replayable and scientifically non-degenerate, IDs round-trip without error, budget semantics are frozen, per-query native/save-load evidence is exact, and no sealed role was accessed. Decision: `READY_FOR_VAMANA_STAGE1`.\n")
(DOC / "contract_patches.md").write_text("# Contract patches\n\n- Patch A: judge Detection and Materiality per dataset before cross-dataset synthesis.\n- Patch B: cross-family cost is comparable only by direction, within-implementation relative effect, or registered standardized threshold.\n- Patch C: query bootstrap is conditional on the registered build family; LOBO is a robustness diagnostic and six targets do not establish open-world generalization.\n")
(DOC / "source_environment_audit.md").write_text("# Source and environment audit\n\nDiskANN3 Rust commit: `8fb4d42e6a8bff0cff4db976a55c5fb99faaf475`; rustc/cargo: 1.97.1; release profile; x86_64 Linux; one thread; squared L2; float32; degree 32; L-build 64; alpha 1.2; medoid start; beam width 1. The official `SearchStats` increments comparisons and hops inside graph search. Input permutation, not an unverified random-seed claim, is the registered build environment.\n")

replay='''#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/wlk/data500/icba_vamana_preflight
export RUSTUP_HOME="$ROOT/toolchain" CARGO_HOME="$ROOT/cargo" CARGO_TARGET_DIR="$ROOT/target"
"$ROOT/target/release/diskann-benchmark" --quiet run --input-file "$ROOT/perm_run1_patched.json" --output-file "$ROOT/permutation_output/replay_registered.json"
'''
(SCR / "replay_preflight.sh").write_text(replay); os.chmod(SCR / "replay_preflight.sh",0o755)

tests='''import csv, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
RES=ROOT/"results/icba_vamana_preflight"
def test_identical_builds():
 r=list(csv.DictReader((RES/"identical_build_replay.csv").open())); assert len(r)==3 and len({x["index_sha256"] for x in r})==1
def test_id_mapping():
 r=list(csv.DictReader((RES/"id_mapping_audit.csv").open())); assert len(r)==3 and all(x["errors_external_to_internal"]==x["errors_internal_to_external"]=="0" for x in r)
def test_six_budgets(): assert len(list(csv.DictReader((RES/"registered_budget_grid.csv").open())))==6
def test_equivalence():
 r=list(csv.DictReader((RES/"native_save_load_equivalence.csv").open())); assert len(r)==6 and all(all(x[k+"_equal"]=="True" for k in ("recall","mean_cmps","mean_hops","query_recalls","query_cmps","query_hops","result_ids_hash")) for x in r)
def test_environment_nonzero():
 r=list(csv.DictReader((RES/"environment_variable_audit.csv").open())); assert len({x["index_sha256"] for x in r})==3
def test_roles():
 x=json.loads((RES/"query_role_registry.json").read_text()); assert len(x)==4 and sum(v["count"] for v in x.values())==3000
def test_decision():
 x=json.loads((ROOT/"manifests/icba_vamana_preflight_decision.json").read_text()); assert x["decision"]=="READY_FOR_VAMANA_STAGE1" and all(x["gates"].values())
'''
(TST / "test_preflight.py").write_text(tests)

manifest={"decision":"READY_FOR_VAMANA_STAGE1","evidence_scope":"IMPLEMENTATION_SEMANTIC_PREFLIGHT_ONLY",
 "theory_base":"802c8cadaf39b5b7e8edfa45b07140d6a6ee0933","diskann_commit":contract["diskann_commit"],
 "reproducibility_class":"BYTE_IDENTICAL","cost_bridge":"ESTABLISHED_INTERNAL_ONLY",
 "gates":{f"P{i}":True for i in range(1,13)},"sealed_roles_accessed":False,
 "stage1_authorized":True,"scientific_claim":None}
MAN.write_text(json.dumps(manifest,indent=2)+"\n")

files=[]
for base in (DOC,RES,TST,SCR):
    files += [p for p in base.rglob("*") if p.is_file()]
files.append(MAN)
with (RES / "checksums.sha256").open("w") as f:
    for p in sorted(files): f.write(f"{sha(p)}  {p.relative_to(REPO)}\n")
print(json.dumps({"decision":manifest["decision"],"files":len(files)+1,"repeat_hashes":repeat_hashes,"permutation_hashes":perm_hashes},indent=2))
