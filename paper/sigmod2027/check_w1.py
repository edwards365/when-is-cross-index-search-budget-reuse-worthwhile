"""Structural writing checks only; no experiment or statistical validation."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ledger = json.loads((ROOT / 'evidence/evidence_ledger.json').read_text(encoding='utf-8'))
macro_text = (ROOT / 'evidence/results_macros.tex').read_text(encoding='utf-8')
macros = dict(re.findall(r'\\newcommand\{\\(WZero\w+)\}\{([^}]+)\}', macro_text))
expected = {row['macro']: row['display'] for row in ledger['numbers']}
assert macros == expected, 'W0 macro/ledger mismatch'
sections = sorted((ROOT / 'sections').glob('*.tex'))
assert len(sections) == 10
text = '\n'.join(p.read_text(encoding='utf-8') for p in [ROOT / 'main.tex', *sections])
used = set(re.findall(r'\\(WZero\w+)', text))
assert used <= macros.keys(), used - macros.keys()
labels = re.findall(r'\\label\{([^}]+)\}', text)
refs = re.findall(r'\\(?:ref|eqref)\{([^}]+)\}', text)
assert len(labels) == len(set(labels)), 'Duplicate labels'
assert set(refs) <= set(labels), set(refs) - set(labels)
assert text.count(r'\begin{figure}') == 5
assert text.count(r'\begin{table}') == 4
assert '[Experiments \\& Analysis]' in text
assert not re.search(r'\\(?:geometry|fontsize|baselinestretch)\b', text)
assert not re.search(r'https?://|101\.6\.|/home/|wanglekang|edwards365', text)
assert '2026/08/16 v2.20' in (ROOT/'acmart.cls').read_text(encoding='utf-8')
bib = (ROOT / 'references.bib').read_text(encoding='utf-8')
keys = re.findall(r'@\w+\{([^,]+),', bib)
assert len(keys) == len(set(keys)), 'Duplicate bibliography keys'
cited = {key.strip() for group in re.findall(r'\\cite\w*\{([^}]+)\}', text) for key in group.split(',')}
assert cited == set(keys), ('Unresolved or unused references', cited ^ set(keys))
assert len(keys) == 13
assert r'\bibliography{references}' in text
for section in sections[:2]:
    prose = section.read_text(encoding='utf-8')
    assert r'\sectionaim' not in prose
    assert 'Contributions to develop' not in prose
assert '5\\% mixed delete/insert refresh' in sections[0].read_text(encoding='utf-8')
print(f'PASS: {len(macros)} W0 macros, {len(used)} referenced; 10 sections; 5 figure slots; 4 tables; labels resolved.')
print(f'PASS: W2 Introduction/Related Work; {len(keys)} unique, cited bibliography entries; refresh scope explicit.')
print('Template SHA256:', hashlib.sha256((ROOT/'acmart.cls').read_bytes()).hexdigest())
print('Scope: structure and frozen-value linkage, NOT scientific validation or submission readiness.')
