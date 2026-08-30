#!/usr/bin/env python3
"""Generate the eight required theory structure figures in PNG and PDF."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures" / "icba_oracle_observable"
NAVY = "#16324F"
BLUE = "#2A6F97"
TEAL = "#2A9D8F"
GOLD = "#E9C46A"
RED = "#C44536"
INK = "#17202A"
PALE = "#F5F7FA"


def canvas(title: str, subtitle: str = ""):
    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.text(0.3, 5.65, title, fontsize=18, fontweight="bold", color=NAVY, va="top")
    if subtitle:
        ax.text(0.3, 5.22, subtitle, fontsize=9.5, color="#52616B", va="top")
    return fig, ax


def box(ax, x, y, w, h, text, color=BLUE, face="white", size=10, weight="normal"):
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08",
        linewidth=1.7, edgecolor=color, facecolor=face
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK, fontweight=weight, wrap=True)
    return patch


def arrow(ax, x1, y1, x2, y2, color=INK, text=None, dy=0.12):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", lw=1.6, color=color))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + dy, text, fontsize=8.5, color=color, ha="center")


def save(fig, stem: str):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", dpi=190, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig1():
    fig, ax = canvas("Information hierarchy", "More target information enlarges the admissible rule class; acquisition cost remains explicit.")
    box(ax, 0.7, 2.1, 2.3, 1.45, "$\\mathcal{I}_0$\nsource policy and\ndeployable metadata", NAVY, "#EAF0F6", 10.5, "bold")
    box(ax, 3.85, 1.75, 2.3, 2.15, "$\\mathcal{I}_m$\n$\\mathcal{I}_0$ + purchased\ntarget transcript $Z_m$", BLUE, "#E8F3F8", 11, "bold")
    box(ax, 7.0, 1.4, 2.3, 2.85, "$\\mathcal{I}_\\theta$\ncomplete target\nresponse\n(non-deployable)", TEAL, "#E8F7F4", 11, "bold")
    arrow(ax, 3.05, 2.82, 3.75, 2.82, BLUE, "$\\subseteq$")
    arrow(ax, 6.2, 2.82, 6.9, 2.82, TEAL, "$\\subseteq$")
    ax.text(5, 0.65, "$R_\\theta \\leq R_m \\leq R_0$  when actions and safety semantics are fixed", ha="center", fontsize=11, color=NAVY)
    save(fig, "01_information_hierarchy")


def fig2():
    fig, ax = canvas("Oracle headroom decomposition", "Opportunity is not recoverability.")
    x, y, w, h = 0.9, 2.35, 8.2, 1.25
    ax.add_patch(Rectangle((x, y), w * 0.43, h, facecolor=TEAL, edgecolor="white"))
    ax.add_patch(Rectangle((x + w * 0.43, y), w * 0.57, h, facecolor=GOLD, edgecolor="white"))
    ax.text(x + w * 0.215, y + h / 2, "$H_{obs}(m)=R_0-R_m$\nobservable value", ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(x + w * 0.715, y + h / 2, "$G_{id}(m)=R_m-R_\\theta$\nidentification gap", ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(5, 4.35, "$H_{oracle}=R_0-R_\\theta=H_{obs}(m)+G_{id}(m)$", ha="center", fontsize=16, color=NAVY, fontweight="bold")
    ax.text(0.9, 1.55, "$R_0$", fontsize=11, color=NAVY, ha="center")
    ax.text(4.43, 1.55, "$R_m$", fontsize=11, color=NAVY, ha="center")
    ax.text(9.1, 1.55, "$R_\\theta$", fontsize=11, color=NAVY, ha="center")
    ax.text(5, 0.75, "T-OO2: the gold segment can equal the entire bar even when oracle headroom is positive.", ha="center", fontsize=10, color=RED)
    save(fig, "02_oracle_headroom_decomposition")


def fig3():
    fig, ax = canvas("Negative-positive theorem dependency", "Only two grouped results are selected as paper mains.")
    box(ax, 0.45, 3.65, 2.0, 0.85, "Information model", NAVY, "#EAF0F6", 10, "bold")
    box(ax, 3.0, 4.0, 2.0, 0.85, "T-OO2\nfinite obstruction", RED, "#FAECEA", 9.5, "bold")
    box(ax, 5.55, 4.0, 2.0, 0.85, "T-OO3\nLe Cam lower bound", RED, "#FAECEA", 9.5, "bold")
    box(ax, 8.05, 4.0, 1.55, 0.85, "T-OO8\ninfo rate", GOLD, "#FFF7DD", 9.5, "bold")
    box(ax, 3.0, 2.05, 2.0, 0.85, "T-OO5\nmargin recovery", TEAL, "#E8F7F4", 9.5, "bold")
    box(ax, 5.55, 2.05, 2.0, 0.85, "T-OO6\ncertification", TEAL, "#E8F7F4", 9.5, "bold")
    box(ax, 8.05, 2.05, 1.55, 0.85, "RACS\nP1-P3", BLUE, "#E8F3F8", 9.5, "bold")
    arrow(ax, 2.5, 4.1, 2.95, 4.35)
    arrow(ax, 5.05, 4.42, 5.5, 4.42)
    arrow(ax, 7.6, 4.42, 8.0, 4.42)
    arrow(ax, 2.5, 3.9, 2.95, 2.48)
    arrow(ax, 5.05, 2.48, 5.5, 2.48)
    arrow(ax, 7.6, 2.48, 8.0, 2.48)
    ax.plot([7.3, 7.3], [3.0, 3.82], color=GOLD, lw=2, ls="--")
    ax.text(7.35, 3.38, "partial bridge\nknown binary channel", fontsize=8, color="#8A6700", va="center")
    ax.text(5, 0.75, "Main I: T-OO3 + T-OO8 consequence     |     Main II: T-OO5 + T-OO6 + RACS", ha="center", fontsize=10.5, color=NAVY, fontweight="bold")
    save(fig, "03_theorem_dependency")


def fig4():
    fig, ax = canvas("Three safety semantics", "These are distinct contracts, not a containment chain.")
    box(ax, 0.45, 2.0, 2.65, 2.15, "FIXED TARGET\n$\\rho_\\theta(a)\\leq\\delta$\n\nOne named build\nquery uncertainty", BLUE, "#E8F3F8", 11, "bold")
    box(ax, 3.68, 2.0, 2.65, 2.15, "META AVERAGE\n$\\mathbb{E}_{\\theta\\sim\\Pi}\\rho_\\theta(a)\\leq\\delta$\n\nRequires explicit $\\Pi$", GOLD, "#FFF7DD", 11, "bold")
    box(ax, 6.9, 2.0, 2.65, 2.15, "OPEN WORLD\n$\\sup_{\\theta\\in\\Theta_{new}}\\rho_\\theta(a)\\leq\\delta$\n\nUniform declared class", RED, "#FAECEA", 11, "bold")
    ax.text(3.38, 3.08, "$\\nRightarrow$", fontsize=20, color=RED, ha="center")
    ax.text(6.62, 3.08, "$\\nRightarrow$", fontsize=20, color=RED, ha="center")
    ax.text(5, 1.12, "C5: average safe can be pointwise unsafe     |     C6: current-target certification can fail on unseen support", ha="center", fontsize=9.5, color=RED)
    ax.text(5, 0.55, "Query resampling never creates independent build evidence.", ha="center", fontsize=10.5, color=NAVY, fontweight="bold")
    save(fig, "04_safety_semantics")


def fig5():
    fig, ax = canvas("Recovery conditions and evidence complexity", "Margins govern the upper bound; information separation governs the lower bound.")
    box(ax, 0.45, 3.7, 2.1, 0.9, "Information\n$I^*>0$", GOLD, "#FFF7DD", 10.5, "bold")
    box(ax, 0.45, 1.9, 2.1, 0.9, "Label complexity\n$m \\gtrsim \\log(1/\\beta)/I^*$", NAVY, "#EAF0F6", 9.5, "bold")
    arrow(ax, 1.5, 3.65, 1.5, 2.85, GOLD)
    box(ax, 3.45, 3.7, 2.1, 0.9, "Risk slack\n$\\delta-\\rho(a^*)\\geq2\\epsilon_R$", TEAL, "#E8F7F4", 9.5, "bold")
    box(ax, 6.45, 3.7, 2.1, 0.9, "Cost margin\n$\\Gamma_C>2\\epsilon_C$", TEAL, "#E8F7F4", 10, "bold")
    box(ax, 3.45, 1.9, 2.1, 0.9, "Safe screen\nno false-safe action", BLUE, "#E8F3F8", 9.5, "bold")
    box(ax, 6.45, 1.9, 2.1, 0.9, "Exact action\nor $2\\epsilon_C$ near-oracle", BLUE, "#E8F3F8", 9.5, "bold")
    arrow(ax, 4.5, 3.65, 4.5, 2.85, TEAL)
    arrow(ax, 7.5, 3.65, 7.5, 2.85, TEAL)
    ax.text(5, 0.75, "No empirical Graph-ANNS claim is made until all three inputs are measured with deployable data.", ha="center", fontsize=10, color=RED)
    save(fig, "05_margin_information_complexity")


def fig6():
    fig, ax = canvas("RACS decision flow", "Risk-Aware Certified Selection - theoretical method template")
    box(ax, 0.35, 3.55, 1.85, 0.85, "Selection split\nrisk + cost estimates", NAVY, "#EAF0F6", 8.8, "bold")
    box(ax, 2.75, 3.55, 1.85, 0.85, "UCB screening\nretain safe set", TEAL, "#E8F7F4", 8.8, "bold")
    box(ax, 5.15, 3.55, 1.85, 0.85, "Minimum total cost\ncandidate", BLUE, "#E8F3F8", 8.8, "bold")
    box(ax, 7.55, 3.55, 1.85, 0.85, "Independent cert\nchosen action only", GOLD, "#FFF7DD", 8.8, "bold")
    arrow(ax, 2.22, 3.98, 2.72, 3.98)
    arrow(ax, 4.62, 3.98, 5.12, 3.98)
    arrow(ax, 7.02, 3.98, 7.52, 3.98)
    box(ax, 7.55, 1.65, 1.85, 0.75, "ACCEPT\ndeploy candidate", TEAL, "#E8F7F4", 9.2, "bold")
    box(ax, 3.55, 1.65, 1.65, 0.75, "REJECT / EMPTY\nsafe fallback", RED, "#FAECEA", 9.5, "bold")
    arrow(ax, 8.48, 3.5, 8.48, 2.45, TEAL, "UCB <= delta", 0.06)
    arrow(ax, 7.52, 3.7, 5.25, 2.45, RED, "otherwise", 0.04)
    arrow(ax, 3.7, 3.5, 4.35, 2.45, RED, "empty set", -0.08)
    ax.text(5, 0.72, "P1 fixed-target safety  |  P2 conditional near-oracle cost  |  P3 symbolic break-even", ha="center", fontsize=10.5, color=NAVY, fontweight="bold")
    save(fig, "06_racs_flow")


def fig7():
    fig, ax = canvas("Classical theory crosswalk", "The contribution is the safe ordered-budget combination, not renamed classical tools.")
    rows = [
        ("Blackwell / value of information", "T-OO1", "identity / direct consequence"),
        ("Le Cam / Brown-Low", "T-OO2, T-OO3", "testing reduction"),
        ("Fano / Assouad", "T-OO4", "appendix qualification"),
        ("Uniform convergence", "T-OO5", "margin-based safe screen"),
        ("Clopper-Pearson / reject option", "T-OO6", "split certificate + fallback"),
        ("Cost-sensitive classification", "T-OO7", "decision metric"),
        ("Active testing / SPRT", "T-OO8", "restricted rate bridge"),
    ]
    x0, y0 = 0.55, 4.65
    widths = (4.0, 1.7, 3.15)
    headers = ("Classical source", "Project result", "Honest disposition")
    for j, (head, width) in enumerate(zip(headers, widths)):
        x = x0 + sum(widths[:j])
        ax.add_patch(Rectangle((x, y0), width, 0.48, facecolor=NAVY, edgecolor="white"))
        ax.text(x + width / 2, y0 + 0.24, head, color="white", fontsize=9.5, fontweight="bold", ha="center", va="center")
    for i, row in enumerate(rows):
        y = y0 - (i + 1) * 0.52
        face = "#F3F6F8" if i % 2 == 0 else "white"
        for j, (val, width) in enumerate(zip(row, widths)):
            x = x0 + sum(widths[:j])
            ax.add_patch(Rectangle((x, y), width, 0.5, facecolor=face, edgecolor="#D7DEE3", linewidth=0.7))
            ax.text(x + 0.09, y + 0.25, val, color=INK, fontsize=8.7, ha="left", va="center")
    ax.text(5, 0.42, "Novelty label ceiling: NEW_COMBINATION_OF_CLASSICAL_RESULTS", ha="center", fontsize=10.5, color=RED, fontweight="bold")
    save(fig, "07_classical_crosswalk")


def fig8():
    fig, ax = canvas("From Graph-ANNS to finite-budget decisions", "A formal abstraction ladder; not a cross-domain empirical claim.")
    levels = [
        (0.85, 1.05, 8.3, 0.72, "Generic hidden-environment finite ordered-budget decision", NAVY, "#EAF0F6"),
        (1.45, 2.0, 7.1, 0.72, "Safe recovery: under-budget risk + compute tax + evidence + fallback", BLUE, "#E8F3F8"),
        (2.05, 2.95, 5.9, 0.72, "Graph-ANNS rebuild action: reuse / recalibrate / retrain / fallback", TEAL, "#E8F7F4"),
        (2.65, 3.9, 4.7, 0.72, "Per-query ordered search budget and recall target", GOLD, "#FFF7DD"),
    ]
    for x, y, w, h, text, edge, face in levels:
        box(ax, x, y, w, h, text, edge, face, 10, "bold")
    arrow(ax, 5, 4.85, 5, 4.67, NAVY)
    ax.text(5, 4.92, "concrete", ha="center", fontsize=8.5, color="#52616B")
    arrow(ax, 5, 1.02, 5, 0.7, NAVY)
    ax.text(5, 0.35, "broader formal class: early exit, LLM compute, algorithm configuration - requires separate instantiation", ha="center", fontsize=9.3, color=RED)
    save(fig, "08_graph_ann_abstraction")


def main():
    for fn in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8):
        fn()
    print("generated 8 PNG and 8 PDF figures")


if __name__ == "__main__":
    main()
