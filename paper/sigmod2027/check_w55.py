"""Read-only structural/numeric/PDF checks; optional page rendering for visual QA."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pdf',type=Path,default=ROOT/'build/main.pdf')
    ap.add_argument('--render',action='store_true')
    args=ap.parse_args()
    subprocess.run([sys.executable,str(ROOT/'evidence/check_w5_numbers.py')],check=True)
    maintex=(ROOT/'main.tex').read_text(encoding='utf-8')
    active=[ROOT/(p+'.tex') for p in re.findall(r'\\input\{([^}]+)\}',maintex)]
    text=maintex+'\n'+'\n'.join(p.read_text(encoding='utf-8') for p in active)
    assert r'\documentclass[sigconf,anonymous,nonacm]{acmart}' in maintex
    assert '[Experiments \\& Analysis]' in maintex
    for rq in range(1,10):
        assert f'RQ{rq}:' in text
    assert text.count('\\begin{figure*}')==3
    assert text.count('\\begin{table}')==6  # Five numbered tables + unnumbered glossary.
    assert text.count('\\caption*')==1
    assert 'Index-Conditioned Budget Audit (ICBA)' in maintex
    assert 'Tiered Conformal Pooling (TCP)' in maintex
    assert 'unresolved endpoint' not in text
    assert text.count('[95\\% interval]')>=5
    assert text.count('\\begin{proposition}')==4
    assert text.count('\\begin{proof}')==4
    for forbidden in ['W4 writing draft','Planned exhibit','Writing Completion Map','sectionaim','placeholder']:
        assert forbidden not in text, forbidden
    keys=set(re.findall(r'@\w+\{([^,]+),',(ROOT/'references.bib').read_text()))
    used=set(k for group in re.findall(r'\\cite\w*\{([^}]+)\}',text) for k in group.split(','))
    assert used==keys, (keys-used,used-keys)
    labels=re.findall(r'\\label\{([^}]+)\}',text)
    assert len(labels)==len(set(labels))
    refs=set(re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',text))
    assert refs<=set(labels),refs-set(labels)
    defined=set(re.findall(r'\\newcommand\{\\(W(?:Zero|Five)\w+)\}',text))
    requested=set(re.findall(r'\\(W(?:Zero|Five)\w+)',text))
    assert requested<=defined
    ledger=json.loads((ROOT/'evidence/evidence_ledger.json').read_text())
    frozen=dict(re.findall(r'\\newcommand\{\\(WZero\w+)\}\{([^}]+)\}',text))
    assert len(ledger['numbers'])==57
    for row in ledger['numbers']:
        assert frozen[row['macro']]==row['display'],row['macro']
    import csv
    buildrows=list(csv.DictReader((ROOT/'evidence/refresh95_per_build.csv').open()))
    diag=json.loads((ROOT/'evidence/w55_diagnostics.json').read_text())
    newmacros=dict(re.findall(r'\\newcommand\{\\(WFiftyFive\w+)\}\{([^}]+)\}',text))
    for ds,prefix in [('sift100k','Sift'),('arxiv_nomic_100k','Arxiv')]:
        source=[r for r in buildrows if r['dataset']==ds and r['method']=='SOURCE_TCP_POOL_REUSE']
        target=[r for r in buildrows if r['dataset']==ds and r['method']=='TARGET_SELECTION_TCP_RECALIBRATION']
        f=[int(r['evaluation_failures']) for r in source]
        assert len(f)==10 and all(int(r['evaluation_n'])==1000 for r in source)
        assert all(x>50 for x in f)
        assert all(int(r['certified_deployment'])==1 and float(r['evaluation_risk'])<.05 for r in target)
        vals={'MinRisk':min(f)/10,'MaxRisk':max(f)/10,'MaxShare':100*max(f)/sum(f),'DeleteRisk':100*(sum(f)-max(f))/9000}
        for suffix,value in vals.items():assert newmacros['WFiftyFive'+prefix+suffix]==f'{value:.2f}'
        assert diag['datasets'][ds]['fallback_seeds']==[int(r['seed']) for r in target if int(r['fallback'])]
        end={r['seed']:float(r['mean_dists']) for r in buildrows if r['dataset']==ds and r['method']=='FIXED_SAFE_NATIVE_ENDPOINT'}
        tar={r['seed']:float(r['mean_dists']) for r in target}
        loto={s:1-sum(v for k,v in tar.items() if k!=s)/sum(v for k,v in end.items() if k!=s) for s in end}
        assert max(end,key=lambda s:1-tar[s]/end[s])==min(loto,key=loto.get)
    reader=PdfReader(args.pdf)
    pages=[p.extract_text() or '' for p in reader.pages]
    reference_pages=[i+1 for i,t in enumerate(pages) if re.search(r'(?m)^References\s*$',t)]
    assert len(reference_pages)==1,reference_pages
    # References may start on the same page as the conclusion: count that page.
    content_pages=reference_pages[0]
    assert content_pages<=12
    assert args.pdf.stat().st_size<=10_000_000
    assert all(abs(float(p.mediabox.width)-612)<1 and abs(float(p.mediabox.height)-792)<1 for p in reader.pages)
    alltext='\n'.join(pages)
    assert '??' not in alltext
    for leak in ['wanglekang','edwards365','/home/wlk','101.6.160.66','C:\\Users']:
        assert leak.lower() not in (alltext+str(reader.metadata)).lower(),leak
    fonts={}
    uris=set()
    for page in reader.pages:
        for ref in page.get('/Resources',{}).get('/Font',{}).values():
            font=ref.get_object()
            nested=font.get('/DescendantFonts',[font])
            for x in nested:
                f=x.get_object()
                fd=f.get('/FontDescriptor')
                embedded=bool(fd and any(k in fd.get_object() for k in ('/FontFile','/FontFile2','/FontFile3')))
                fonts[str(f.get('/BaseFont'))]=embedded
        for ref in page.get('/Annots',[]):
            action=ref.get_object().get('/A')
            if action and action.get('/URI'):
                uris.add(str(action['/URI']))
    # Embedded figure PDFs are Form XObjects with their own font resources.
    def font_resources(resources):
        for ref in resources.get('/Font',{}).values():
            f=ref.get_object()
            for nested in f.get('/DescendantFonts',[f]):
                ff=nested.get_object();fd=ff.get('/FontDescriptor')
                fonts[str(ff.get('/BaseFont'))]=bool(fd and any(k in fd.get_object() for k in ('/FontFile','/FontFile2','/FontFile3')))
        for ref in resources.get('/XObject',{}).values():
            x=ref.get_object()
            if x.get('/Resources'):font_resources(x['/Resources'])
    for page in reader.pages:font_resources(page['/Resources'])
    assert all(fonts.values()),fonts
    assert 'TimesNewRoman' in str(fonts)
    for name in ['overview','workflow','target_decisions']:
        for ext in ['pdf','svg','png']:
            assert (ROOT/'figures'/f'{name}.{ext}').is_file()
    assert all(f'Figure {i}:' in alltext for i in range(1,4))
    assert all(f'Table {i}:' in alltext for i in range(1,6))
    assert 'Table 6:' not in alltext
    assert 'Terms at a glance' in alltext
    assert not re.search(r'ICBA[A-Za-z]|TCP[a-z]',alltext)
    assert 'ICBA..' not in alltext and 'unresolved endpoint' not in alltext
    assert not any('edwards365' in u or 'example.com' in u for u in uris)
    print(json.dumps(dict(status='PASS_STRUCTURAL_NOT_SCIENTIFIC_CERTIFICATION',
        total_pages=len(pages),content_pages_inclusive=content_pages,
        references_start_page=reference_pages[0],bytes=args.pdf.stat().st_size,
        pdf_sha256=hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
        paper_size='Letter 612x792 pt',references=len(keys),tables=5,glossary=1,figures=3,
        propositions=4,metadata=dict(reader.metadata or {}),fonts=fonts,external_links=sorted(uris)),indent=2))
    if args.render:
        import pypdfium2 as pdfium
        from PIL import Image,ImageOps,ImageDraw
        pdf=pdfium.PdfDocument(args.pdf)
        tiles=[]
        for i,page in enumerate(pdf):
            img=page.render(scale=1.5).to_pil().convert('RGB')
            img.save(ROOT/'build'/f'w55_page_{i+1:02}.png')
            thumb=img.copy();thumb.thumbnail((459,594))
            tile=Image.new('RGB',(479,620),'#dddddd');tile.paste(thumb,(10,20))
            ImageDraw.Draw(tile).text((10,3),str(i+1),fill='black');tiles.append(tile)
        sheet=Image.new('RGB',(479*3,620*((len(tiles)+2)//3)),'white')
        for i,tile in enumerate(tiles):sheet.paste(tile,((i%3)*479,(i//3)*620))
        sheet.save(ROOT/'build/w55_contact.png')

if __name__=='__main__':main()
