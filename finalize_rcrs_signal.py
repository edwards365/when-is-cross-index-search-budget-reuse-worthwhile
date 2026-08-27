#!/usr/bin/env python3
import csv, hashlib, json
from pathlib import Path

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs')
RES=ROOT/'results/rcrs_signal'; DOC=ROOT/'docs/rcrs_signal'; DOC.mkdir(parents=True,exist_ok=True)
sift=json.loads((RES/'sift_signal_summary.json').read_text())
glove=json.loads((RES/'glove_signal_summary.json').read_text())
split=json.loads((ROOT/'manifests/rcrs_signal_query_split.json').read_text())

eq={}
for seed in (7,17,29):
    with (RES/f'glove/seed{seed}_equivalence.csv').open() as f:
        rows=list(csv.DictReader(f))
    eq[str(seed)]={'queries':len(rows),'all_topk_equal':all(r['topk_equal']=='1' for r in rows),
      'all_ndc_equal':all(r['ndc_equal']=='1' for r in rows),'all_trace_equal':all(r['visited_order_equal']=='1' for r in rows)}

decision={
 'label':'STOP_RCRS_NO_CERTIFIED_STOPPING_SIGNAL',
 'scope':'MINIMAL_CROSS_REBUILD_SEED_PILOT',
 'frozen_start':'01c491f712700bd146227c44db18848dd41d356a',
 'query_split_commit':'11a24b5','materialization_commit':'c0e184e',
 'query_sha256':split['query_content_sha256'],'truth_sha256':split['truth_content_sha256'],
 'preprocessing_correction':'The first temporary materialization omitted the preregistered L2 normalization. It was invalidated before policy selection; all GloVe traces and decisions were recomputed after exact Gate A normalization.',
 'prefix_equivalence':eq,'sift_design_signal':sift,'glove_gate':glove,
 'gates':{'S':False,'E':False,'P':True,'R':True,'G':False},
 'cross_history_confirmation':False,'new_indexes_built':False,
 'validation_dev_accessed':False,'formal_test_accessed':False}
(RES/'final_decision.json').write_text(json.dumps(decision,indent=2)+'\n')

(DOC/'input_audit.md').write_text(f'''# RCRS Signal Pilot input audit

- Frozen start: `01c491f712700bd146227c44db18848dd41d356a`
- Query split: 256 design, 256 calibration, 256 design-evaluation queries; seed 20261020.
- Query SHA256: `{split['query_content_sha256']}`
- Truth SHA256: `{split['truth_content_sha256']}`
- GloVe preprocessing: L2-normalized base and queries, matching frozen Gate A ingest.
- Existing indexes only: GloVe Original seeds 7, 17 and 29. No index was built.
- `validation-dev` and `formal-test` were not accessed.
- Correction audit: the initial temporary raw-vector materialization was detected by implausible fixed recall, invalidated before policy selection, and fully recomputed with the preregistered normalization. No grid, feature, seed, query or threshold was changed.
''')

(DOC/'risk_matched_theory.md').write_text('''# Risk-matched monotone result

The deterministic delta=0.05 dynamic program completed 568 of 648 cells; 80 frozen-grid/right-censored cells were infeasible. Mean complete-cell hnswlib risk-matched costs were 0.434873 (Arxiv), 0.819622 (GloVe), and 0.473278 (SIFT), expressed as fractions of fixed NDC. The older pointwise monotone tax remains much larger: 3.129691, 1.013613, and 2.697290 respectively. This weakens the universal pointwise-bound story but does not itself establish a deployable stopping rule.
''')

g=glove['design_eval']; c=glove['calibration']; b=sift['best_empirical_risk_le_5pct']
(DOC/'signal_pilot_report.md').write_text(f'''# RCRS Signal Pilot final report

## Result

Final label: **STOP_RCRS_NO_CERTIFIED_STOPPING_SIGNAL**.

SIFT design-only grouped cross-fitting showed a strong learnable signal (AUROC {sift['logistic_auroc']:.6f}, AUPRC {sift['logistic_auprc']:.6f}); its empirical design point had under-target risk {b['under_target_rate']:.3f} and gross NDC gain {b['gross_ndc_gain']:.3%}. This was not a certified held-out result.

The GloVe minimal pilot reused three frozen Original indexes. Each seed passed 768/768 native/prefix equality checks. With fixed L2 logistic regression (C=1, seed 991), 16 complete policies, n=256 calibration and Bonferroni correction, **0/16 policies certified**. Protocol therefore selected fixed-e0 fallback. Calibration under-target rate was {c['failure_rate']:.3%} (corrected upper bound {c['bonferroni_cp_upper']:.3%}); design-evaluation under-target rate was {g['failure_rate']:.3%} (corrected upper bound {g['bonferroni_cp_upper']:.3%}). Fallback Recall difference was {g['recall_difference']:.6f}, stop coverage {g['stop_coverage']:.1%}, and gross NDC gain {g['gross_ndc_gain']:.1%}.

Gate R passed. Gate S failed because no learned policy certified; consequently Gate E and minimal Gate G could not support promotion. Gate P is trivially non-worse under fixed fallback. Because only rebuild seeds of one history were available, this is `MINIMAL_CROSS_REBUILD_SEED_PILOT`, not cross-history confirmation.

## Conclusion

Checkpoint state is predictive on SIFT design data, but the frozen GloVe experiment provides no certifiable stopping policy under the prescribed finite-sample guarantee. The project must stop this RCRS algorithm route rather than add thresholds, features, histories or calibration samples after seeing the result.
''')

paths=[p for p in sorted(list(RES.rglob('*'))+list(DOC.rglob('*'))) if p.is_file() and p.name!='checksums.sha256']
lines=[]
for p in paths:
    lines.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}')
(RES/'checksums.sha256').write_text('\n'.join(lines)+'\n')
print(json.dumps({'decision':decision['label'],'hashed_files':len(lines),'equivalence':eq},indent=2))
