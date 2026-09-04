# GSC operator-proposal freeze (pre-certification)

The frozen 72-cell sentinel slack audit is complete. Proposal generation now
registers eight deterministic O4/O6 configurations, with one conservative
configuration for each primary operator. The proposal stage may carry
Stability, Mean, and Tail as candidate tracks, but it has no access to
certification, final-evaluation, or future-confirm data.

The proposal table is a plan, not an experiment result: actual_operator_trials
and generated graphs remain zero until a configuration is actually executed.
Every configuration is constrained to the frozen SIFT/Arxiv graph representation
and response traces; no threshold, track, or tolerance is tuned from held-out
results. O4 is response-weighted robust pruning and O6 is response-aware
insertion scheduling. O3/O1 remain mechanism and determinism baselines, not
GSC method claims.

After proposal/validation, one action and one primary track must be frozen in
manifests/icba_gsc_final_track_freeze.json before any certification query is
opened. Certification will then use the realized action count as M_cert; the
24-trial cap is not a certification family.
