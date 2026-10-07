# Newly executed recovery results → statistical outputs

`analyze_new.py` accepts **new typed receipts**, not historical paths or saved
paper statistics. It closes the seven-repeat timing → technical means → paired
source/target/query cells → confidence intervals path for S9-3 and S9-4.
It never searches an index, retimes a query, or overwrites a historical result.

Prerequisites: Linux/Python 3.11, this directory's pinned `requirements.txt`, and
one completed new `lock`, `evaluate`, all 16 `timing` units plus the 16 evaluation
role profiles. The same lock SHA must bind evaluation and every timing unit.
Use a fresh output directory; keep any failed output and diagnose before retry.

Request JSON:

```json
{
  "family": "3",
  "lock": {"directory": "/new/lock", "completed_sha256": "SHA"},
  "evaluation": {"directory": "/new/evaluation", "completed_sha256": "SHA"},
  "response_manifest": "/new/evaluation-profile-map.json",
  "timings": [
    {"directory": "/new/timing-unit", "completed_sha256": "SHA"}
  ]
}
```

The `timings` array must contain all 16 distinct registered units; the abbreviated
example is not executable until complete. The response manifest is the same
16-profile manifest used by the new evaluation stage. Change family to `4` for
the separate baseline panel; never mix family 3 and family 4 roles or receipts.

```sh
python analyze_new.py --request new-analysis.json --output /new/analysis \
  --authorize-new-analysis
```

The entry validates every parent file's SHA/size, family and lock; exactly seven
repetitions per action/query; all 500 queries and all 16 builds; deterministic
returned-ID hashes; and complete matching of timing hashes to native evaluation
responses. It recomputes evaluation cells using the fixed decisions as an
integrity check before any statistics. S9-4's evaluation oracle remains marked
nondeployable and is excluded from deployable runtime aggregation.

The four `analysis*_core.py` files retain original statistical functions and the
runtime summary statements from `analyze_s9_3_prospective.py`,
`analyze_s9_3_runtime.py`, `analyze_s9_4_arms.py`, and
`analyze_s9_4_runtime.py`. The maintenance assembler is
`artifact/build_recovery_analysis.py`. Its separate `analysis_config.json`
pins both the unchanged stage producer/config and extracted statistical code;
it does not invalidate existing new stage receipts by modifying their config.

Seven technical repetitions are averaged **before** policy attachment. Original
source-direction weighting is retained inside target/query cells. Crossed
bootstrap resamples targets and shared query positions, preserves source
directions and paired endpoints, uses 5,000 repetitions with seed 991, and
returns original 2.5/97.5 percentile intervals. Original leave-one-target-out,
top-1% query-benefit deletion, action-block CV and deployment gates are retained.
These are new-result intervals, not a claim of matching historical clock values.

Outputs include `primary_summary.json`/`arm_ndc_summary.json`,
`runtime_summary.json`/`arm_runtime_summary.json`, technical means, attached
runtime cells, block CV, and a hashed `completed.json`. Saved-paper resampling
and preregistered sensitivity reconstruction remain separate published paths;
this entry does not select a new strategy or expand the original action grid.

Bound: CPU2, one library thread, 4 GiB address space, 512 MiB single-file and total
output, 3,600 CPU seconds, 7,200 wall seconds. Non-finite or incomplete data stops
the stage. Packaging tests use only synthetic frames with seven bootstrap draws
for speed; production defaults are never changed. No historical timing or full
historical bootstrap was rerun during packaging.
