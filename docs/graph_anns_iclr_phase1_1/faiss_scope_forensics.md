# Faiss scope forensics

The historical Faiss runner and registry both show `base_count=30000` for SIFT and Arxiv. The cause is an explicit `train[:30000]` loader slice. The source HDF5 files contain at least 100,000 train vectors for both datasets. Historical 30K results therefore remain a registered 30K subset; they are not relabeled as 100K. A separate 100K scope-correction registry was completed with 24 builds per dataset and is never mixed into the 30K estimand. The 100K results pass the registered strong scope Gate on both datasets.
