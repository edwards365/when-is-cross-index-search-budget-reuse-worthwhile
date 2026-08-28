# Open-world ICBA formal problem

An environment `theta` is a graph build. Queries are drawn from its
environment-specific distribution and actions lie on the frozen finite search
budget grid. Query risk and build-level deployment risk are distinct: a
query-level certificate within observed builds does not imply reliability for a
new build without an assumption on how builds are sampled or related.

The open-world decision observes a permitted channel `Z` and must choose either
a budget or a safe fallback. Z0 contains deployment metadata; Z1 would contain
unlabeled runtime fingerprints common to all implementations; Z2 contains
labeled target sentinel responses; Z3 is a source per-query Oracle. Frozen
Graph-ANNS evidence provides Z0, Z2 and Z3 but no common Z1. Only Z0/Z1 are
candidates for an unlabeled deployable recovery statement.

Right-censored queries have unknown minimum safe budgets above the grid and are
never imputed as the maximum grid point. Population endpoint infeasibility is
separated from finite-sample failure to certify an endpoint.
