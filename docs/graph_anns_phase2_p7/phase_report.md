# Phase P7 report — major paper revision to ICLR-style DOCX

## Goal
Apply R1-R12 + all P6 findings as a full manuscript rewrite; deliver an anonymous
ICLR-template DOCX with figures, tables, and equations.

## Toolchain deviation (recorded)
The docx skill's primary path (docx-js via node/bun) is unavailable: no node/bun in the
environment and no reachable npm registry; pip cannot reach PyPI for python-docx. The build
therefore constructs the OOXML package with the Python standard library (zipfile + XML),
following the skill's formatting standards: 1.3x line spacing (w:line=312), real Heading1-3
styles, Caption style, table cell margins, CLEAR header shading, top/bottom booktabs-style
borders, cantSplit + tblHeader, aspect-preserving images, keepNext captions/headings,
A4 with 1in margins, footer page numbers. Postcheck: 9/9 passed.

## Deliverables
- results/graph_anns_phase2_p7/ICBA_ICLR_Anonymous_Revised_v2.docx (834 KB):
  526 paragraphs, 11 tables, 28 drawings (7 figures + 21 rendered equations),
  62,129 characters of body text.
- All revision content integrated: rewritten abstract (P6 numbers + pooling boundary +
  predictor verdict + TV instantiation); multi-replica motivation; three-layer evidence
  framing; D1-D8 definitions in Sections 3-5; estimand crosswalk in Appendix F; Vamana
  boundary panel (Table 4, daggered); constructive Section 7.4 (Table 6 + Figures 4-5 +
  Theorem-2 verdict); contract ablation Section 7.3 (+Figure 6); P6 Section 7.5 (Table 7);
  economics Table 8 + grid sensitivity; compressed ladder (Table 9 + Figure 7); all six
  previously-unanchored references anchored in Related Work/Theory; updated limitations,
  claim registry, reproducibility, and artifact manifest (including the three
  origin-unlocated aggregates flagged).
- Figures: 3 original (setting, workflow, cross-family) + 3 new (pooling ladder, decision
  plane, ablation) + original ladder figure; equations rendered at 300 dpi via matplotlib.

## Verification (step 3)
- All package XML parts well-formed; re-extraction reproduces all probe strings (21 content
  probes pass); image count == figure + equation count; postcheck 9/9.
- Build bug fixed during review (missing </wp:inline> closing tag) — code-only fix, content
  unchanged; rebuilt and revalidated.

## Known limitation
No LibreOffice in the environment: the exported-PDF page-by-page render check cannot run
here. The user must open the DOCX in Word/WPS, confirm equation/table/figure rendering, and
export the submission PDF; the earlier extraction-failure lesson (judge PDFs, not text
extracts) applies. Inline math uses italic runs (B_E(q) style); camera-ready may upgrade to
native equation objects if desired.

## Addendum — native-equation edition (user request)

All 21 display equations converted from 300-dpi PNGs to native Word equation objects
(OMML) via a fail-fast LaTeX->OMML converter (scripts/graph_anns_phase2/p7/eq_omml.py;
21/21 converted, XML-validated). Equation paragraphs use center/right tab stops with the
(1)-(21) numbers; math font pinned to Cambria Math through settings.xml mathPr
(nary limits under/over, display defaults). Package no longer embeds equation PNGs
(834 KB -> 599 KB). Postcheck 8/9 - the single advisory is the Cambria Math font,
standard in Word/WPS. Tests 20/20. Delivered copy: /home/wlk/Downloads/.

## Addendum 2 — Word/WPS compatibility fixes (user report)

User reported: Word repair dialog on open; WPS dropped images and partially failed to
render equations as equation objects. Root cause: hand-constructed OOXML violated the
strict CT_PPr / CT_RPr / CT_TcPr child-order schemas (jc before spacing/ind; keepNext
before pStyle; rFonts after b/i; shd after tcMar). Word enters repair mode on such
files and renderers drop affected paragraphs (explaining missing images and unparsed
equations). Fixes: (1) schema-ordered emission everywhere; (2) tcBorders inserted
between tcW and shd; (3) \mathrm groups emitted as single upright runs via raw-group
capture. Added scripts/graph_anns_phase2/p7/schema_check.py asserting zero child-order
violations (now part of the build gate). Rebuilt: 598,415 bytes; XML valid; 21 oMath,
7 figures, 11 tables; tests 20/20; postcheck 8/9 (Cambria Math advisory only).
Redelivered to /home/wlk/Downloads/.

## Addendum 3 — LaTeX source edition (user request)

Full LaTeX source delivered (ICBA_ICLR_Anonymous_Revised_v2.tex, 1,216 lines / 72.8 KB):
ICLR-style preamble (official-kit preferred, article-class fallback documented), 21 native
LaTeX display equations with \label/\ref cross-references, 11 booktabs tables, 7 figure
includes, theorem environments, and a self-contained thebibliography (23 entries).
Structural validation: environment and brace balance OK; 23 citations <-> 23 bibitems
(no undefined, no uncited); all 7 figure files present; no undefined references.
Delivered to /home/wlk/Downloads/ICBA_ICLR_LaTeX/ (tex + figures).
