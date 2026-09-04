Evidence level: EXPLORATORY_FIXED_TARGET_CALS_AUDIT.
Frozen branch: exp/icba_cals_oracle_attainability (derived from c9c4915cf626d6170132c7beafd2dbbc58b44776).
All values use target-build as the outer unit, query as the inner unit, tau=0.99, delta=0.05, gamma=0.01 and seed 991.
Oracle/per-query choices are explicitly NON_DEPLOYABLE_UPPER_BOUND; no Oracle is an algorithm.

# CALS input and resource audit
SIFT-100K and Arxiv-Nomic-100K used only their existing original b7/b17/b29 indexes and first 500 test queries as design/attainability inputs. GloVe, validation-dev, formal-test, certification/evaluation/future roles were not accessed. Root free space was approximately 18 GiB at the run; generated artifacts are small and streaming-safe. The external theory reference 6dbe4892ea4c7a2f1a22226c9d62f27b6654ba21 was not a local ancestor and is therefore recorded with provenance limitation; the available theory bundle is /home/wlk/projects/icba_theory_lock_ed8d1e0_incremental.bundle (SHA256 336dd347bbbab343bd83b7bad877cf2ae5b056780ab5e37a50431eb444dbe124), read-only.
