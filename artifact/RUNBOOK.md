# Reproduce the selected saved-response analyses

## Scope and inputs

This entry reconstructs nine tables for the same-condition summary-cost diagnostic, qualification sensitivity and fixed-cost components (§4–6). It uses the frozen qualification/evaluation responses and original locked decisions. It does not execute ANN, construct an index, obtain new exact truth, train a model, regenerate bootstrap intervals, or cover every paper panel.

The Release asset contains four response NPZs, numeric query-membership IDs, policy/decision records, the cost ledger and an audit receipt. No source vectors, original documents or indexes are included. All NPZs are byte-identical to their pinned source files. The audit JSON replaces private absolute paths with basenames; the manifest records both original and published hashes. Its extra source/design audit rows are retained for provenance, but those arrays are not dependencies of this particular analysis.

The original policy document records the preregistered formulation. For the executed qualification event, use the decision lock and analysis implementation together; the historical policy text alone does not replace the actual union-event protocol described in the paper.

## 1. Obtain this release

Use a checkout of the `artifact-response-v1` tag. From its repository root, download [summary-analysis-inputs.zip](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/download/artifact-response-v1/summary-analysis-inputs.zip), or use GitHub CLI:

```sh
gh release download artifact-response-v1 --repo edwards365/when-is-cross-index-search-budget-reuse-worthwhile --pattern summary-analysis-inputs.zip
python artifact/reproduce_summary.py --archive summary-analysis-inputs.zip --check-inputs
```

The input-only check uses the standard library and verifies the archive, complete member list, member sizes and hashes before extraction. Downloading GitHub's source-code ZIP alone does not include Release assets.

## 2. Create an isolated environment

The research reference pipeline used Python 3.11. This portable entry was tested on Windows with Python 3.12.14, NumPy 1.26.4 and SciPy 1.13.1. Python 3.11 compatibility is intended, but no additional 3.11 portability run is claimed here. Use Python 3.12 to reproduce the recorded check:

```sh
python -m venv .venv-artifact
```

Activate it using `.venv-artifact\Scripts\activate` on Windows or `source .venv-artifact/bin/activate` on Linux/macOS, then:

```sh
python -m pip install -r artifact/requirements-analysis.txt
python artifact/check_saved_results.py
python -m unittest discover -s artifact -p "test_*.py"
```

NumPy and SciPy retain their upstream licenses. The dependency file pins versions, not platform-specific wheel hashes; this is not a fully offline environment archive.

## 3. Reconstruct and compare

```sh
python artifact/reproduce_summary.py --archive summary-analysis-inputs.zip --output reproduction-output
```

The output directory must not already exist and must be outside `artifact/`. It holds extracted copies, a resolved audit view, derived CSVs and `verification.json`. An error leaves `failure.json` rather than overwriting prior evidence. No network or dataset acquisition occurs during this command. Use a standard CPU workstation; the original derivation used a 1 GiB RSS stop threshold, not a measured minimum memory requirement. The portable wrapper uses one library thread but does not reproduce the original process-level resource sandbox.

## What PASS means

All nine CSVs must have the same schema and row order as the saved results. Statuses, decisions and strings must match; differing finite numerical cells must satisfy `rel_tol=1e-10, abs_tol=1e-9`. Empty values remain empty, not zero. In the recorded run, eight tables were byte-identical; the remaining qualification table differed only numerically within tolerance. The comparison report exposes non-identical cell counts rather than claiming bitwise reproduction.

This verifies the portable reconstruction of selected derived outputs. It does not independently remeasure recall/NDC, validate all historical records, or prove complete paper reproduction. Full-query infeasibility, conditional-subset weighting, singleton coverage and all targets are preserved.
