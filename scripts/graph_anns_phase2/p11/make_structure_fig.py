#!/usr/bin/env python
"""P11: research-structure diagram + gap-closure roadmap figure (8-point path)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

REPO = Path(__file__).resolve().parents[3]
FIG = REPO / "results/graph_anns_phase2_p11"
FIG.mkdir(parents=True, exist_ok=True)

C = {"done": "#2e7d32", "run": "#ef6c00", "todo": "#1565c0", "box": "#eceff1",
     "edge": "#607d8b", "thm": "#6a1b9a", "exp": "#1565c0", "meth": "#2e7d32"}


def box(ax, x, y, w, h, title, lines, color="#37474f", fc="#eceff1", badge=None, fs=7.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                fc=fc, ec=color, lw=1.4))
    ax.text(x + w / 2, y + h - 0.16, title, ha="center", va="top",
            fontsize=fs + 1.2, fontweight="bold", color=color)
    body = "\n".join(lines)
    ax.text(x + w / 2, y + h - 0.55, body, ha="center", va="top", fontsize=fs - 0.4,
            color="#263238")
    if badge:
        bc = {"DONE": C["done"], "RUN": C["run"], "NEW": C["todo"]}[badge[0]]
        ax.add_patch(FancyBboxPatch((x + w - 1.05, y + h - 0.02), 1.0, 0.3,
                                    boxstyle="round,pad=0.01", fc=bc, ec="none"))
        ax.text(x + w - 0.55, y + h + 0.13, badge[1], ha="center", va="center",
                fontsize=6.4, color="white", fontweight="bold")


def arrow(ax, x1, y1, x2, y2, color=C["edge"], style="-|>", lw=1.3, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, color=color,
                                 lw=lw, linestyle=ls, mutation_scale=11))


# ================= panel 1: current research architecture =================
fig, ax = plt.subplots(figsize=(13.4, 8.6))
ax.set_xlim(0, 17.6); ax.set_ylim(0, 11.6); ax.axis("off")
ax.text(8.8, 11.35, "Research architecture — what exists, how it connects, evidence status",
        ha="center", fontsize=12, fontweight="bold")

# Theory layer
box(ax, 0.3, 8.6, 5.2, 2.3, "THEORY  (classical tools, new reduction)",
    ["Thm 1  transcript-limited lower bound", "    premise: probe-class evidence TV<=0.25 hits /",
     "    0.44 runtime; conflict 45-57%", "Thm 2  fixed-target recovery (5 conditions)",
     "    audit: cert POWER binds, not margin"],
    color=C["thm"], badge=("DONE", "SEALED"))
box(ax, 6.1, 8.6, 5.2, 2.3, "THEORY  (new, optional)",
    ["Cross-build risk control:", "  builds as sampling units;", "  P(risk of new build > gate) bound",
     "  from 24-build empirical dist.", "  upgrades 'registered-conditional' claim"],
    color=C["todo"], badge=("NEW", "P11"))

# ICBA / method layer
box(ax, 11.9, 8.6, 5.3, 2.3, "METHOD  ICBA audit + decision rule",
    ["four outcomes: unsafe/conservative/", "fallback/abstain; cost-ordered rule:",
     "contract > pooling > certify > abstain", "canonical-order default tier",
     "inputs/outputs frozen, roles disjoint"],
    color=C["meth"], badge=("DONE", "SEALED"))

# Evidence layer
box(ax, 0.3, 5.4, 5.2, 2.6, "EVIDENCE  scale ladder (real data)",
    ["100K hnswlib+Faiss x2 datasets:", "  risk 17.17-23.60%, V_fin 76-91%",
     "1M preregistered: 21.87% [21.5,22.2]", "10M deep-image (running): 8+2 builds",
     "h=8/9/10 incremental sens: min 5.96%"], color=C["exp"],
    badge=("RUN", "10M LIVE"))
box(ax, 6.1, 5.4, 5.2, 2.6, "EVIDENCE  layer boundaries (measured)",
    ["layer1 response: non-portable (4 cells+1M)", "layer2 policy: pooling <1% @1.34-1.45x;",
     "  1M: k=7 leaves 10.4% (scale-bound)", "layer3 predictor: fails (R2=0.015)",
     "Thm1 premise: TV<=0.25 / runtime 0.44"], color=C["exp"], badge=("DONE", "SEALED"))
box(ax, 11.9, 5.4, 5.3, 2.6, "EVIDENCE  falsification ladder",
    ["16 routes pruned at first failed precondition", "reuse: fixed-target safety only",
     "selection: no joint-feasible action (72)", "portals: mechanism w/o trigger/economics",
     "auditor: safe w/o decision value"], color=C["exp"], badge=("DONE", "SEALED"))

# Mitigation layer
box(ax, 0.3, 2.6, 5.2, 2.3, "MITIGATION  deterministic contract",
    ["risk 0 at 1.71-3.52x build (100K reg.)", "1M: 252s median single-thread (measured)",
     "ablation: order pinning free, halves var;", "single-thread carries byte-identity",
     "8-thread 1M ratio: NOT measured (honest)"], color=C["meth"], badge=("DONE", "SEALED"))
box(ax, 6.1, 2.6, 5.2, 2.3, "MITIGATION  pooled replay (M2)",
    ["risk 0.18/0.09% @1.34-1.45x oracle", "q0.9 = max (no cheaper order stat.)",
     "source req. grows with scale (k=7->10.4%@1M)", "REPLAY+label cache: coverage=repeat rate",
     "COLD-QUERY behavior: unmeasured -> P11"], color=C["meth"],
    badge=("NEW", "P11"))
box(ax, 11.9, 2.6, 5.3, 2.3, "ECONOMICS  ledgers",
    ["profile+certify: 0.12-0.99s INCL TRUTH;", "certifies max only (P=0.47-0.63)",
     "break-even: SIFT NO_FINITE / Arxiv 11.8k q", "p95/p99 + coverage sweep: MISSING",
     "-> P11 latency/SLO ledger"], color=C["meth"], badge=("NEW", "P11"))

# Bottom: hygiene spine
box(ax, 0.3, 0.3, 16.9, 1.7, "HYGIENE SPINE  (applies to every box above)",
    ["preregistered manifests before build/search  |  query/base overlap forensics  |  role disjointness  |  "
     "byte-identity replay  |  NOT_ESTIMABLE never imputed  |  claim registry: permitted/prohibited  |  "
     "incremental-Eq20 caliber crosswalk  |  15-value h/gamma/q-quantile audit CSVs  |  tests 16/24/27/16/7/22/17/12"],
    fc="#e8f5e9", color=C["done"], fs=7.0)

for x in (2.9, 8.7, 14.5):
    arrow(ax, x, 5.35, x, 4.95)
arrow(ax, 5.5, 8.6, 5.5, 8.05, color=C["thm"])
arrow(ax, 14.5, 5.35, 14.5, 4.95)
ax.text(8.8, 0.05, "solid = sealed frozen evidence   |   orange = running (10M)   |   blue = P11 gap-closure items",
        ha="center", fontsize=7.5, color="#455a64")
fig.tight_layout()
fig.savefig(FIG / "research_structure.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# ================= panel 2: roadmap to 8 =================
fig, ax = plt.subplots(figsize=(13.4, 10.4))
ax.set_xlim(0, 17.6); ax.set_ylim(0, 13.1); ax.axis("off")
ax.text(8.8, 12.85, "Roadmap to 8/10 — pure-code first, decisive experiment second, writing third",
        ha="center", fontsize=12, fontweight="bold")

lanes = [
    (8.0, "LANE A  pure code, frozen data (hours each)", "#1565c0", [
        ("A1 probe-feature exhaustion matrix", "curve-shape/queue/latency/x-ef features; 24 builds x 276 pairs; DONE-claim upgrades either way"),
        ("A2 conditional distinguishability", "per-query (q|T) joint test + F-stat; upgrades Thm-1 premise from marginal to conditional"),
        ("A3 M2 coverage-rho sweep", "repeat-rate 0..1 x fallback max/abstain: effective risk/cost/coverage mix (kills 'not serviceable' attack)"),
        ("A4 build-level risk bound", "exchangeable-build population bound for P(new-build risk>gate); upgrades generality claim"),
        ("A5 unsupervised no-truth budget rule", "queue-saturation ef choice: does 'profile w/o truth' have hidden risk? (closes the biggest loophole)"),
        ("A6 latency p95/p99 + re-derivation", "SLO-loss ledger (R1-Q1); 3 origin-unlocated aggregates recomputed or dropped"),
    ]),
    (4.9, "LANE B  decisive online experiment (cheap compute, 100K)", "#2e7d32", [
        ("B1 online M2 service prototype", "rebuild 22-24 source indexes (~10 min); serve COLD SIFT-1M queries: search sources -> pooled action -> measured risk/cost/QPS + coverage"),
        ("B2 head-to-head acceptance line", "same cert level: online-M2 vs profile-and-certify vs always-max vs contract on identical workload; win condition pre-stated"),
        ("B3 weighted pooling", "correlation-weights vs max: does k drop 22->8-10 below 2%?"),
    ]),
    (1.5, "LANE C  writing + scale (after A/B)", "#6a1b9a", [
        ("C1 v5: narrative convergence", "one spine: 'rebuild = hidden shift; measured boundary; cost-ordered rule'; exec table front; hedging consolidated"),
        ("C2 10M section", "from P10 run (in flight): ladder 0.1M->1M->10M closes the scale attack"),
        ("C3 optional: cross-build risk theorem", "only if A4 empirical bound is tight; else stay descriptive"),
    ]),
]
for y0, title, color, items in lanes:
    ax.add_patch(FancyBboxPatch((0.3, y0 - 0.35), 17.0, len(items) * 0.62 + 0.75,
                                boxstyle="round,pad=0.02", fc="#fafafa", ec=color, lw=1.3))
    ax.text(0.55, y0 + len(items) * 0.62 + 0.18, title, fontsize=9.6, fontweight="bold", color=color)
    for i, (t, d) in enumerate(items):
        y = y0 + (len(items) - 1 - i) * 0.62 + 0.12
        ax.add_patch(FancyBboxPatch((0.6, y), 1.35, 0.42, boxstyle="round,pad=0.01",
                                    fc="white", ec=color, lw=1.1))
        ax.text(1.275, y + 0.21, t.split()[0], ha="center", va="center", fontsize=7.4,
                color=color, fontweight="bold")
        ax.text(2.1, y + 0.21, t.split(None, 1)[1] + "  —  " + d, fontsize=7.3,
                va="center", color="#263238")

for x in (8.8,):
    arrow(ax, x, 8.62, x, 8.15, color="#455a64", lw=1.6)
arrow(ax, 8.8, 4.42, 8.8, 4.02, color="#455a64", lw=1.6)
ax.text(16.5, 11.9, "gate: every number traces to\nfrozen artifacts + tests", fontsize=7.2,
        ha="center", color="#37474f", style="italic")
ax.text(16.5, 6.6, "gate: pre-stated win condition;\nidentical workload+cert level", fontsize=7.2,
        ha="center", color="#37474f", style="italic")
ax.text(8.8, 1.9, "expected: A-lane + B1/B2 + C1/C2 -> reviewer-calibrated 7.5-8; if B2 loses to profile-and-certify,\n"
                  "the paper pivots to the strong NEGATIVE route (validated boundary + economics) and still stands",
        ha="center", fontsize=8.2, color="#b71c1c", fontweight="bold")
fig.tight_layout()
fig.savefig(FIG / "roadmap_to_8.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("figures:", [p.name for p in FIG.glob('*.png')])
