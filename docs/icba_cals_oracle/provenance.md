Evidence level: EXPLORATORY_FIXED_TARGET_CALS_AUDIT.
Frozen branch: exp/icba_cals_oracle_attainability (derived from c9c4915cf626d6170132c7beafd2dbbc58b44776).
All values use target-build as the outer unit, query as the inner unit, tau=0.99, delta=0.05, gamma=0.01 and seed 991.
Oracle/per-query choices are explicitly NON_DEPLOYABLE_UPPER_BOUND; no Oracle is an algorithm.

# Provenance and role firewall
Existing hnswlib indexes are immutable inputs. SIFT and Arxiv each have 500 design queries split as portal_selection=200 and attainability_holdout=300; certification_reserved, evaluation_reserved and future_confirmation are sealed/empty in this audit. Query-role overlap is zero. The bridge executable is project-side only and does not alter third-party source or old result files. This is a fixed-target audit, not an open-world claim.
