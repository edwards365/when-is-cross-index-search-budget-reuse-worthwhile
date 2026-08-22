# Phase I reproducibility record

## Frozen environment

- Result-code commit: `ba90eda1cbbedc4bb8a9474b540622d9882cb79f`
- hnswlib submodule: `3f3429661187e4c24a490a0f148fc6bc89042b3d`
- Hardware ID: `LAPTOP-Q79U6UF3-AMD64`
- Tier: 0; Windows; 15.627 GiB RAM; 32 logical CPUs
- Python: 3.11.16; MSVC 19.44; CMake 3.30.5
- Formal graph seed: 7
- Independent holdout seed: 101
- Random control seed: 313
- Bootstrap seed/replicates: 991 / 5,000

Exact environment and artifact hashes are in `artifacts/phase1_manifest.yaml`.

## Verified commands

```powershell
conda run -p .venv python -m pytest -q
conda run -p .venv ruff check python scripts tests theory
.venv\Library\bin\cmake.exe --build build --config Release --parallel 2
.venv\Library\bin\ctest.exe --test-dir build -C Release --output-on-failure
conda run -p .venv python scripts/experiments/run_controlled_swap.py `
  results/raw/controlled_swap_fixture_s7 `
  results/raw/candidate_scoring_s7/candidate_scores.csv `
  results/raw/query_attribution_s7/failure_query_support.csv `
  results/raw/phase1_reproduction_ba90eda
conda run -p .venv python scripts/analysis/audit_phase1_artifacts.py `
  artifacts/phase1_manifest.yaml
```

## Closure audit

On 2026-08-22 the suite passed Python 48/48, Ruff, and CTest 2/2. The native smoke test exercises insertion and query replay. The formal controlled-swap reproduction regenerated five outputs byte-for-byte: `swaps.csv`, `heldout_query_results.csv`, `heldout_summary.csv`, `paired_comparisons.csv`, and `metadata.json`.

Raw datasets and result files are intentionally ignored by Git. The manifest records their relative paths and SHA-256 values; regeneration scripts and code are committed. The formal summary is sourced only from `controlled_swap_eval_s7`. The invalid base-perturbation run is not a source for any formal table.
