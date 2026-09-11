"""P5 checks. Run:
LD_LIBRARY_PATH=/home/wlk/miniconda3/lib .venv/bin/python tests/graph_anns_phase2_p5/test_p5.py
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
checks = []
def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")

fig = REPO / "figures" / "graph_anns_phase2"
for f in ("fig_pooling_ladder", "fig_decision_plane", "fig_contract_ablation"):
    check(f"{f}_png_pdf", (fig / f"{f}.png").exists() and (fig / f"{f}.pdf").exists())

patch = (REPO / "docs/graph_anns_phase2_p5/paper_revision_patch.md").read_text()
for token in ("R1.", "R2.", "R3.", "R4.", "R5.", "R6.", "R7.", "R8.", "R9.", "R10.", "R11.", "R12.",
              "DistComp", "multi-replica", "plausible deployment shortcut", "1.34", "4.73"):
    check(f"patch_contains_{token[:16]}", token in patch)

review = (REPO / "docs/graph_anns_phase2_p5/final_iclr_review.md").read_text()
check("review_has_score", "8/10" in review or "8th point" in review)
check("review_has_next_loop", "P6-A" in review and "P6-B" in review and "P6-C" in review)

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
