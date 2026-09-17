"""Non-mutating PDF/layout checks, plus generated QA reports and page previews."""
from pathlib import Path
import json,re
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parent
reports={}
for name in ['main','appendix']:
    path=ROOT/'build'/f'{name}.pdf'
    reader=PdfReader(path)
    text='\n'.join(p.extract_text() or '' for p in reader.pages)
    assert all(abs(float(p.mediabox.width)-612)<.1 and abs(float(p.mediabox.height)-792)<.1 for p in reader.pages)
    assert path.stat().st_size<10*1024*1024
    forbidden=['wanglekang','edwards365','101.6.160.66','/home/wlk','C:\\Users\\','navigation-aware-resistance-hnsw.git']
    metadata={str(k):str(v) for k,v in (reader.metadata or {}).items()}
    assert not any(s.lower() in (text+str(metadata)).lower() for s in forbidden)
    assert metadata.get('/Author','') in ['', 'Anonymous Author(s)']
    assert '??' not in text
    log=(ROOT/'build'/f'{name}.log').read_text(encoding='utf-8',errors='replace')
    bad=[line for line in log.splitlines() if re.search(r'Overfull|undefined references|Citation .* undefined|Missing character',line)]
    assert not bad,bad
    font_names=set();unembedded=[]
    for p in reader.pages:
        fonts=p['/Resources'].get('/Font',{})
        for _,v in fonts.items():
            f=v.get_object();font_names.add(str(f.get('/BaseFont','')))
            children=f.get('/DescendantFonts',[f])
            for item in children:
                ff=item.get_object();desc=ff.get('/FontDescriptor')
                if desc:
                    desc=desc.get_object()
                    if not any(k in desc for k in ['/FontFile','/FontFile2','/FontFile3']):
                        unembedded.append(str(ff.get('/BaseFont')))
    assert not unembedded,unembedded
    refs=[i+1 for i,p in enumerate(reader.pages) if re.search(r'\bReferences\b',p.extract_text() or '')]
    reports[name]={'pages':len(reader.pages),'bytes':path.stat().st_size,'letter':True,'metadata':metadata,'references_heading_pages':refs,'font_count':len(font_names),'all_inspected_fonts_embedded':True,'no_identifying_paths_or_author':True,'no_overfull_missing_glyph_or_unresolved_reference':True}
    doc=pdfium.PdfDocument(str(path))
    for i,p in enumerate(doc):
        p.render(scale=1.5).to_pil().save(ROOT/'build'/f'final_{name}_{i+1}.png')
(ROOT/'build'/'delivery_qa.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
print(json.dumps(reports,indent=2))
