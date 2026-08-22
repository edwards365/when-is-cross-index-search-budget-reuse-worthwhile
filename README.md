# Navigation-Aware Resistance Graph for ANNS

This repository is a reproducible feasibility study of whether local effective-resistance edge leverage and directional coverage can improve finite-degree proximity graphs. HNSW is the first experimental vehicle; the scientific scope is broader than HNSW.

The current phase tests two preregistered hypotheses: whether missing high-leverage local edges explain hard queries (H1), and whether degree-preserving local rewiring improves cost at matched recall (H2). Positive and negative results are retained.

## Reproduce the local smoke experiment

Requirements: Python 3.11 and a C++17 compiler. On Windows, use an x64 Visual Studio developer shell.

```powershell
conda env create -p .venv -f environment.yml
conda run -p .venv python -m pip install -e .
conda run -p .venv python scripts/data/generate_synthetic.py --name narrow_bridge --n 2000 --seed 7
conda run -p .venv python scripts/experiments/run_smoke.py --config configs/experiments/smoke.yaml
conda run -p .venv python -m pytest tests/python -q
cmake -S . -B build
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

Generated data, indexes, and raw benchmark output are ignored by Git. Each run writes its configuration, source commit, hardware ID, timestamps, seed, and status. See [methodology](docs/methodology.md), [reproducibility](docs/reproducibility.md), and [current status](reports/STATUS.md).

## Modeling boundary

The first implementation symmetrizes local directed neighborhoods and computes exact Moore-Penrose resistance only on small connected candidate graphs. Disconnected pairs are reported as infinite unless an explicitly named alternative policy is selected. No local submodular guarantee is interpreted as a global HNSW recall guarantee.

## External components

- `third_party/hnswlib`: upstream nmslib/hnswlib pinned as a Git submodule; its own license is preserved.
- Faiss, VIBE, DiskANN, ANN-Benchmarks, and Big-ANN-Benchmarks are recorded in `third_party/LOCKS.md`; they are not vendored for the Tier-0 smoke phase.

