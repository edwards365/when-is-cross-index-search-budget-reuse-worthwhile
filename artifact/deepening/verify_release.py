"""Verify fixed release assets and safely extract the saved-response bundle."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, subprocess, zipfile


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--assets', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    a = ap.parse_args()
    record = json.loads((a.assets / 'release-manifest.json').read_text(encoding='utf-8'))
    pinned = json.loads((Path(__file__).parent / 'release-manifest.json').read_text(encoding='utf-8'))
    if record != pinned:
        raise RuntimeError('Release manifest differs from fixed Git checkout')
    for name, data in record['assets'].items():
        if sha(a.assets / name) != data['sha256']:
            raise RuntimeError('Release asset checksum mismatch: ' + name)
    if a.output.exists():
        raise RuntimeError('Use a new extraction directory')
    with zipfile.ZipFile(a.assets / 'ICDE_P0-P11_artifact.zip') as z:
        for name in z.namelist():
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name:
                raise RuntimeError('Unsafe archive member')
        if z.testzip() is not None:
            raise RuntimeError('Corrupt ZIP')
        z.extractall(a.output)
    binding = json.loads((a.output / 'PAPER_BINDING.json').read_text(encoding='utf-8'))
    if binding['assets'] != {n: d['sha256'] for n, d in record['assets'].items() if n != 'ICDE_P0-P11_artifact.zip'}:
        raise RuntimeError('Paper-to-artifact binding mismatch')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    result = {'status': 'PASS', 'release_tag': record['release_tag'], 'entry_commit': commit,
              'assets': record['assets'], 'paper_binding': binding}
    (a.assets / 'ASSET_VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Release assets, fixed Git manifest, and paper binding PASS')


if __name__ == '__main__':
    main()
