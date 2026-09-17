"""Regenerate W5 display values from frozen W0 inputs; no experiment execution."""
import csv
import hashlib
import io
import json
from pathlib import Path
import argparse
import subprocess

ROOT = Path(__file__).resolve().parent
BASE = 'd0ceb9bafa12480d04d4ae473b4c669e0e5b6ff5'
ORIGINAL = 'results/graph_anns_phase3_ea85/refresh95/'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--repo', type=Path)
    args = ap.parse_args()
    inputs = {}
    tables = {}
    for short in ('summary', 'per_build'):
        blob = (ROOT / f'refresh95_{short}.csv').read_bytes()
        if args.repo:
            committed = subprocess.check_output(['git', 'show', f'{BASE}:{ORIGINAL}{short}.csv'], cwd=args.repo)
            assert blob.replace(b'\r\n', b'\n') == committed.replace(b'\r\n', b'\n')
        inputs[f'refresh95_{short}.csv'] = hashlib.sha256(blob).hexdigest()
        tables[short] = list(csv.DictReader(io.StringIO(blob.decode())))
    values = []
    lines = ['% Generated from unchanged W0 summary rows; no new experimental data.']
    def add(name, row, column, percent=False):
        val = float(row[column]) * (100 if percent else 1)
        display = f'{val:.2f}'
        lines.append('\\newcommand{\\'+name+'}{'+display+'}')
        values.append(dict(macro=name, display=display, dataset=row['dataset'],
                           method=row['method'], column=column, multiplier=100 if percent else 1))
    for ds, prefix in [('sift100k','Sift'), ('arxiv_nomic_100k','Arxiv')]:
        rows = [r for r in tables['summary'] if r['dataset']==ds]
        def one(method):
            found = [r for r in rows if r['method']==method]
            assert len(found)==1
            return found[0]
        end = one('FIXED_SAFE_NATIVE_ENDPOINT')
        tar = one('TARGET_SELECTION_TCP_RECALIBRATION')
        add('WFive'+prefix+'EndpointRisk',end,'evaluation_risk',True)
        add('WFive'+prefix+'EndpointPninetyNine',end,'p99_dists')
        add('WFive'+prefix+'TargetPninetyNine',tar,'p99_dists')
        add('WFive'+prefix+'Loto',tar,'min_lobo_gain',True)
        add('WFive'+prefix+'DeleteLargest',tar,'delete_largest_gain',True)
        for row in rows:
            sub=[r for r in tables['per_build'] if r['dataset']==ds and r['method']==row['method']]
            assert len(sub)==10
            risk=sum(int(r['evaluation_failures']) for r in sub)/sum(int(r['evaluation_n']) for r in sub)
            assert abs(risk-float(row['evaluation_risk']))<1e-12
            assert sum(int(r['fallback']) for r in sub)==int(row['fallback_builds'])
        end_by_seed={r['seed']:r for r in tables['per_build'] if r['dataset']==ds and r['method']==end['method']}
        target=[r for r in tables['per_build'] if r['dataset']==ds and r['method']==tar['method']]
        assert sum(int(r['fallback'])==0 and int(r['certified_deployment'])==1 for r in target)==(10 if prefix=='Sift' else 9)
        for r in target:
            if int(r['fallback']):
                for col in ['evaluation_risk','mean_dists','p95_dists','p99_dists']:
                    assert float(r[col])==float(end_by_seed[r['seed']][col])
                assert float(end_by_seed[r['seed']]['cert_ucb'])<=.05
    tex='\n'.join(lines)+'\n'
    ledger=dict(source_baseline=BASE,original_directory=ORIGINAL,input_sha256=inputs,values=values,
                scope='Formatting and exact extraction from frozen summaries; not new inference or experiment.')
    outputs={'w5_macros.tex':tex,'w5_number_ledger.json':json.dumps(ledger,indent=2)+'\n'}
    for name, content in outputs.items():
        path=ROOT/name
        if args.write:
            path.write_text(content,encoding='utf-8')
        else:
            assert path.read_text(encoding='utf-8')==content, name
    print('PASS: 10 W5 values, 80 per-build risk/fallback rows, 19 candidate acceptances, fallback endpoint equality.')

if __name__=='__main__':
    main()
