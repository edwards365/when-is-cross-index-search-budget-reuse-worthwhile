#!/usr/bin/env python
"""P11: horizontal TCP (Tiered Conformal Pooling) showcase figure — one wide panel."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

REPO = Path(__file__).resolve().parents[3]
FIG = REPO / "results/graph_anns_phase2_p11"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 9})
fig, ax = plt.subplots(figsize=(16.5, 5.4))
ax.set_xlim(0, 33); ax.set_ylim(0, 10.8); ax.axis("off")

INK = "#263238"
BLUE = "#1565c0"; GREEN = "#2e7d32"; ORANGE = "#ef6c00"; PURPLE = "#6a1b9a"; GRAY = "#78909c"

def box(x, y, w, h, title, lines, ec, fc="white", fs=8.0, tfs=9.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.10",
                                fc=fc, ec=ec, lw=1.6))
    ax.text(x + w/2, y + h - 0.32, title, ha="center", va="top",
            fontsize=tfs, fontweight="bold", color=ec)
    ax.text(x + w/2, y + h - 0.86, "\n".join(lines), ha="center", va="top",
            fontsize=fs, color=INK, linespacing=1.35)

def arrow(x1, y1, x2, y2, color=GRAY, lw=2.0, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 color=color, lw=lw, linestyle=ls,
                                 mutation_scale=16))

# ================= stage 1: offline label cache =================
box(0.3, 5.4, 7.4, 4.6, "OFFLINE  ·  source-label cache  (once per replica)",
    ["k historical rebuilds of the same data",
     "(hnswlib / Faiss; k = 9–23 certified, 49 in farm)",
     "",
     "each replica searched once per query:",
     "B_s(q) = min efSearch reaching Recall@10 = h10",
     "",
     "cost: 0.13 s per replica per 500 queries",
     "→ cached per-query table {q → B_1(q)…B_k(q)}"],
    ec=BLUE)

# ================= stage 2: online tier A (repeat query) =================
box(8.6, 5.4, 7.9, 4.6, "ONLINE tier A  ·  repeat query  →  cache hit",
    ["a(q) = ⌈(1−α)(k+1)⌉-th smallest of {B_s(q)}",
     "(α = 0.05, k = 23 → deploy the 23rd of 24)",
     "",
     "Theorem 3:  Pr[ B_t(q) > a(q) ]  ≤  α",
     "finite-sample · per-query · no deployment truth",
     "· no query-distribution assumption",
     "",
     "measured: 0.96% / 1.35% ≤ 5%  (hnswlib ×2 datasets)",
     "0.05% (clean Faiss)   ·   DistComp 1.32–1.44× oracle"],
    ec=GREEN, fc="#f1f8e9")

# ================= stage 3: online tier B (cold query) =================
box(17.4, 5.4, 7.4, 4.6, "ONLINE tier B  ·  cold query  →  fallback",
    ["cache miss (unseen query)",
     "",
     "deploy maximum registered action",
     "(or abstain)",
     "",
     "measured risk: 0.8–1.3%  (< δ = 5%)",
     "latency 276 µs p95",
     "cold online pooling infeasible: 1.73 s/query"],
    ec=ORANGE, fc="#fff8e1")

# ================= stage 4: composite guarantee =================
box(25.7, 5.4, 7.0, 4.6, "COMPOSITE  ·  tiered risk bound",
    ["r_tiered ≤ ρ·α + (1−ρ)·r_max",
     "",
     "ρ = workload repeat rate (measured, not assumed)",
     "",
     "ρ:      0      0.25    0.5     0.75    1.0",
     "risk: 1.03%  0.80%  0.58%  0.35%  0.13%",
     "(Arxiv; SIFT: 0.80% → 0.18%)",
     "meets δ = 5% at every measured ρ"],
    ec=PURPLE, fc="#f3e5f5")

for x1, x2 in ((7.7, 8.6), (16.5, 17.4), (24.8, 25.7)):
    arrow(x1, 7.7, x2, 7.7, color=GRAY)

# query arrival
arrow(0.3, 8.0, 0.05, 8.0, color=GRAY, style="<|-")
ax.text(0.15, 8.9, "query q", fontsize=8, color=GRAY, style="italic")

# ================= bottom strip: validation matrix + boundaries =================
ax.add_patch(FancyBboxPatch((0.3, 0.4), 32.4, 4.3, boxstyle="round,pad=0.10",
                            fc="#eceff1", ec="#546e7a", lw=1.4))
ax.text(16.5, 4.42, "VALIDITY MATRIX  —  every non-vacuous (α, k) holds  ·  boundaries measured, not hidden",
        ha="center", fontsize=10, fontweight="bold", color="#37474f")

cells = [
    ("100K hnswlib\n0.96 / 1.35% ≤ 5%\nk=23 · 1.44/1.32×", GREEN),
    ("100K Faiss (clean)\n0.05% ≤ 5%\nk=23 · abstain 0.5–1.8%", GREEN),
    ("1M  (k=7 → α≥12.5%)\n0.92% ≤ 12.5%", GREEN),
    ("10M  (k=7 → α≥12.5%)\n0.64% ≤ 12.5%\nabstain 36% (endpoint mass)", GREEN),
    ("200-build farm\nk=49: 0.72% ≤ 5%\nk=9:  2.48% ≤ 10%", GREEN),
    ("vacuous (α=.05, k=10)\n→ 100% abstain\nfeasibility is operational", ORANGE),
    ("corr-weighted selection\n3.8–4.4% > α  ✗\nexchangeability is load-bearing", "#c62828"),
]
w = 4.35
for i, (txt, col) in enumerate(cells):
    x = 0.75 + i * (w + 0.22)
    ax.add_patch(FancyBboxPatch((x, 0.65), w, 2.85, boxstyle="round,pad=0.06",
                                fc="white", ec=col, lw=1.4))
    ax.text(x + w/2, 2.02, txt, ha="center", va="center", fontsize=7.6,
            color=INK, linespacing=1.5)

ax.text(16.5, 0.16,
        "TCP is a budget-decision layer over any exposed-knob Graph-ANNS — not a retrieval algorithm; "
        "pool resolution α ≥ 1/(k+1); single-pipeline exchangeability tested on farm (KS 0.11); 10M uncached pooling degrades to 23.3% → contract tier",
        ha="center", fontsize=7.8, color="#546e7a", style="italic")

fig.tight_layout()
fig.savefig(FIG / "tcp_method_figure.png", dpi=170, bbox_inches="tight")
fig.savefig(FIG / "tcp_method_figure.pdf", bbox_inches="tight")
print("saved:", [p.name for p in FIG.glob("tcp_method*")])
