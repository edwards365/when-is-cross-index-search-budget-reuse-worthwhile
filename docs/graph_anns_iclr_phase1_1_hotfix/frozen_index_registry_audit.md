# Frozen-index registry audit

The parent build registry was compared row-by-row to current serialized indices: 48/48 rows matched index SHA256, base count, Faiss version, M and efConstruction; base HDF5 file SHA256 matched the source registry for every dataset=True. Observed dimension/metric came from the Faiss index object; build/order metadata came from the frozen registry. See `frozen_index_registry_audit.csv`.
