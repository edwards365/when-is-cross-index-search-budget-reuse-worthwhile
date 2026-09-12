#!/usr/bin/env python
"""P7: build the revised ICLR-style anonymous paper DOCX via direct OOXML construction.

DEVIATION NOTE (recorded in docs/graph_anns_phase2_p7/phase_report.md): the docx skill's
primary path is docx-js (bun/node); this environment has no node/bun and no reachable npm
registry, and pip cannot reach PyPI for python-docx. The build therefore constructs the
OOXML package with the Python standard library while following the skill's formatting
standards (1.3x line spacing, real Heading styles, table cell margins, CLEAR shading,
aspect-preserving images, caption/keepNext rules, no decorative cover for an academic
paper template).
"""
import re
import struct
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ASSETS = REPO / "results/graph_anns_phase2_p7"
MEDIA = ASSETS / "media"
EQ = ASSETS / "eq"
OUT = ASSETS / "ICBA_ICLR_Anonymous_Revised_v2.docx"

EMU_PER_CM = 360000
CONTENT_W_CM = 15.92


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def png_size(path):
    with open(path, "rb") as f:
        f.seek(16)
        w, h = struct.unpack(">II", f.read(8))
    return w, h


def rpr(b=False, i=False, sz=20, font="Times New Roman", color=None, caps=False):
    x = '<w:rPr>'
    if b:
        x += "<w:b/>"
    if i:
        x += "<w:i/>"
    if caps:
        x += "<w:caps/>"
    x += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>'
    if color:
        x += f'<w:color w:val="{color}"/>'
    x += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>'
    return x


TOKEN = re.compile(r"(\*[^*]+\*)")


def runs(text, b=False, sz=20, i_all=False, font="Times New Roman", color=None):
    """Text with *italic* inline markup -> runs."""
    out = []
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append(f'<w:r>{rpr(b=b, i=True, sz=sz, font=font, color=color)}<w:t xml:space="preserve">{esc(part[1:-1])}</w:t></w:r>')
        else:
            out.append(f'<w:r>{rpr(b=b, i=i_all, sz=sz, font=font, color=color)}<w:t xml:space="preserve">{esc(part)}</w:t></w:r>')
    return "".join(out)


def para(text="", style=None, b=False, sz=20, align=None, space_after=120,
         space_before=0, i_all=False, keep_next=False, indent_first=0, color=None):
    ppr = "<w:pPr>"
    if keep_next:
        ppr += "<w:keepNext/>"
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if align:
        ppr += f'<w:jc w:val="{align}"/>'
    ppr += f'<w:spacing w:before="{space_before}" w:after="{space_after}" w:line="312" w:lineRule="auto"/>'
    if indent_first:
        ppr += f'<w:ind w:firstLine="{indent_first}"/>'
    ppr += "</w:pPr>"
    body = runs(text, b=b, sz=sz, i_all=i_all, color=color) if text else ""
    return f"<w:p>{ppr}{body}</w:p>"


def heading(level, text):
    style = f"Heading{level}"
    sz = {1: 24, 2: 22, 3: 20}[level]
    before = {1: 280, 2: 220, 3: 180}[level]
    return para(text, style=style, b=True, sz=sz, space_before=before, space_after=140,
                keep_next=True) + f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr></w:p>' \
        if False else para(text, style=style, b=True, sz=sz, space_before=before,
                           space_after=140, keep_next=True)


_imgid = [100]


