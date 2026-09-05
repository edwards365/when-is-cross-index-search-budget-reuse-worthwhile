from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
DOC = ROOT / "docs/icba_fixed_target_auditor"
OUT = ROOT / "results/icba_fixed_target_auditor"
FIG = ROOT / "figures/icba_fixed_target_auditor"
MAN = ROOT / "manifests"
ART = ROOT / "artifacts/icba_fixed_target_auditor/source_policies"
for p in (DOC, OUT, FIG): p.mkdir(parents=True, exist_ok=True)

decision = json.loads((MAN / "icba_fixed_target_auditor_retrospective_gate.json").read_text())
recovery = json.loads((MAN / "icba_fixed_target_auditor_data_recovery.json").read_text())
ev = pd.read_csv(OUT / "evaluation_results.csv")
dec = pd.read_csv(OUT / "crossfit_decisions.csv")
ep = pd.read_csv(OUT / "endpoint_build_summary.csv")
pol = pd.read_csv(OUT / "source_policy_registry.csv")
base = pd.read_csv(OUT / "baseline_comparison.csv")
cluster = pd.read_csv(OUT / "build_cluster_bootstrap.csv")

disk = subprocess.check_output(["df", "-B1", "/"], text=True).splitlines()[-1].split()
mem = subprocess.check_output(["free", "-b"], text=True).splitlines()[1].split()
with (OUT / "resource_inventory.csv").open("w", newline="") as f:
    w=csv.writer(f); w.writerow(["resource","total_bytes","available_bytes","status"]); w.writerow(["root_filesystem",disk[1],disk[3],"PASS_GT_5_GIB"]); w.writerow(["memory",mem[1],mem[6],"AVAILABLE"])
proc = subprocess.check_output(["ps","-u","wlk","-o","pid=,pcpu=,pmem=,etime=,args="], text=True).splitlines()
with (OUT / "process_inventory.csv").open("w", newline="") as f:
    w=csv.writer(f); w.writerow(["snapshot_line"]); w.writerows([[x.strip()] for x in proc])

fallback = pd.read_csv(OUT / "certification_results.csv")
fallback = fallback[fallback.certificate_role == "fallback"].copy()
fallback[["dataset","source_seed","target_seed","fold","raw_ef","failures","n","cp_upper","passed","alpha_share"]].to_csv(OUT / "fallback_results.csv", index=False)

(DOC / "server_audit.md").write_text(f"# Server audit\n\nThe audit ran in the unique main worktree on `{subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()}`. Root free space remained above 5 GiB, memory was sufficient, and no competing ANN experiment was present. Historical untracked directories were preserved. No unknown files, indices, logs, or user data were deleted.\n")
(DOC / "final_report.md").write_text("# Final report\n\nThe original 81 Gate-A runs were recovered with 243/243 checksum matches. Their common action grid is six levels rather than twelve. Six source policies were serialized from historical source development and all selected ef=120. Five-fold retrospective cross-fit across 12 directed pairs produced 36 safe acceptances and 24 safe-but-rejected abstentions, with zero unsafe acceptance. However, every accepted deployment used ef=200, exactly matching Always Fallback cost, while search-only decision regret versus the fixed-pair safe Oracle was significantly positive for both datasets. Gate R3 therefore failed and no prospective access was authorized. Final decision: `ICBA_DECISION_REGRET_NOT_IMPROVED`.\n")
(DOC / "executive_brief.md").write_text("# Executive brief\n\nThis round recovered substantially more evidence than the CALS four-level subset and proved that the corrected auditor can make nontrivial safe decisions retrospectively. It did not recover economic action value: certification drives every accepted decision to ef=200, while 40% of decisions abstain despite a safe retrospective action. The method is runtime-valid and safety-conservative, but the fixed-target route is not closed.\n")

# Fifteen factual figures; no prospective outcomes are displayed.
def save(name, draw):
    fig, ax = plt.subplots(figsize=(7,4.2)); draw(ax); fig.tight_layout(); fig.savefig(FIG/f"{name}.png",dpi=150); fig.savefig(FIG/f"{name}.pdf"); plt.close(fig)

