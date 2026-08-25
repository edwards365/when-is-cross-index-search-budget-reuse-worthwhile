## 2026-08-25 — main-matrix orchestration

- Gate R passed before this amendment.
- `run_ocgt_v3_main_matrix.py` executes the byte-for-byte frozen Gate R runner (SHA256 `db37a9915a63b2b18c5152b0e46f4e92b46e19d4c2903f0cb54d88e3e1ac8a77`) with only the preregistered graph seed and output-directory literals changed to 59 and 71.
- It conservatively repeats every new graph twice. Only repetition 1 enters the 27-graph primary matrix; repetition 2 is determinism evidence and cannot affect endpoints or tuning.
- No data, query, graph order, HNSW parameter, ef value, schema, endpoint, threshold or analysis rule changed.
