"""Portable saved-response analysis. Never runs ANN, old launchers or bootstrap."""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys
import zipfile

# Set before NumPy/SciPy import. This small analysis does not need a BLAS thread pool.
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
ROOT = Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def need(value, message):
    if not value:
        raise ValueError(message)

def validate(archive, manifest):
    data = archive.read_bytes()
    need(len(data) == manifest['archive']['bytes'] and sha(data) == manifest['archive']['sha256'], 'Archive hash/size mismatch')
    with zipfile.ZipFile(archive) as z:
        need(set(z.namelist()) == set(manifest['files']) and len(z.namelist()) == len(manifest['files']), 'Unexpected archive members')
        for name, pin in manifest['files'].items():
            need(Path(name).name == name and not Path(name).is_absolute(), 'Unsafe member name')
            data = z.read(name)
            need(len(data) == pin['bytes'] and sha(data) == pin['sha256'], 'Input mismatch: ' + name)

def compare(actual, expected):
    with actual.open(encoding='utf-8-sig', newline='') as a, expected.open(encoding='utf-8-sig', newline='') as e:
        ar, er = csv.DictReader(a), csv.DictReader(e)
        need(ar.fieldnames == er.fieldnames, 'Header mismatch: ' + actual.name)
        aa, ee = list(ar), list(er)
    need(len(aa) == len(ee), 'Row count mismatch: ' + actual.name)
    numeric_cells = 0
    for i,(a,e) in enumerate(zip(aa,ee)):
        for key in a:
            if a[key] == e[key]:
                continue
            try:
                x,y = float(a[key]),float(e[key])
            except (ValueError,TypeError):
                raise ValueError(f'{actual.name} row {i} field {key}: text/status differs')
            need(math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-9),
                 f'{actual.name} row {i} field {key}: numerical mismatch')
            numeric_cells += 1
    return {'rows':len(aa),'within_tolerance_nonidentical_cells':numeric_cells,
            'rel_tol':1e-10,'abs_tol':1e-9,'byte_identical':actual.read_bytes()==expected.read_bytes()}

def main():
    need(__debug__, 'Run without -O: the numerical reference uses assertion checks')
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive',type=Path,required=True)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--check-inputs',action='store_true',help='Hash and archive checks only, no analysis/dependencies')
    args=ap.parse_args()
    manifest=json.loads((ROOT/'input_manifest.json').read_text(encoding='utf-8'))
    validate(args.archive,manifest)
    if args.check_inputs:
        print('PASS_INPUT_ARCHIVE_AND_MEMBER_HASHES'); return
    need(args.output is not None,'--output is required for analysis')
    out=args.output.resolve()
    need(not out.exists(),'Output already exists; choose a new directory')
    need(not out.is_relative_to(ROOT),'Output must be outside the artifact source directory')
    import numpy as np
    import scipy
    spec=importlib.util.spec_from_file_location('summary_analysis',ROOT/'reference/summary_analysis.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    out.mkdir(parents=True)
    inputs=out/'inputs'; inputs.mkdir()
    with zipfile.ZipFile(args.archive) as z:
        z.extractall(inputs)  # Names were checked against the pinned basename-only manifest.
    paths={k:str(inputs/v) for k,v in manifest['paths'].items()}
    audit=json.loads(Path(paths['profile_audit']).read_text(encoding='utf-8'))
    # All supplied role arrays remain byte-identical; resolve paths only in a new JSON view.
    for row in audit['rows']:
        row['array_path']=str(inputs/Path(row['array_path']).name)
    view=out/'resolved_audit.json'
    view.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    paths['profile_audit']=str(view)
    conf={'paths':paths,'inputs':{str(inputs/k):v for k,v in manifest['files'].items()}}
    derived=out/'derived'; derived.mkdir()
    try:
        result=module.run(conf,derived)
        expected=ROOT/'data/summary_information_bridge'
        need({p.name for p in derived.glob('*.csv')}=={p.name for p in expected.glob('*.csv')},'Output set differs')
        comparisons={p.name:compare(p,expected/p.name) for p in sorted(derived.glob('*.csv'))}
        report={'status':'PASS_SAVED_RESPONSE_REPRODUCTION','python':platform.python_version(),
                'numpy':np.__version__,'scipy':scipy.__version__,'comparisons':comparisons,
                'new_ann_runs':0,'new_bootstrap_runs':0,
                'scope':'Regenerated selected derived tables from archived responses; not independent original measurements or full-paper reproduction'}
        (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,indent=2))
    except Exception as error:
        (out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'message':str(error)})+'\n',encoding='utf-8')
        raise

if __name__=='__main__':
    main()
