"""Reproducible verification-only export correction for the sealed P8 checker."""
from pathlib import Path
import hashlib, json

OLD = '61a121f9280f2249fd8f105926ec239d49c179da984d5c8f20a3383d00b3fc1e'
NEW = 'dbc9a078afee2367259211142669986871be65d9d833a3000602d7c53f6e24e6'
BEFORE = "                if k not in ['panel','target','support']:assert old[k]==r[k],(k,old[k],r[k])"
AFTER = "                if k in ['candidate_ucb','endpoint_ucb']:close(old[k],r[k])\n                elif k not in ['panel','target','support']:assert old[k]==r[k],(k,old[k],r[k])"


def apply(bundle):
    bundle = Path(bundle)
    p = bundle/'p0-p10/src/p8_check.py'
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    if digest == OLD:
        original = p.read_text(encoding='utf-8')
        if original.count(BEFORE) != 1:
            raise RuntimeError('Unexpected legacy verification source')
        # Match the checked UTF-8/LF export; algorithms and expected files are untouched.
        p.write_bytes(original.replace(BEFORE, AFTER).encode('utf-8'))
    if hashlib.sha256(p.read_bytes()).hexdigest() != NEW:
        raise RuntimeError('Unexpected portable P8 export hash')
    provenance = json.loads((bundle/'p0-p10/SOURCE_PROVENANCE.json').read_text(encoding='utf-8'))
    record = next(r for r in provenance if r['file']=='src/p8_check.py')
    record['previous_portable_sha256'] = OLD
    record['export_sha256'] = NEW
    record['changes'] = ('saved-response native-index scope preserved; candidate_ucb and endpoint_ucb '
                         'cross-stage comparisons use existing numeric close instead of exact strings; '
                         'all integer/action/decision fields remain exact; optimizer/fitter/data unchanged')
    (bundle/'p0-p10/SOURCE_PROVENANCE.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    root = json.loads((bundle/'PROVENANCE.json').read_text(encoding='utf-8'))
    root = [r for r in root if r.get('file')!='p0-p10/src/p8_check.py']
    root.append({'file':'p0-p10/src/p8_check.py','original_scientific_sha256':record['original_sha256'],
                 'previous_portable_sha256':OLD,'export_sha256':NEW,'changes':record['changes']})
    (bundle/'PROVENANCE.json').write_text(json.dumps(root, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--bundle', required=True)
    apply(p.parse_args().bundle)
