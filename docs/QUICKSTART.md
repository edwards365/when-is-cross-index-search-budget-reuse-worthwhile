# Quickstart

This guide separates compact verification from expensive native replay. Start with the smallest tier that answers your question.

## 1. Requirements

- Git
- Python 3.10--3.13 (the delivered clean manuscript replay used Python 3.11)
- Bash for artifact shell entry points
- CMake and a C++17 compiler only for native tests or full experiments

No GPU is required for the compact artifact or the registered CPU experiments.

## 2. Create an isolated environment

Linux/macOS:

```bash
git clone https://github.com/edwards365/navigation-aware-resistance-hnsw.git
cd navigation-aware-resistance-hnsw
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[analysis,test]'
```

Windows PowerShell:

```powershell
git clone https://github.com/edwards365/navigation-aware-resistance-hnsw.git
Set-Location navigation-aware-resistance-hnsw
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[analysis,test]"
```

The reviewer-facing shell scripts are validated on Linux. On Windows, use Git Bash/WSL or run the Python checks listed in the artifact README.

## 3. Lightweight artifact smoke

```bash
bash artifacts/graph_anns_phase3_ea85/reproduce_smoke.sh
```

Expected scope:

- verify sealed input checksums;
- parse all recorded phase decisions;
- check selection/certification/evaluation role isolation;
- rerun the compact Phase 5 integration; and
- run focused tests.

This tier does not download datasets, build indexes, or access reserved truth.

## 4. Regenerate paper-facing tables

```bash
bash artifacts/graph_anns_phase3_ea85/reproduce_tables.sh
```

Outputs are written under the existing result and figure directories. The scripts check their committed inputs before regeneration.

## 5. Replay the manuscript package

```bash
cd paper/sigmod2027
python evidence/replay_graph_only_intervals.py
python evidence/check_postseal.py
python make_figures.py
python check_evidence.py
python run_clean_replay.py --package .
```

This validates compact evidence and, when a supported LaTeX engine is installed, rebuilds the main paper and appendix. See [the manuscript README](../paper/sigmod2027/README.md) for exact tool versions and build notes.

## 6. Run the general test suite

```bash
python -m pytest tests/python theory/tests -q
ruff check python scripts tests theory
cmake -S . -B build
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

Native tests require the pinned hnswlib submodule and a working C++17 toolchain.

## 7. Full external-data replay

The full path requires checksummed external datasets/indexes and more storage. It is intentionally gated:

```bash
bash artifacts/graph_anns_phase3_ea85/run_artifact.sh full-check
ICBA_FULL_REPLAY_ACK=YES bash artifacts/graph_anns_phase3_ea85/run_artifact.sh full
```

Read [full_replay.md](../artifacts/graph_anns_phase3_ea85/full_replay.md) first. Do not substitute unregistered datasets, roles, action grids, or truth sources and describe the result as a reproduction.

## 8. Common interpretation mistakes

- NDC is distance-computation work, not wall time.
- Per-target or per-decision certificates are not simultaneous campaign certificates.
- Endpoint-relative recovery is not the same as incremental value over a strong target-calibrated baseline.
- A fallback is a valid safety outcome, not a missing result.
- Historical stage folders are provenance, not the recommended starting point.
