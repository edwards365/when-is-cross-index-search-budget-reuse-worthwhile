#!/usr/bin/env python
"""P0 audit: check that every entry in the paper's reference list has at least one
in-text citation anchor in the extracted DOCX text. Output:
results/graph_anns_phase2_p0/reference_anchor_audit.csv"""
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p0"
text = (OUT / "paper_extracted_text.txt").read_text()

# Reference list block starts after the line 'References'
body, _, reflist = text.partition("\nReferences\n")
# Body ends before appendix? Anchors may also appear in appendices; use full text
# minus the reference block itself for anchor search.
anchor_text = body

REFS = [
    ("Angelopoulos et al. 2025 (LTT)", "Angelopoulos"),
    ("Angelopoulos et al. 2024 (CRC)", ["Angelopoulos", "conformal risk control"]),
    ("Bae et al. 2026 (QBAT)", "Bae"),
    ("Bates et al. 2021 (RCPS)", "Bates"),
    ("Ben-David et al. 2010", "Ben-David"),
    ("Chatzakis et al. 2025 (DARTH)", "Chatzakis"),
    ("Duchi et al. 2025", "Duchi"),
    ("Elliott & Clark 2024", ["Elliott", "Clark"]),
    ("El-Yaniv & Wiener 2010", "El-Yaniv"),
    ("Fu et al. 2019 (NSG)", "Fu"),
    ("Garivier & Kaufmann 2016", ["Garivier", "Kaufmann"]),
    ("Horchidan et al. 2025 (ConANN)", "Horchidan"),
    ("Johansson et al. 2019", "Johansson"),
    ("Johnson et al. 2021 (Faiss)", "Johnson"),
    ("Li et al. 2020", "Li"),
    ("Malkov & Yashunin 2020 (HNSW)", "Malkov"),
    ("Prokhorenkova & Shekhovtsov 2020", "Prokhorenkova"),
    ("Subramanya et al. 2019 (DiskANN)", "Subramanya"),
    ("Wang et al. 2026 (ANNiE)", "Wang et al., 2026"),
    ("Wang et al. 2022 (SafeBAI)", "Wang et al., 2022"),
    ("Xu et al. 2022", "Xu"),
    ("Yu 1997 (Le Cam Festschrift)", "Yu"),
    ("Zhang & Miller 2026", "Zhang"),
]

rows = []
for name, keys in REFS:
    keys = [keys] if isinstance(keys, str) else keys
    hits = {k: len(re.findall(re.escape(k), anchor_text)) for k in keys}
    anchored = all(v > 0 for v in hits.values())
    rows.append({
        "reference": name,
        "anchor_keys": "; ".join(f"{k}={v}" for k, v in hits.items()),
        "status": "ANCHORED" if anchored else "NO_IN_TEXT_ANCHOR",
    })

with open(OUT / "reference_anchor_audit.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["reference", "anchor_keys", "status"])
    w.writeheader()
    w.writerows(rows)
missing = [r["reference"] for r in rows if r["status"] != "ANCHORED"]
print(f"anchored={len(rows)-len(missing)}/{len(rows)}; missing: {missing}")
