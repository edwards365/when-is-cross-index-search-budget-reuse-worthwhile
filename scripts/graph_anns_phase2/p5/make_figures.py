#!/usr/bin/env python
"""P5: three paper figures from the P2-P4 constructive results."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RES = REPO / "results"
FIG = REPO / "figures" / "graph_anns_phase2"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 9, "figure.dpi": 150})

# ---- Fig 5: k-source ladder
ks = pd.read_csv(RES / "graph_anns_phase2_p2/max_over_k_sources.csv")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=False)
for ax, ds in zip(axes, ["sift_100k", "arxiv_nomic_100k"]):
    for impl, marker in [("hnswlib", "o-"), ("faiss", "s--")]:
        g = ks[(ks.dataset == ds) & (ks.implementation == impl)].sort_values("k_sources")
        ax.plot(g.k_sources, g.mean_risk * 100, marker, ms=4, label=f"{impl} mean")
        ax.plot(g.k_sources, g.risk_p95 * 100, marker, ms=3, alpha=0.45,
                label=f"{impl} p95")
    ax.axhline(2, color="crimson", lw=1, ls=":", label="2% materiality gate")
    ax.axhline(5, color="darkorange", lw=1, ls=":", label="5% risk tolerance")
    ax.set_xlabel("k pooled source builds")
    ax.set_title("SIFT-100K" if ds == "sift_100k" else "Arxiv-Nomic-100K")
    ax.set_yscale("log")
axes[0].set_ylabel("transport risk (%)")
axes[0].legend(fontsize=6.5, loc="upper right")
fig.suptitle("Robust source pooling: risk vs. number of pooled builds", y=1.02, fontsize=10)
fig.tight_layout()
fig.savefig(FIG / "fig_pooling_ladder.png", bbox_inches="tight")
fig.savefig(FIG / "fig_pooling_ladder.pdf", bbox_inches="tight")

# ---- Fig 6: six-method risk-cost plane
rows = []
for ds in ("sift_100k", "arxiv_nomic_100k"):
    t = pd.read_csv(RES / f"graph_anns_phase2_p2/six_method_table_{ds}.csv")
    rows.append({
        "dataset": ds,
        "M1": (t.M1_naive_k1_risk.mean() * 100, t.M1_distcomp.mean()),
        "M2": (t.M2_overall_unsafe_execution.mean() * 100, t.M2_distcomp.mean()),
        "M3": (t.loc[t.M3_certified, "M3_risk_eval"].mean() * 100,
               t.loc[t.M3_certified, "M3_distcomp"].mean()),
        "M5": (t.M5_max_action_risk.mean() * 100, t.M5_distcomp.mean()),
        "M6": (t.M6_oracle_risk.mean() * 100, 1.0),
    })
fig, ax = plt.subplots(figsize=(5.4, 3.4))
colors = {"M1": "tab:red", "M2": "tab:green", "M3": "tab:purple", "M5": "tab:orange", "M6": "tab:blue"}
labels = {"M1": "M1 naive transport", "M2": "M2 max-over-source",
          "M3": "M3 certified max action", "M5": "M5 always-max (uncertified)",
          "M6": "M6 per-query oracle"}
for m in ("M1", "M2", "M3", "M5", "M6"):
    xs, ys = [], []
    for r in rows:
        risk, cost = r[m]
        if risk is not None and cost is not None:
            xs.append(cost)
            ys.append(risk)
    ax.scatter(xs, ys, c=colors[m], label=labels[m], s=42, zorder=3)
    for r in rows:
        risk, cost = r[m]
        if risk is not None and cost is not None:
            ax.annotate("SIFT" if r["dataset"] == "sift_100k" else "Arxiv",
                        (cost, risk), textcoords="offset points", xytext=(5, -2), fontsize=6.5)
ax.axhline(2, color="crimson", lw=1, ls=":", label="2% materiality gate")
ax.axhline(5, color="darkorange", lw=1, ls=":", label="5% risk tolerance")
ax.set_xlabel("DistComp vs. per-query oracle (x)")
ax.set_ylabel("transport risk (%)")
ax.set_yscale("log")
ax.legend(fontsize=6.5, loc="upper left")
ax.set_title("Constructive decision plane (hnswlib, registered grid)", fontsize=10)
fig.tight_layout()
fig.savefig(FIG / "fig_decision_plane.png", bbox_inches="tight")
fig.savefig(FIG / "fig_decision_plane.pdf", bbox_inches="tight")

# ---- Fig 7: contract ablation
ab = pd.read_csv(RES / "graph_anns_phase2_p3/contract_ablation.csv")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
for ax, ds in zip(axes, ["sift_100k", "arxiv_nomic_100k"]):
    g = ab[ab.dataset == ds]
    ax2 = ax.twinx()
    ax.bar(g.regime, g.min_safe_action_variation * 100, color="#4c72b0", alpha=0.85,
           label="min-safe-action variation (%)")
    ax2.plot(g.regime, g.build_time_median_frozen_s, "ro--", ms=4, lw=1,
             label="median build time (s)")
    ax.set_ylim(0, 80)
    ax2.set_ylim(0, None)
    ax.set_title("SIFT-100K" if ds == "sift_100k" else "Arxiv-Nomic-100K")
    ax.set_xlabel("contract tier")
axes[0].set_ylabel("variation (%)")
axes[1].tick_params(axis="y", colors="firebrick")
axes[0].legend(fontsize=6.5, loc="upper right")
axes[1].legend(fontsize=6.5, loc="upper center")
fig.suptitle("Deterministic-contract ablation (descriptive chain)", y=1.02, fontsize=10)
fig.tight_layout()
fig.savefig(FIG / "fig_contract_ablation.png", bbox_inches="tight")
fig.savefig(FIG / "fig_contract_ablation.pdf", bbox_inches="tight")
print("figures written:", sorted(p.name for p in FIG.iterdir()))
