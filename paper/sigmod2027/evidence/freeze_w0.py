"""Freeze published-table values at a Git revision; never rerun experiments."""
import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from pathlib import Path

BASE = 'd0ceb9bafa12480d04d4ae473b4c669e0e5b6ff5'
P = 'results/graph_anns_phase3_ea85/'


def assemble(repo):
    inputs, numbers = {}, []

    def read(path):
        content = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=repo)
        # Git text normalization may store LF while the generated CSV uses CRLF.
        if (repo / path).read_bytes().replace(b'\r\n', b'\n') != content.replace(b'\r\n', b'\n'):
            raise ValueError(f'Input changed since freeze baseline: {path}')
        inputs[path] = hashlib.sha256(content).hexdigest()
        return content.decode('utf-8')

    def table(path):
        return list(csv.DictReader(io.StringIO(read(path))))

    def add(macro, value, path, selector, column, unit, boundary, status='NUMERICALLY_VERIFIED_SCOPED'):
        value = float(value)
        assert math.isfinite(value)
        display = f'{value * 100:.2f}' if unit in ('percent', 'percentage_points') else f'{value:.0f}' if unit in ('queries', 'count') else f'{value:.2f}'
        numbers.append(dict(macro=macro, value=value, display=display, unit=unit,
                            source=path, row_selector=selector, column=column,
                            claim_boundary=boundary, status=status))

    path = P + 'refresh95/summary.csv'
    rows = table(path)
    for ds, name in [('sift100k', 'Sift'), ('arxiv_nomic_100k', 'Arxiv')]:
        for method, prefix in [('SOURCE_TCP_POOL_REUSE', 'Source'), ('TARGET_SELECTION_TCP_RECALIBRATION', 'Target')]:
            row = next(r for r in rows if r['dataset'] == ds and r['method'] == method)
            selector = {'dataset': ds, 'method': method}
            boundary = 'Registered query-indexed old-build profiles; empirical target Recall@10<.95 rate; no novel-query zero-label guarantee.'
            for field, suffix, unit in [('evaluation_risk','Risk','percent'), ('mean_gain','Gain','percent'), ('gain_ci_low','GainLow','percent'), ('gain_ci_high','GainHigh','percent'), ('p95_dists','Pninetyfive','distance_evaluations'), ('fixed_p95_dists','FixedPninetyfive','distance_evaluations'), ('fallback_builds','FallbackBuilds','count')]:
                add('WZero'+name+prefix+suffix, row[field], path, selector, field, unit, boundary)
            gain = 1 - float(row['mean_dists']) / float(row['fixed_mean_dists'])
            assert abs(gain-float(row['mean_gain'])) < 1e-12
            assert int(row['tail_p95_noninferior']) == int(float(row['p95_dists']) <= float(row['fixed_p95_dists']))

    per_build = table(P+'refresh95/per_build.csv')
    for row in rows:
        subset = [r for r in per_build if r['dataset']==row['dataset'] and r['method']==row['method']]
        assert len(subset)==10
        pooled = sum(int(r['evaluation_failures']) for r in subset) / sum(int(r['evaluation_n']) for r in subset)
        assert abs(pooled-float(row['evaluation_risk'])) < 1e-12

    path = P+'darth95_bridge/dataset_summary.csv'
    for row in table(path):
        if row['method']!='raw_darth':
            continue
        name = 'Sift' if row['dataset']=='sift_100k' else 'Arxiv'
        add('WZeroDarth'+name+'Risk', row['mean_eval_risk'], path,
            {'dataset':row['dataset'],'method':'raw_darth'}, 'mean_eval_risk','percent',
            'Registered DARTH bridge and risk event; not a general published-method ranking.')

    path = P+'adaef_bridge/arxiv_10build/aggregate.json'
    row = json.loads(read(path))['intervals']['raw_eval_risk']
    for field, name in [('mean','Risk'),('ci95_low','RiskLow'),('ci95_high','RiskHigh')]:
        add('WZeroAdaefArxiv'+name,row[field],path,{'json_pointer':'/intervals/raw_eval_risk'},field,'percent','Official Ada-ef bridge; ten registered targets.')

    path=P+'vamana_unified/summary.csv'
    for row in table(path):
        name='Sift' if row['dataset']=='SIFT-100K' else 'Arxiv'
        for field,suffix in [('transport_risk','Risk'),('risk_ci_low','RiskLow'),('risk_ci_high','RiskHigh')]:
            add('WZeroVamana'+name+suffix,row[field],path,{'dataset':row['dataset']},field,'percent','Post-hoc realignment; six source and six distinct target builds; 36 directions; native l action.')

    path=P+'deep1m/summary.csv'
    row=table(path)[0]
    for field,suffix,unit in [('transport_risk','Risk','percent'),('reference_risk','ReferenceRisk','percent'),('incremental_risk','Increment','percentage_points'),('builds','Builds','count'),('queries','Queries','count'),('directed_pairs','Pairs','count')]:
        add('WZeroDeep'+suffix,row[field],path,{'row':0},field,unit,'First-1M; eight builds; target-build conditional inference; reference failures retained.')
    assert abs(float(row['transport_risk'])-float(row['reference_risk'])-float(row['incremental_risk']))<1e-12
    for i,suffix in enumerate(['IncrementLow','IncrementHigh']):
        add('WZeroDeep'+suffix,json.loads(row['incremental_risk_ci'])[i],path,{'row':0},f'incremental_risk_ci[{i}]','percentage_points','95% interval for risk difference, in percentage points.')

    path=P+'lifecycle_cost/dataset_summary.csv'
    for row in table(path):
        name='Sift' if row['dataset']=='sift100k' else 'Arxiv'
        for field,suffix,unit in [('ratio_of_means_break_even_queries','BreakEven','queries'),('bootstrap_break_even_ci_low','BreakEvenLow','queries'),('bootstrap_break_even_ci_high','BreakEvenHigh','queries'),('nonamortizing_builds','Nonamortizing','count')]:
            add('WZero'+name+suffix,row[field],path,{'dataset':row['dataset']},field,unit,'Model-derived query executions with fixed profile amortization; not query sets; source-truth provenance/cost and fresh-query reuse need resolution.', 'CONDITIONAL_MODEL_OUTPUT')

    build_costs=table(P+'lifecycle_cost/per_target_build.csv')
    path=P+'lifecycle_cost/horizon_summary.csv'
    for row in table(path):
        if int(row['N'])!=1000000:
            continue
        subset=[r for r in build_costs if r['dataset']==row['dataset']]
        recomputed=sum(1e6*float(r['serving_saving_per_query'])-float(r['total_incremental_distance_evals']) for r in subset)/len(subset)
        assert math.isclose(recomputed,float(row['net_distance_saving']),rel_tol=1e-12)
        name='Sift' if row['dataset']=='sift100k' else 'Arxiv'
        add('WZero'+name+'NetSavingMillion',row['net_distance_saving'],path,{'dataset':row['dataset'],'N':'1000000'},'net_distance_saving','distance_evaluations','Dataset mean per-target modeled saving, not sum over targets; lifecycle scope conditional.','CONDITIONAL_MODEL_OUTPUT')

    # Preserve exact code/protocol versions needed to interpret the tables.
    for file in ['analyze_phase2_refresh95.py','analyze_loop2_lifecycle_cost.py','analyze_phase3_vamana_unified.py','analyze_phase4_deep1m.py']:
        read('scripts/graph_anns_phase3_ea85/'+file)
    for file in ['p2_refresh95_decision.json','p3_vamana_unified_decision.json','p4_deep1m_decision.json','loop2_lifecycle_cost_decision.json']:
        read('manifests/graph_anns_phase3_ea85/'+file)
    read('results/graph_anns_phase2_p7/ICBA_ICLR_Anonymous_Revised_v12_final.tex')
    read('paper/theory.tex')
    ledger = dict(base_commit=BASE, status='NUMERIC_FREEZE_WITH_EXPLICIT_CLAIM_HOLDS',
                  scope='Committed summary/per-build/code audit, not raw-query replay or independent scientific review.',
                  input_sha256=inputs, numbers=numbers)
    tex=['% Generated by freeze_w0.py from committed evidence.', '% Percent macros contain numeric percentages; append \\%. Increment is percentage points.']
    for number in numbers:
        tex.append('% '+number['status']+' | '+number['unit'])
        tex.append('\\newcommand{\\'+number['macro']+'}{'+number['display']+'}')
    return {'evidence_ledger.json':json.dumps(ledger,indent=2,ensure_ascii=False)+'\n',
            'results_macros.tex':'\n'.join(tex)+'\n'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,default=Path.cwd())
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    out=args.repo/'paper/sigmod2027/evidence'
    payload=assemble(args.repo)
    if args.check:
        for name,text in payload.items():
            assert (out/name).read_text(encoding='utf-8')==text, name
    else:
        out.mkdir(parents=True,exist_ok=True)
        for name,text in payload.items():
            (out/name).write_text(text,encoding='utf-8')
    print('W0 evidence consistency: PASS; '+str(len(json.loads(payload['evidence_ledger.json'])['numbers']))+' numbers; claim holds remain explicit.')


if __name__=='__main__':
    main()
