#!/usr/bin/env python3
"""Run the frozen nine-run exact SGDR Gate-O diagnostic matrix."""

from __future__ import annotations
import argparse, gzip, hashlib, json, shutil, subprocess, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, BinaryIO
import yaml

MIN_FREE = 10 * 2**30
def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""): h.update(b)
    return h.hexdigest()
def stream_sha(f: BinaryIO) -> str:
    h=hashlib.sha256()
    for b in iter(lambda:f.read(4*1024*1024),b""): h.update(b)
    return h.hexdigest()
def gzsha(path: Path) -> str:
    with gzip.open(path,"rb") as f:return stream_sha(f)
def disk(path: Path) -> float:
    free=shutil.disk_usage(path).free
    if free<MIN_FREE:raise OSError(f"free disk {free/2**30:.3f} GiB below 10 GiB")
    return free/2**30
def call(cmd:list[str],out:Path,err:Path)->float:
    start=time.perf_counter()
    with out.open("w") as o,err.open("w") as e:p=subprocess.run(cmd,stdout=o,stderr=e)
    if p.returncode:raise subprocess.CalledProcessError(p.returncode,cmd)
    return time.perf_counter()-start
def compress(src:Path,dst:Path)->None:
    with src.open("rb") as a,gzip.open(dst,"wb",compresslevel=6) as b:shutil.copyfileobj(a,b,4*1024*1024)

def one(job:dict[str,Any],protocol:dict[str,Any],train:dict[str,Any],search:dict[str,Any],e0:Path,plans:Path,output:Path,replay:Path,evaluator:Path,stop:threading.Event)->dict[str,Any]:
    run=job["run_id"]; final=output/"runs"/run; marker=final/"COMPLETE.json"
    if marker.is_file():return json.loads(marker.read_text())
    if stop.is_set():raise RuntimeError("stopped before start")
    if final.exists():raise FileExistsError(f"partial output {final}")
    disk(output); work=output/".work"/run
    if work.exists():raise FileExistsError(f"stale work {work}")
    logs=output/"logs";logs.mkdir(parents=True,exist_ok=True)
    index=work/"original";metric="ip" if train["normalized"] else "l2"
    seconds_build=call([str(replay.resolve()),str(Path(train["path"]).resolve()),str(train["points"]),str(train["dimensions"]),str(job["seed"]),"16","100",metric,str((e0/"audits"/f"{run}-original-plan.csv").resolve()),str(index.resolve())],logs/f"{run}.build.stdout.log",logs/f"{run}.build.stderr.log")
    expected=e0/"runs"/run/"original_algorithm4"
    if sha(index/"layer0_edges.csv")!=gzsha(expected/"layer0_edges.csv.gz"):raise ValueError(f"{run}: Original edge mismatch")
    if sha(index/"internal_to_external.csv")!=gzsha(expected/"internal_to_external.csv.gz"):raise ValueError(f"{run}: mapping mismatch")
    if not json.loads((index/"metadata.json").read_text())["upper_checksum_equal"]:raise ValueError(f"{run}: upper mismatch")
    csv_path,meta=work/"diagnostic.csv",work/"metadata.json"
    seconds_eval=call([str(evaluator.resolve()),str((index/"index.bin").resolve()),str(Path(search["queries"]).resolve()),str(Path(search["truth"]).resolve()),metric,",".join(map(str,protocol["ef_search"])),run,str((index/"layer0_edges.csv").resolve()),str((plans/run/"delta_10pct.csv").resolve()),str(csv_path.resolve()),str(meta.resolve())],logs/f"{run}.eval.stdout.log",logs/f"{run}.eval.stderr.log")
    m=json.loads(meta.read_text())
    if not m["native_original_exact"] or m["formal_test_members_accessed"]:raise ValueError(f"{run}: unsafe diagnostic metadata")
    rows=sum(1 for _ in csv_path.open("rb"))-1
    if rows!=11*6*500:raise ValueError(f"{run}: row mismatch {rows}")
    final.mkdir(parents=True);compress(csv_path,final/"diagnostic.csv.gz");shutil.copy2(meta,final/"metadata.json")
    record={"status":"complete","run_id":run,"dataset":job["dataset"],"build_seed":job["seed"],"rows":rows,"build_seconds":seconds_build,"evaluate_seconds":seconds_eval,"original_edges_exact_e0":True,"mapping_exact_e0":True,"native_original_exact":True,"result_sha256":sha(final/"diagnostic.csv.gz"),"temporary_indexes_deleted":False,"new_ef_points":False,"validation_dev_accessed":False,"formal_test_members_accessed":False}
    (index/"index.bin").unlink();record["temporary_indexes_deleted"]=True;marker.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n");shutil.rmtree(work);disk(output);return record

def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--prereg",type=Path,default=Path("manifests/sgdr_3day/preregistration.json"));p.add_argument("--e0",type=Path,default=Path("results/gb_mpcc/e0"));p.add_argument("--plans",type=Path,default=Path("results/sgdr_3day/delta_plans"));p.add_argument("--output",type=Path,default=Path("results/sgdr_3day/gate_o_stage"));p.add_argument("--replay",type=Path,default=Path("build-r0/hnsw_replay_layer0_plan"));p.add_argument("--evaluator",type=Path,default=Path("build-r0/hnsw_sgdr_gate_o_search"));p.add_argument("--workers",type=int,default=3);a=p.parse_args()
    pre=json.loads(a.prereg.read_text());
    if pre["status"]!="FROZEN_BEFORE_SGDR_PERFORMANCE_EXPERIMENTS" or pre["query_split"]["validation_dev_access"]!="FORBIDDEN" or pre["query_split"]["formal_test_access"]!="FORBIDDEN":raise PermissionError("preregistration firewall changed")
    if a.workers!=3:raise ValueError("frozen maximum is three workers")
    train_m=json.loads(Path("results/gb_mpcc/r0_inputs/manifest.json").read_text());search_m=json.loads((a.e0/"search_inputs"/"manifest.json").read_text());train={x["dataset"]:x for x in train_m["inputs"]};search={x["dataset"]:x for x in search_m["datasets"]}
    if train_m["formal_test_members_accessed"] or search_m["formal_test_members_accessed"]:raise PermissionError("input firewall violation")
    a.output.mkdir(parents=True,exist_ok=True);disk(a.output);jobs=[{"dataset":d,"seed":s,"run_id":f"{d}-b{s}"} for d in pre["datasets"] for s in pre["graph_seeds"]];stop=threading.Event();records=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(one,j,pre,train[j["dataset"]],search[j["dataset"]],a.e0,a.plans,a.output,a.replay,a.evaluator,stop):j for j in jobs}
        for future in as_completed(futures):
            try:r=future.result()
            except BaseException:stop.set();[x.cancel() for x in futures];raise
            records.append(r);print(json.dumps({"complete":len(records),"run_id":r["run_id"],"free_gib":disk(a.output)}),flush=True)
    summary={"status":"SGDR_GATE_O_STAGE_MATRIX_COMPLETE","runs":9,"rows":sum(r["rows"] for r in records),"all_original_reconstructions_exact_e0":True,"all_native_original_checks_exact":True,"all_temporary_indexes_deleted":True,"new_ef_points":False,"validation_dev_accessed":False,"formal_test_members_accessed":False,"records":sorted(records,key=lambda x:x["run_id"])}
    (a.output/"matrix_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps({k:v for k,v in summary.items() if k!="records"}))
if __name__=="__main__":main()
