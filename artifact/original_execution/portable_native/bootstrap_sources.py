"""Fetch pinned public source archives only; never compile or execute science."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--download-public-sources',action='store_true');a=p.parse_args()
    if not a.download_public_sources:p.error('Explicit source-download opt-in required')
    c=json.loads((HERE/'config.json').read_text());d=c['diskann'];l=c['darth']['cpp_lightgbm_source']
    for name,url,pin in [('diskann-source.tar.gz',d['url'],d['archive_sha256']),('lightgbm-source.tar.gz',l['url'],l['sha256'])]:
        dest=HERE/name
        if dest.exists():
            if hashlib.sha256(dest.read_bytes()).hexdigest()!=pin:raise ValueError('Preserve differing existing archive: '+name)
            continue
        with urllib.request.urlopen(url,timeout=60) as r:data=r.read(64<<20)
        if hashlib.sha256(data).hexdigest()!=pin:raise ValueError('Downloaded archive identity: '+name)
        with dest.open('xb') as f:f.write(data)
    print(json.dumps({'public_sources':'READY','scientific_runs':0}))
if __name__=='__main__':main()
