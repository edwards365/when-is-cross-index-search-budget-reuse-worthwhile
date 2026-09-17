#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parent
files = [root / "sections" / name for name in (
    "05_methodology.tex", "06_portability.tex",
    "07_families.tex", "08_recovery_cost.tex")]
text = "\n".join(path.read_text(encoding="utf-8") for path in files)

for rq in range(1, 10):
    assert f"RQ{rq}:" in text, f"missing RQ{rq}"

for block in text.split("\\subsection{RQ")[1:]:
    heading, body = block.split("}", 1)
    for marker in ("\\textbf{Question.}", "\\textbf{Protocol.}",
                   "\\textbf{Observation.}", "\\textbf{Conclusion.}"):
        assert marker in body, f"RQ{heading} missing {marker}"

assert "Planned setup matrix" not in text
assert "to attach" not in text
assert "final text will" not in text.lower()
assert text.count("\\begin{table}") >= 5
print("W4 RQ structure: PASS; RQ1--RQ9 and question/protocol/observation/conclusion complete.")
