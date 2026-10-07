import csv
import json
from pathlib import Path
import tempfile
import unittest
import native_entry as native

class Tests(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name)/'x.csv'
    def tearDown(self):self.t.cleanup()
    def write(self,**changes):
        row={'query_id':100,'ef':10,'ndc':24,'topk':';'.join(map(str,range(10)))};row.update(changes)
        with self.p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerow(row)
    def reject(self,**changes):
        self.write(**changes)
        with self.assertRaises(ValueError):native.validate_csv(self.p,[100],[10],range(32))
    def test_valid(self):self.write();self.assertEqual(native.validate_csv(self.p,[100],[10],range(32)),1)
    def test_query(self):self.reject(query_id=101)
    def test_grid(self):self.reject(ef=40)
    def test_count(self):self.reject(ndc=0)
    def test_duplicate(self):self.reject(topk=';'.join(['1']*10))
    def test_outside(self):self.reject(topk=';'.join(map(str,range(40,50))))
    def test_short(self):self.reject(topk='1;2')
    def test_missing(self):
        self.write()
        with self.assertRaises(ValueError):native.validate_csv(self.p,[100,101],[10],range(32))
    def test_extra(self):
        self.write()
        with self.assertRaises(ValueError):native.validate_csv(self.p,[],[10],range(32))
    def test_sources(self):
        cfg=json.loads((native.HERE/'config.json').read_text())
        for name,h in cfg['files'].items():self.assertEqual(native.sha(native.HERE/name),h)

if __name__=='__main__':unittest.main()
