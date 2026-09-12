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

## Addendum 4 — v3 Overleaf fixes + P8 integration (user compile report)

User compiled v2 on Overleaf: hard error (\newcommand{\Pr} — \Pr is a LaTeX kernel
command), plus style-missing chain when the ICLR kit is absent, and wide tables
overflowing the single-column text block. v3 (ICBA_ICLR_Anonymous_Revised_v3.tex):

1. Preamble now auto-detects iclr2027_conference.sty (\IfFileExists); fallback is
   self-contained (geometry+times+natbib+fancyhdr with the Under-review footer) — compiles
   on Overleaf with or without the official kit.
2. \Pr fixed via \renewcommand{\Pr}{\mathop{\mathrm{Pr}}}.
3. All 13 tables converted to width-bounded p{}-column layouts with \footnotesize or
   \scriptsize and 2.6-4pt tabcolsep; worst-case estimated width 14.9cm vs 16.5cm text
   block; column-count consistency machine-checked (13/13 tables).
4. P8 rebuttal evidence integrated: takeaway table (scenario->route->boundary) after
   contributions; h-sensitivity table + paragraph in 7.1; gamma-sensitivity refinement of
   the Theorem-2 verdict (certification power binds, not margin existence); rich-probe
   qualification in 7.5 (runtime features 0.56-0.58 median, 0.72 max -> TV 0.44, claim
   probe-class-qualified); quantile-pooling sentence in 7.4; canonical-order-as-default
   wording in the decision rule; 2% gate rationale sentence; abstract TV clause updated.
5. Static validation: env/brace balance OK, 23 cites <-> 23 bibitems, all refs/labels
   resolve, no kernel-command collisions, all 7 figures present.

Delivered to /home/wlk/Downloads/ICBA_ICLR_LaTeX/ (v3 tex + figures). No TeX toolchain on
the server: final visual pass happens on Overleaf by construction.

## Addendum 5 — v4 (three-review response: N1 fix, wording sync, page limit)

Triggered by the third review round (R_A 6, R_B re-review 6 with N1, R_C pre-review 4 with
page-limit fatal). Changes in ICBA_ICLR_Anonymous_Revised_v4.tex:

1. N1 CLOSED: h-sensitivity table recomputed in the incremental (Eq. 20) caliber for ALL
   cells (results/graph_anns_phase2_p8/h_sensitivity_incremental.csv, 15 values); the
   h=10 column now reproduces the registered incremental estimates by construction
   (hnswlib rows land on the E4-primary 21.57/17.12 per the Appendix-F crosswalk; Faiss
   and 1M match to the digit), with an explicit crosswalk sentence.
2. Margin wording synchronized at SIX sites (abstract, contributions bullet, theory 4.2,
   7.4 verdict, conclusion): "certification power, not margin existence, binds".
3. Theorem-1 premise paragraph rewritten as probe-class evidence with the joint-
   information caveat (runtime features are functions of (q,build); conflict rate
   supports but does not instantiate D-regions/Delta).
4. M2 relabeled as a pooled REPLAY policy with a source-label cache; coverage equals
   workload query-repeat rate; cold queries fall back.
5. New end-to-end ledger (Table e2e): transport vs pooled replay vs profile-and-certify
   (0.12-0.99 s incl. truth; certifies max budget only, P=0.47-0.63) vs contract —
   answers reviewer Q4: cost was never binding; attainability and certification power are.
6. 1M contract times reported honestly: median 252 s (13 builds), identity rebuilds 238 s;
   8-thread 1M ratio NOT measured (flagged).
7. Eq. 20 auditability: per-sample BOT->max mapping and target-bottom reference event
   stated explicitly.
8. PAGE LIMIT: main text compressed 63.2k -> 55.7k chars; figures in main 5 -> 2
   (setting, pooling); tables in main 11 -> 5 (takeaway, crossfamily, constructive, p6,
   e2e); moved to appendix: semantics/theory/hsens/economics/contract/vamana/ladder
   tables, workflow/crossfamily/plane/ablation/ladder figures, protocol detail
   paragraphs; related work and ICBA and limitations and conclusion condensed. Calibrated
   estimate (from the user's compiled v2: ~8.8k chars/page effective) puts main at ~8.5
   pages, within the 9-page initial-submission limit; references follow (uncounted).

Static validation: env/brace/cite/label/figure checks clean; all 12 content probes and
the 12-slot layout audit pass.
