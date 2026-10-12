"""Verify/extract the immutable P12 review payload; no experiment on import."""
import argparse,hashlib,json,zipfile
from pathlib import Path,PurePosixPath

EXPECTED='0ddfae6978c8876edd272940a5ce5de7339b0bd2e4a4d8b43ad361aed8d86c0f'
def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--verify-only',action='store_true');g.add_argument('--extract',type=Path)
    a=p.parse_args();assert hashlib.sha256(a.package.read_bytes()).hexdigest()==EXPECTED,'package identity'
    with zipfile.ZipFile(a.package) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('MANIFEST.json'))
        assert len(z.namelist())==len(set(z.namelist()))==len(manifest)+1
        assert set(z.namelist())==set(manifest)|{'MANIFEST.json'}
        for name,digest in manifest.items():
            assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts and '\\' not in name and ':' not in name
            assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
        if a.extract:
            a.extract.mkdir(parents=True,exist_ok=False);z.extractall(a.extract)
    print('P12_PAYLOAD_VERIFIED')
if __name__=='__main__':main()
