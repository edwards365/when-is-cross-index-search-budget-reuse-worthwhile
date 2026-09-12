#!/usr/bin/env python
"""Strict-mode schema order checker for the generated document.xml.
Verifies child ordering of w:pPr, w:rPr, w:tcPr against the OOXML sequences."""
import re
import sys
import zipfile

ORDER = {
    "pPr": ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "numPr", "tabs",
            "spacing", "ind", "jc", "outlineLvl", "rPr", "sectPr"],
    "rPr": ["rStyle", "rFonts", "b", "i", "caps", "color", "sz", "szCs"],
    "tcPr": ["tcW", "gridSpan", "tcBorders", "shd", "tcMar", "vAlign"],
    "trPr": ["cantSplit", "trHeight", "tblHeader"],
    "tblPr": ["tblW", "tblBorders", "tblLayout"],
}

def check(docx):
    z = zipfile.ZipFile(docx)
    doc = z.read("word/document.xml").decode()
    bad = 0
    for tag, seq in ORDER.items():
        for m in re.finditer(rf"<w:{tag}>((?:(?!</w:{tag}>).)*)</w:{tag}>", doc):
            kids = re.findall(r"<w:(\w+)[ />]", m.group(1))
            idx = [seq.index(k) for k in kids if k in seq]
            if idx != sorted(idx):
                bad += 1
                if bad <= 5:
                    print(f"ORDER VIOLATION in w:{tag}: {kids}")
    return bad

if __name__ == "__main__":
    bad = check(sys.argv[1])
    print(f"order violations: {bad}")
    sys.exit(1 if bad else 0)
