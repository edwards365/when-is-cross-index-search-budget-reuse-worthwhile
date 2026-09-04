# Certification family audit

The audit is intentionally pre-certification.  Current counts are:

* operator trials: 0;
* generated candidate graphs: 0;
* candidate-selection actions: 0;
* independently certified actions: 0;
* `M_cert`: 0 (no certification family has been entered).

The only valid future values are the actual number of actions passed to one
simultaneous certifier: one selected action gives M=1; selected action plus a
newly certified fallback gives M=2; K graphs at L fixed-ef values give M=K*L.
The certification-family table records these possible definitions without
asserting that any action was certified.  Bonferroni alpha, CP bounds,
zero-failure thresholds, acceptance rates, and certification cost must be
recomputed from the realized M, never from the 24-trial search cap.

No certification query, certification per-query result, final evaluation, or
future-confirm artifact has been accessed.  This file is an audit record, not
an independent safety certificate.