save("01_data_recovery", lambda ax: (ax.bar(["declared main runs","checksums"],[81,243],color=["#4C78A8","#59A14F"]), ax.set_title("Recovered Gate-A artifacts")))
save("02_query_roles", lambda ax: (ax.bar(["selection","pseudo-cert","evaluation"],[600,200,200],color="#4C78A8"), ax.set_title("Per-fold retrospective roles (overlap=0)")))
save("03_endpoint_states", lambda ax: (ax.barh(ep.build,ep.safe_endpoint_queries,color="#59A14F",label="safe endpoint"), ax.barh(ep.build,ep.right_censored_queries,left=ep.safe_endpoint_queries,color="#E15759",label="right-censored"), ax.legend(), ax.set_title("Endpoint states by build")))
save("04_source_policy", lambda ax: (ax.bar(pol.source_build,pol.raw_ef,color="#4C78A8"), ax.tick_params(axis="x",rotation=55), ax.set_title("Serialized source policy ef")))
counts=dec.deployed_action.value_counts()
save("05_selected_actions", lambda ax: (ax.bar(counts.index,counts.values,color="#F28E2B"), ax.set_title("Retrospective deployed actions")))
save("06_unsafe_acceptance", lambda ax: (ax.bar(["unsafe","safe accepted"],[int(ev.unsafe_acceptance.sum()),int((ev.outcome=="SAFE_ACCEPTANCE").sum())],color=["#E15759","#59A14F"]), ax.set_title("Evaluation safety outcomes")))
save("07_correct_abstention", lambda ax: (ax.bar(["correct abstention","safe-but-rejected"],[int((ev.outcome=="CORRECT_ABSTENTION").sum()),int((ev.outcome=="SAFE_BUT_REJECTED").sum())],color=["#59A14F","#EDC948"]), ax.set_title("Abstention attribution")))
save("08_safe_but_rejected", lambda ax: (ax.bar(ev.groupby("dataset").apply(lambda x:(x.outcome=="SAFE_BUT_REJECTED").sum()).index,ev.groupby("dataset").apply(lambda x:(x.outcome=="SAFE_BUT_REJECTED").sum()).values,color="#EDC948"), ax.set_title("Safe-but-rejected folds")))
save("09_decision_regret", lambda ax: (ax.bar(cluster.dataset,cluster.estimate,yerr=[cluster.estimate-cluster.ci_low,cluster.ci_high-cluster.estimate],capsize=4,color="#E15759"), ax.axhline(0,color="black",lw=1), ax.set_title("Build-cluster search regret (95% bootstrap CI)")))
acc=ev[ev.action!="A6"].groupby("dataset")[["mean_ndc","p95_ndc","p99_ndc"]].mean()
save("10_mean_p95_p99", lambda ax: (acc.plot.bar(ax=ax),ax.set_title("Accepted-action NDC tails"),ax.tick_params(axis="x",rotation=0)))
safe_base=base[base.baseline.isin(["B0_ALWAYS_DIRECT_REUSE","B4_ALWAYS_FALLBACK_CANDIDATE"])].groupby(["dataset","baseline"])[["risk","mean_ndc"]].mean().reset_index()
save("11_cost_safety_pareto", lambda ax: (ax.scatter(safe_base.risk,safe_base.mean_ndc,c=np.arange(len(safe_base)),s=70),[ax.annotate(r.baseline.replace("_ALWAYS_"," "),(r.risk,r.mean_ndc),fontsize=7) for r in safe_base.itertuples()],ax.set_xlabel("risk"),ax.set_ylabel("mean NDC"),ax.set_title("Cost–safety diagnostic")))
save("12_service_total_cost", lambda ax: (ax.text(.5,.5,"SYMBOLIC_BREAK_EVEN_ONLY\ncomplete offline cost unavailable",ha="center",va="center",fontsize=14),ax.axis("off"),ax.set_title("Service volume and total cost")))
bsummary=base.groupby(["dataset","baseline"]).agg(unsafe=("status",lambda x:(x=="UNSAFE").sum()),mean_ndc=("mean_ndc","mean")).reset_index()
save("13_baseline_comparison", lambda ax: (bsummary.pivot(index="baseline",columns="dataset",values="mean_ndc").plot.bar(ax=ax),ax.set_title("Baseline mean NDC"),ax.tick_params(axis="x",rotation=60)))
save("14_build_robustness", lambda ax: (ax.bar(cluster.dataset,cluster.ci_low,color="#E15759"),ax.axhline(0,color="black"),ax.set_title("Lower CI remains positive: regret not improved")))
statuses=[1,1,1,0,0,0]; labels=["raw recall","NDC","latency","truth acquisition cost","complete cost","prospective cert"]
save("15_estimability", lambda ax: (ax.imshow([statuses],cmap="RdYlGn",vmin=0,vmax=1,aspect="auto"),ax.set_xticks(range(len(labels)),labels,rotation=50,ha="right"),ax.set_yticks([]),ax.set_title("Estimability matrix")))

final = {
 "completed": True, "decision": "ICBA_DECISION_REGRET_NOT_IMPROVED", "branch": "exp/icba_fixed_target_auditor_closure",
 "data_recovery": recovery["decision"], "main_runs":81, "checksums":"243/243", "common_grid":[10,20,40,80,120,200],
 "source_policies":6, "source_policy_ef":120, "evidence":"RETROSPECTIVE_CROSSFIT", "directed_pairs":12, "fold_decisions":60,
 "accepted":36, "abstained":24, "abstain_fraction":0.4, "unsafe_acceptance":0, "safe_but_rejected":24,
 "arxiv_query_regret_mean":684.4933333333333, "sift_query_regret_mean":470.33722222222224,
 "complete_cost":"NOT_ESTIMABLE", "break_even":"SYMBOLIC_BREAK_EVEN_ONLY", "R1":True,"R2":True,"R3":False,"R4":True,"R5":False,"R6":True,
 "future_confirm_status":"NO_FUTURE_CONFIRM_QUERY_POOL_FOR_THIS_METHOD", "future_confirm_accessed":False,"validation_dev_accessed":False,"formal_test_accessed":False,
 "route_a_closure":False,"scope":"FIXED_TARGET_RETROSPECTIVE_ONLY_NO_OPEN_WORLD_CLAIM",
 "legacy":"LEGACY_BASELINE_CONDITIONALLY_REPRODUCED: 111/123 matched, 8 mismatched, 4 untracked __pycache__ entries"
}
(MAN/"icba_fixed_target_auditor_decision.json").write_text(json.dumps(final,indent=2)+"\n")

targets=[]
for base_dir in (DOC,OUT,FIG,ROOT/"scripts/icba_fixed_target_auditor",ROOT/"tests/icba_fixed_target_auditor",ART):
    if base_dir.exists(): targets += [p for p in base_dir.rglob("*") if p.is_file() and p.name!="checksums.sha256"]
targets += [p for p in MAN.glob("icba_fixed_target_auditor_*.json") if p.is_file()]
with (OUT/"checksums.sha256").open("w") as f:
    for p in sorted(set(targets)): f.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}\n")
print(json.dumps(final,sort_keys=True))
