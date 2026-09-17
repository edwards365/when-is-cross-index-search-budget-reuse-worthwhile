# W4 validation

Stage W4 rewrites the experimental narrative around RQ1--RQ9.  It introduces no new experiment and leaves all 57 W0 frozen values unchanged.

## Structure

- Every RQ subsection contains the four explicit elements: Question, Protocol, Observation, and Conclusion.
- Decisive evidence (RQ1, RQ4, RQ5) precedes robustness, economics, extension, and reproducibility evidence.
- DARTH/Ada-ef, Vamana, and Deep1M remain protocol-separated rather than forming a pooled leaderboard.
- Placeholder experimental figures and future-tense result prose from W3 were removed.

## Checks

- `freeze_w0.py --check`: PASS; 57 frozen numbers.
- `check_w3_math.py`: PASS; 10/10 deterministic checks.
- `check_w4.py`: PASS; RQ1--RQ9 and all four paragraph elements present.
- Tectonic 0.17.0 compilation: PASS.
- Output: 8 pages; no unresolved references or overfull boxes.
- Visual inspection: all 8 pages inspected; tables fit their columns and no content is clipped.

## Remaining scope limits

The individual candidate and endpoint Clopper--Pearson bounds are not described as a joint 95% certificate.  Lifecycle values remain conditional on the source-profile cost treatment.  Query-pooled tail comparisons are distance-count observations, not wall-clock noninferiority certificates.
