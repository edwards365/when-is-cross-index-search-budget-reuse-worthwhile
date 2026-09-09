# Reproducibility report

The unified entry point is `python -m scripts.graph_anns_e4_seal.run`. Required arguments parameterize repository root, frozen build manifest, raw directory, seed, bootstrap count, and output directory. Runtime versions are recorded in `environment.json`. The raw inputs are individually inventoried and hashed; build identity is unique by dataset/seed/order. Two clean runs with seed 991 and 5000 resamples produce byte-identical core CSV files. The compatible project-local C++ runtime path must precede the system library path: `LD_LIBRARY_PATH=/home/wlk/projects/navigation-aware-resistance-hnsw/.venv/lib`.

No interactive notebook state is required. The replay reads only frozen E4 raw records and frozen query manifests. It does not build indexes or execute searches. Checksums intentionally exclude caches, logs, temporary files, and compiled products.
