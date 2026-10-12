"""Reconstruct the released P0--P11 saved responses with independent checks."""
from pathlib import Path
import argparse, csv, hashlib, json, math, os, re, shutil, subprocess, sys, time


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify_manifest(bundle):
    expected = json.loads((bundle / 'MANIFEST.json').read_text(encoding='utf-8'))
    actual = {p.relative_to(bundle).as_posix(): digest(p) for p in bundle.rglob('*')
              if p.is_file() and p.relative_to(bundle).as_posix() != 'MANIFEST.json' and '__pycache__' not in p.parts}
    if actual != expected:
        raise RuntimeError('Payload file set or SHA256 mismatch')
    return len(expected)


def compare(x, y, location, differences):
    if type(x) is type(y) and x == y:
        return
    if isinstance(x, dict) and isinstance(y, dict):
        if x.keys() != y.keys():
            raise AssertionError(('JSON fields', location))
        for k in x:
            compare(x[k], y[k], location + '/' + k, differences)
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            raise AssertionError(('row count', location))
        for i, (a, b) in enumerate(zip(x, y)):
            compare(a, b, location + '/' + str(i), differences)
    else:
        if isinstance(x, bool) or isinstance(y, bool) or x is None or y is None:
            raise AssertionError(('exact category', location, x, y))
        if isinstance(x, str) and isinstance(y, str):
            if re.fullmatch(r'-?\d+', x) and re.fullmatch(r'-?\d+', y):
                if int(x) != int(y):
                    raise AssertionError(('integer', location, x, y))
                return
            try:
                a, b = float(x), float(y)
            except ValueError:
                raise AssertionError(('exact text', location, x, y))
        elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
            if isinstance(x, int) and isinstance(y, int):
                raise AssertionError(('integer', location, x, y))
            a, b = float(x), float(y)
        else:
            raise AssertionError(('type', location, type(x).__name__, type(y).__name__))
        if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-9):
            raise AssertionError(('number', location, x, y))
        differences.append({'field': location, 'absolute_difference': abs(a-b)})


def verify_p11(expected, actual):
    names = sorted(p.name for p in expected.iterdir() if p.is_file())
    if names != sorted(p.name for p in actual.iterdir() if p.is_file()):
        raise AssertionError('P11 output file set mismatch')
    exact, differences = [], []
    for name in names:
        a, b = actual / name, expected / name
        if digest(a) == digest(b):
            exact.append(name)
            continue
        if a.suffix == '.csv':
            with a.open(encoding='utf-8', newline='') as f:
                x = list(csv.DictReader(f))
            with b.open(encoding='utf-8', newline='') as f:
                y = list(csv.DictReader(f))
        elif a.suffix == '.json':
            x, y = (json.loads(p.read_text(encoding='utf-8')) for p in (a, b))
        else:
            raise AssertionError(('unhandled differing file', name))
        compare(x, y, name, differences)
    for name in ('cost_check.json', 'learning_check.json'):
        if json.loads((actual / name).read_text(encoding='utf-8'))['status'] != 'PASS':
            raise AssertionError(('independent checker', name))
    return {'files_checked': len(names), 'byte_identical_files': exact,
            'floating_point_differences': differences, 'status': 'PASS'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle', required=True, type=Path)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--verify-only', action='store_true')
    a = ap.parse_args()
    bundle = a.bundle.resolve()
    count = verify_manifest(bundle)
    if a.verify_only:
        print(json.dumps({'status': 'PASS', 'manifest_files': count}))
        return
    if a.output is None:
        ap.error('--output is required for reconstruction')
    out = a.output.resolve()
    if out.exists() or out == bundle or bundle in out.parents:
        raise RuntimeError('Use a new output directory outside the extracted bundle')
    import psutil
    if psutil.virtual_memory().available < 5 * 1024**3:
        raise RuntimeError('At least 5 GiB available RAM required')
    if shutil.disk_usage(out.parent).free < 10 * 1024**3:
        raise RuntimeError('At least 10 GiB free disk required')
    out.mkdir()
    logs = out / 'logs'
    logs.mkdir()
    env = os.environ.copy()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        env[key] = '1'
    env['PYTHONUTF8'], env['PYTHONNOUSERSITE'] = '1', '1'
    env.pop('PYTHONPATH', None)
    affinity = psutil.Process().cpu_affinity()
    psutil.Process().cpu_affinity([affinity[0]])
    receipt = {'status': 'RUNNING', 'manifest_files': count, 'stages': [],
               'scope': 'saved-response reconstruction and independent algorithms; no ANN, truth, timing or bootstrap rerun',
               'python': sys.version.split()[0], 'logical_cpus_used': 1,
               'minimum_available_GiB': psutil.virtual_memory().available / 1024**3,
               'maximum_sampled_rss_MiB': 0, 'seconds': 0}
    start = time.monotonic()
    tasks = [('p0-p10', [sys.executable, '-B', str(bundle / 'p0-p10/rebuild.py'), '--output', str(out / 'p0-p10')]),
             ('theory', [sys.executable, '-B', str(bundle / 'p0-p10/rebuild_theory.py'), '--output', str(out / 'theory')])]
    for phase in ('cost', 'cost_check', 'learning', 'learning_check'):
        tasks.append(('p11-' + phase, [sys.executable, '-B', str(bundle / 'p11/rebuild.py'), '--phase', phase, '--output', str(out / 'p11')]))
    try:
        for name, cmd in tasks:
            with (logs / (name + '.stdout')).open('x', encoding='utf-8') as so, (logs / (name + '.stderr')).open('x', encoding='utf-8') as se:
                p = subprocess.Popen(cmd, cwd=bundle, env=env, stdout=so, stderr=se)
                handle = psutil.Process(p.pid)
                while p.poll() is None:
                    available = psutil.virtual_memory().available / 1024**3
                    receipt['minimum_available_GiB'] = min(receipt['minimum_available_GiB'], available)
                    processes = [handle] + handle.children(recursive=True)
                    rss = 0
                    for process in processes:
                        try:
                            process.cpu_affinity([affinity[0]])
                            rss += process.memory_info().rss
                        except psutil.NoSuchProcess:
                            pass
                    receipt['maximum_sampled_rss_MiB'] = max(receipt['maximum_sampled_rss_MiB'], rss / 1024**2)
                    if available < 3 or rss > 2 * 1024**3 or time.monotonic() - start > 1800:
                        for process in reversed(processes):
                            try:
                                process.terminate()
                            except psutil.NoSuchProcess:
                                pass
                        p.wait(timeout=10)
                        raise RuntimeError('Resource or time gate reached; logs preserved')
                    time.sleep(0.5)
            receipt['stages'].append({'name': name, 'exit_code': p.returncode})
            if p.returncode:
                raise RuntimeError(name + ' failed; inspect its logs')
            print(name + ' PASS', flush=True)
        receipt['p0-p10'] = json.loads((out / 'p0-p10/REBUILD_COMPLETE.json').read_text())
        receipt['p11'] = verify_p11(bundle / 'p11/expected', out / 'p11')
        receipt['status'] = 'PASS'
    except BaseException as exc:
        receipt['status'], receipt['error'] = 'FAIL', str(exc)
        raise
    finally:
        receipt['seconds'] = time.monotonic() - start
        (out / 'VERIFICATION.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'report': 'VERIFICATION.json'}))


if __name__ == '__main__':
    main()
