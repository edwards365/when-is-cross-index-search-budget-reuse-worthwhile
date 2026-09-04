# GSC statistical report (smoke)

The validation layer contains 500 disjoint queries and three raw fixed-`ef`
values (16, 32, 64), with the first 200 queries used only for proposal response
scores.  The C++ counting-space evaluator reports exact NDC and checks tracer
versus native top-k equality.  The smoke is too small and single-subset to
support a build-cluster certificate; no 5000-bootstrap certification was run.

At ef 16, O6-robust improves mean NDC by 0.143% and p95 by 0.779% but lowers
recall by 0.0014.  At ef 64, O6-conservative has the best recall-safe p95
change (-0.071%) while mean NDC worsens 0.120%; the preregistered half-tail
threshold is 2.5%.  Other rows likewise fail to jointly satisfy the hard
recall constraint and half-track threshold.  Therefore no primary track is
frozen and no candidate enters certification.
