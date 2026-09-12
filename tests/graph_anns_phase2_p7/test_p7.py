"""P7 checks: validate the revised paper package."""
import zipfile
import xml.etree.ElementTree as ET
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOCX = REPO / "results/graph_anns_phase2_p7/ICBA_ICLR_Anonymous_Revised_v2.docx"
checks = []
def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")

check("docx_exists", DOCX.exists() and DOCX.stat().st_size > 500_000)
z = zipfile.ZipFile(DOCX)
ok_xml = True
for n in z.namelist():
    if n.endswith(('.xml', '.rels')):
        try:
            ET.fromstring(z.read(n))
        except Exception:
            ok_xml = False
check("all_xml_wellformed", ok_xml)
doc = z.read('word/document.xml').decode()
texts = "".join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', doc))
check("figures_7_drawings", doc.count('<w:drawing>') == 7)
check("native_omath_21", doc.count('<m:oMath>') == 21)
check("no_equation_images", not [n for n in z.namelist() if n.startswith('eq/')])
check("mathfont_settings", b'Cambria Math' in z.read('word/settings.xml'))
check("tables_11", doc.count('<w:tbl>') == 11)
for probe in ["21.87", "max-over-source", "DistComp", "k=7 still leaves 10.4%",
              "Yu, B. (1997)", "0.47-0.63", "21.55% [20.76, 22.33]", "V_fin",
              "79.5-93.4", "three-layer", "preregistered"]:
    check(f"content::{probe[:24]}", probe in texts)
styles = z.read('word/styles.xml').decode()
check("heading_styles_defined", all(f'w:styleId="Heading{i}"' in styles for i in (1, 2, 3)))
check("line_spacing_312", 'w:line="312"' in styles)

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
