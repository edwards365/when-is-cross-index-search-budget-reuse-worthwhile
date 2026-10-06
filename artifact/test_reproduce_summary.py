"""New wrapper controls; no frozen experiment/control or dataset analysis."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec=importlib.util.spec_from_file_location('portable',Path(__file__).with_name('reproduce_summary.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='artifact-wrapper-')
        self.root=Path(self.temp.name).resolve()
    def tearDown(self):
        assert self.root.name.startswith('artifact-wrapper-') and self.root.parent==Path(tempfile.gettempdir()).resolve()
        self.temp.cleanup()
    def files(self,a,e):
        x,y=self.root/'actual.csv',self.root/'expected.csv'
        x.write_text(a,encoding='utf-8'); y.write_text(e,encoding='utf-8')
        return x,y
    def test_numeric_tolerance(self):
        r=m.compare(*self.files('v,status\n1.00000000001,PASS\n','v,status\n1.0,PASS\n'))
        self.assertEqual(r['within_tolerance_nonidentical_cells'],1)
    def test_status_not_coerced(self):
        with self.assertRaises(ValueError):m.compare(*self.files('v\nPASS\n','v\nFAIL\n'))
    def test_missing_not_zero(self):
        with self.assertRaises(ValueError):m.compare(*self.files('v,status\n,INFEASIBLE\n','v,status\n0,INFEASIBLE\n'))
    def test_large_numeric_change(self):
        with self.assertRaises(ValueError):m.compare(*self.files('v\n2\n','v\n1\n'))
    def test_archive_hash(self):
        p=self.root/'inputs.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('input.txt','ok')
        d=p.read_bytes(); b=b'ok'
        manifest={'archive':{'bytes':len(d),'sha256':m.sha(d)},'files':{'input.txt':{'bytes':len(b),'sha256':m.sha(b)}}}
        m.validate(p,manifest)
        p.write_bytes(d+b'bad')
        with self.assertRaises(ValueError):m.validate(p,manifest)
    def test_traversal_member(self):
        p=self.root/'unsafe.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('../input.txt','ok')
        d=p.read_bytes()
        manifest={'archive':{'bytes':len(d),'sha256':m.sha(d)},'files':{'../input.txt':{'bytes':2,'sha256':m.sha(b'ok')}}}
        with self.assertRaises(ValueError):m.validate(p,manifest)

if __name__=='__main__':unittest.main()
