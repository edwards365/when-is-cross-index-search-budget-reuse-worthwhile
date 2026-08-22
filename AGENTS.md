# Repository guidance

- Never invent benchmark results; every number in a report must trace to a committed config and a raw result file.
- Do not commit datasets, indexes, credentials, or large generated outputs.
- Keep test queries separate from all method/parameter selection.
- Preserve failed seeds and report them.
- Use C++17 for native code and Python 3.11 for the reference pipeline.
- Run `python -m pytest tests/python` and the CMake/CTest smoke test before committing algorithm changes.
- Effective resistance means the Moore-Penrose definition on a connected undirected weighted graph. Label regularized or component-wise variants explicitly.
- Local objective guarantees must not be presented as global ANN recall or complexity guarantees.

