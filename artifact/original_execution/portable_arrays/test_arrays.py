import csv
from pathlib import Path
import tempfile
import unittest
import numpy as np
import materialize as m

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
        self.ids=np.array([100,101],dtype=np.int64);self.grid=[10,40];self.builds=['a','b'];self.base=np.arange(20,dtype=np.int64)
        self.truth=np.tile(np.arange(10,dtype=np.int64),(2,1));self.rows=[]
        for ef in self.grid:
            for q in self.ids:self.rows.append({'query_id':q,'ef':ef,'ndc':25,'topk':';'.join(map(str,range(5,15)))})
        self.save()
    def tearDown(self):self.tmp.cleanup()
    def save(self):
        for b in self.builds:
            with (self.p/(b+'.csv')).open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['query_id','ef','ndc','topk']);w.writeheader();w.writerows(self.rows)
    def run_arrays(self):return m.arrays_from_csv(self.p,self.ids,self.grid,self.builds,self.truth,self.base,np)
    def reject(self):
        self.save()
        with self.assertRaises(ValueError):self.run_arrays()
    def test_correct(self):
        a=self.run_arrays();self.assertTrue(np.all(a['hits']==5));self.assertEqual(a['hits'].dtype,np.int16)
        self.assertEqual(a['ndc'].dtype,np.uint64);self.assertEqual(a['topk'].dtype,np.int64)
        self.assertEqual(a['action_grid'].dtype,np.int32);self.assertEqual(a['topk'].shape,(2,2,2,10))
        self.assertEqual(list(a),['query_ids','action_grid','build_ids','hits','ndc','topk'])
    def test_missing(self):self.rows.pop();self.reject()
    def test_extra(self):self.rows.append(self.rows[-1]);self.reject()
    def test_order(self):self.rows.reverse();self.reject()
    def test_counter_zero(self):self.rows[0]['ndc']=0;self.reject()
    def test_counter_overflow(self):self.rows[0]['ndc']=2**64;self.reject()
    def test_duplicate(self):self.rows[0]['topk']=';'.join(['5']*10);self.reject()
    def test_excluded(self):self.rows[0]['topk']=';'.join(map(str,range(15,25)));self.reject()
    def test_truth_bad(self):
        self.truth[0,0]=50
        with self.assertRaises(ValueError):self.run_arrays()
    def test_serialization(self):
        a=self.run_arrays();p=self.p/'x.npz';m.write_array(p,a,np)
        with np.load(p,allow_pickle=False) as r:
            for n in a:np.testing.assert_array_equal(r[n],a[n])
        with self.assertRaises(FileExistsError):m.write_array(p,a,np)
    def test_roles_duplicate(self):
        self.ids[1]=self.ids[0]
        with self.assertRaises(ValueError):self.run_arrays()
    def test_empty_row(self):self.rows[0]['topk']='';self.reject()

if __name__=='__main__':unittest.main()
