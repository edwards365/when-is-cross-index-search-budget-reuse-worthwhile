"""Read-only saved-output identity/arithmetic check. No ANN or bootstrap runs."""
from pathlib import Path
import csv
import hashlib
import json
import math
from statistics import mean

ROOT = Path(__file__).resolve().parent

def require(condition, message):
    if not condition:
        raise ValueError(message)

def rows(name):
    with (ROOT / 'data/summary_information_bridge' / name).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def near(actual, expected, tolerance=.011):
    require(math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance),
            f'Value mismatch: {actual} versus {expected}')

def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    for name, pin in manifest['files'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT.resolve()), 'Manifest path escapes artifact')
        data = path.read_bytes()
        require(len(data) == pin['bytes'] and hashlib.sha256(data).hexdigest() == pin['sha256'],
                'File identity mismatch: ' + name)
    final_data = (ROOT / 'receipts/analysis_final.json').read_bytes()
    final = json.loads(final_data)
    separate = json.loads((ROOT / 'receipts/analysis_check.json').read_bytes())
    require(separate['analysis_final_sha256'] == hashlib.sha256(final_data).hexdigest(), 'Receipt pairing mismatch')
    for path in (ROOT / 'data/summary_information_bridge').glob('*.csv'):
        require(hashlib.sha256(path.read_bytes()).hexdigest() == final['outputs'][path.name]['sha256'],
                'Historical output mismatch: ' + path.name)
    obj, cov = rows('objectives.csv'), rows('coverage.csv')
    require(len(obj) == 640 and len(cov) == 320, 'Row count mismatch')
    report = {}
    for ds, expected, singleton, retained in [
        ('sift-1m-heldout', [1549.64, 1710.29, 4906.70, 5172.91], 51.09, 99.10),
        ('arxiv-nomic-1.34m-heldout', [957.37, 1106.47, 2329.06, 2614.02], 37.93, 99.80),
    ]:
        def select(summary):
            return [r for r in obj if r['dataset'] == ds and r['summary'] == summary
                    and r['subset'] == 'endpoint_solvable' and r['criterion'] == 'stable_tail']
        v, m = select('vector'), select('max')
        require(len(v) == len(m) == 8, 'Target count mismatch')
        require({r['target'] for r in v} == {r['target'] for r in m}, 'Targets mismatch')
        values = [mean(float(r[k]) for r in rr) for rr, k in
                  [(v, 'J_identity'), (v, 'J_summary'), (m, 'J_summary'), (m, 'J_order')]]
        for got, want in zip(values, expected):
            near(got, want)
        vb = {r['target']: r for r in v}
        require(all(float(r['J_summary']) > float(vb[r['target']]['J_summary']) for r in m), 'Compression sign mismatch')
        require(all(r['n_query'] == vb[r['target']]['n_query'] for r in m), 'Subset size mismatch')
        cc = [r for r in cov if r['dataset'] == ds and r['summary'] == 'vector' and r['subset'] == 'endpoint_solvable']
        near(mean(100 * int(r['singleton_query_n']) / int(r['n_query']) for r in cc), singleton)
        near(mean(100 * (1 - float(r['excluded_fraction'])) for r in cc), retained)
        report[ds] = {'optimal_ndc': values, 'compression_positive_targets': 8,
                      'order_positive_targets': sum(float(r['order_gap']) > 1e-9 for r in m)}
    require(len(rows('qualification_sensitivity.csv')) == 320, 'Sensitivity rows mismatch')
    for ds, expected in [('sift-1m-heldout', 211.622), ('arxiv-nomic-1.34m-heldout', 574.531)]:
        rr = [r for r in rows('fixed_cost_components.csv') if r['dataset'] == ds]
        total = next(float(r['seconds']) for r in rr if r['component'] == 'fixed_net_setup_total')
        near(sum(float(r['seconds']) for r in rr if r['component'] != 'fixed_net_setup_total'), total, 1e-9)
        near(total, expected, .001)
    print(json.dumps({'status': 'PASS_SAVED_OUTPUT_CONSISTENCY', 'results': report,
                      'scope': 'File identity and selected CSV arithmetic only; no original measurement, raw-array, ANN or bootstrap verification'}, indent=2))

if __name__ == '__main__':
    main()
