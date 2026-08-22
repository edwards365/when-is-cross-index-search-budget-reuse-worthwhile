# Assumptions

1. The resistance graph is explicitly symmetrized and nonnegative.
2. Standard resistance is evaluated only within connected components; cross-component pairs have infinite resistance.
3. Candidate leverage is computed before greedy selection and is not recomputed after each choice in the v0.1 objective.
4. Candidate directions are nonzero and coefficients `alpha`, `beta`, `gamma` are nonnegative.
5. Any navigation statement additionally requires candidate coverage and metric progress assumptions; spectral importance alone is insufficient.