def image(name, width_cm=14.5, caption=None):
    p = MEDIA / name
    w, h = png_size(p)
    emu_w = int(width_cm * EMU_PER_CM)
    emu_h = int(emu_w * h / w)
    _imgid[0] += 1
    rid = _imgid[0]
    IMG_RELS.append((rid, f"media/{name}"))
    d = (f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="60" w:line="240" w:lineRule="auto"/><w:keepNext/></w:pPr>'
         f'<w:r><w:rPr>{rpr(sz=18)}</w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
         f'<wp:extent cx="{emu_w}" cy="{emu_h}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
         f'<wp:docPr id="{rid}" name="{name}"/><wp:cNvGraphicFramePr>'
         f'<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
         f'</wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
         f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
         f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
         f'<pic:nvPicPr><pic:cNvPr id="{rid}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
         f'<pic:blipFill><a:blip r:embed="rId{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
         f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm>'
         f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
         f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
    cap = para(caption, style="Caption", space_after=200) if caption else ""
    return d + cap


def equation(n, width_cm=None):
    p = EQ / f"eq{n:02d}.png"
    w, h = png_size(p)
    wc = width_cm or min(13.5, 0.06 * w / 3.0)  # 300dpi -> cm
    emu_w = int(wc * EMU_PER_CM)
    emu_h = int(emu_w * h / w)
    _imgid[0] += 1
    rid = _imgid[0]
    IMG_RELS.append((rid, f"eq/eq{n:02d}.png"))
    return (f'<w:p><w:pPr><w:tabs><w:tab w:val="center" w:pos="4786"/>'
            f'<w:tab w:val="right" w:pos="9572"/></w:tabs>'
            f'<w:spacing w:before="80" w:after="80" w:line="240" w:lineRule="auto"/>'
            f'<w:jc w:val="left"/></w:pPr>'
            f'<w:r><w:tab/></w:r>'
            f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{emu_w}" cy="{emu_h}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
            f'<wp:docPr id="{rid}" name="eq{n}"/><wp:cNvGraphicFramePr>'
            f'<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
            f'</wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="{rid}" name="eq{n}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="rId{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
            f'<w:r><w:tab/><w:t>({n})</w:t></w:r></w:p>')


def cell(text, bold=False, header=False, sz=18, align="left", w_cm=None):
    shd = '<w:shd w:val="clear" w:color="auto" w:fill="E8E8E8"/>' if header else ""
    wm = (f'<w:tcW w:w="{int(w_cm*567)}" w:type="dithered"/>') if w_cm else '<w:tcW w:w="0" w:type="auto"/>'
    lines = text.split("\n")
    paras = "".join(
        para(ln, b=bold or header, sz=sz, align=align, space_after=40)
        for ln in lines)
    return (f'<w:tc><w:tcPr>{wm}<w:tcMar><w:top w:w="60" w:type="dithered"/>'
            f'<w:left w:w="100" w:type="dithered"/><w:bottom w:w="60" w:type="dithered"/>'
            f'<w:right w:w="100" w:type="dithered"/></w:tcMar>{shd}'
            f'<w:vAlign w:val="center"/></w:tcPr>{paras}</w:tc>')


def table(rows, widths=None, header=True, sz=18, caption=None, aligns=None):
    """rows: list of list of str. widths: cm list. First row header if header."""
    n = len(rows[0])
    widths = widths or [CONTENT_W_CM / n] * n
    aligns = aligns or (["left"] + ["center"] * (n - 1))
    tbl = ['<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/>'
           '<w:tblBorders>'
           '<w:top w:val="single" w:sz="12" w:color="404040"/>'
           '<w:bottom w:val="single" w:sz="12" w:color="404040"/>'
           '<w:insideH w:val="none"/><w:insideV w:val="none"/>'
           '<w:left w:val="none"/><w:right w:val="none"/>'
           '</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr>']
    hdr_border = '<w:tcBorders><w:bottom w:val="single" w:sz="6" w:color="808080"/></w:tcBorders>'
    for ri, row in enumerate(rows):
        tbl.append('<w:tr><w:trPr><w:cantSplit/>' +
                   ('<w:tblHeader/>' if header and ri == 0 else '') + '</w:trPr>')
        for ci, val in enumerate(row):
            c = cell(val, header=(header and ri == 0), sz=sz, align=aligns[ci],
                     w_cm=widths[ci])
            if header and ri == 0:
                c = c.replace("<w:tcMar>", hdr_border + "<w:tcMar>")
            tbl.append(c)
        tbl.append("</w:tr>")
    tbl.append("</w:tbl>")
    cap = para(caption, style="Caption", space_after=200, keep_next=False) if caption else ""
    pre = para("", space_after=0)
    return pre + "".join(tbl) + cap


IMG_RELS = []

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/>
<w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="312" w:lineRule="auto"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="center"/><w:spacing w:after="120"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:outlineLvl w:val="0"/><w:spacing w:before="280" w:after="140"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:outlineLvl w:val="1"/><w:spacing w:before="220" w:after="120"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:outlineLvl w:val="2"/><w:spacing w:before="180" w:after="100"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="center"/><w:spacing w:after="200"/></w:pPr>
<w:rPr><w:i/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
</w:styles>"""


def package(document_xml, extra_media):
    ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>',
          '<Default Extension="png" ContentType="image/png"/>',
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
          '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>',
          '</Types>']
    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>',
            '</Relationships>']
    drels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',
             '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>',
             '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>']
    for rid, target in IMG_RELS:
        drels.append(f'<Relationship Id="rId{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{target}"/>')
    drels.append('</Relationships>')
    footer = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
              '<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:line="240" w:lineRule="auto" w:after="0"/></w:pPr>'
              '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:t>Under review as a conference paper at ICLR 2027</w:t></w:r>'
              '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve">\u2003\u2014\u2003</w:t></w:r>'
              '<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
              '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
    header = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
              '<w:p><w:pPr><w:jc w:val="right"/><w:spacing w:line="240" w:lineRule="auto" w:after="0"/></w:pPr>'
              '<w:r><w:rPr><w:sz w:val="16"/><w:i/></w:rPr>'
              '<w:t>Safe Search Budgets Across Graph-ANNS Rebuilds</w:t></w:r></w:p></w:hdr>')
    sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rId2"/>'
            '<w:headerReference w:type="default" r:id="rId3"/>'
            '<w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
            'w:header="720" w:footer="720" w:gutter="0"/>'
            '<w:cols w:space="425"/><w:docGrid w:linePitch="312"/></w:sectPr>')
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
           'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
           'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
           f'<w:body>{document_xml}{sect}</w:body></w:document>')
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(ct))
        z.writestr("_rels/.rels", "".join(rels))
        z.writestr("word/document.xml", doc)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/_rels/document.xml.rels", "".join(drels))
        z.writestr("word/footer1.xml", footer)
        z.writestr("word/header1.xml", header)
        for name in extra_media:
            z.write(MEDIA / name, f"media/{name}")
        for n in range(1, 22):
            z.write(EQ / f"eq{n:02d}.png", f"eq/eq{n:02d}.png")
    return OUT
