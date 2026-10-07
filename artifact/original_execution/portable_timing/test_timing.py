import csv
import json
import platform
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import numpy as np
from timing import FIELDS,digest,query_ids,reference,validate,mean_service,save_arrays

HERE=Path(__file__).resolve().parent

class TimingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.ids=[100,200];self.grid=[10,2400];self.expected={(e,i):tuple(range(10)) for e in self.grid for i in range(2)}
        self.rows=[]
        for r in range(7):
            for i,q in enumerate(self.ids):
                for a,e in enumerate(self.grid):
                    self.rows.append([q,i,r,e,a,10+r+a,0,';'.join(map(str,range(10))),'OK'])

    def csv(self,rows=None,fields=FIELDS):
        path=self.root/'test.csv'
        with path.open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f);writer.writerow(fields);writer.writerows(self.rows if rows is None else rows)
        return path

    def test_source_pin_and_frozen_grid(self):
        cfg=json.loads((HERE/'config.json').read_text())
        self.assertEqual(digest(HERE/'e1a_runtime_native.cpp'),cfg['source_sha256'])
        self.assertEqual(cfg['action_grid'],[10,20,40,80,120,200,400,800,1200,1600,2400])
        self.assertEqual((cfg['queries'],cfg['repetitions']),(1000,7))

    def test_complete_zero_cpu_and_mean(self):
        wall,cpu,audit=validate(self.csv(),self.ids,self.grid,self.expected)
        self.assertEqual(audit['rows'],28);self.assertEqual(audit['zero_process_cpu_cells'],28)
        np.testing.assert_array_equal(mean_service(wall,[0,1]),[13,14])
        self.assertEqual(int(cpu.sum()),0)

    def test_duplicate_cell_rejected(self):
        with self.assertRaises(ValueError):validate(self.csv(self.rows+[self.rows[0]]),self.ids,self.grid,self.expected)

    def test_duplicate_order_rejected(self):
        self.rows[1][4]=0
        with self.assertRaises(ValueError):validate(self.csv(),self.ids,self.grid,self.expected)

    def test_missing_cell_rejected(self):
        with self.assertRaises(ValueError):validate(self.csv(self.rows[:-1]),self.ids,self.grid,self.expected)

    def test_duration_boundaries(self):
        for column,value in [(5,0),(5,-1),(5,2**64),(6,-1),(6,2**64)]:
            with self.subTest(column=column,value=value):
                rows=[r[:] for r in self.rows];rows[0][column]=value
                with self.assertRaises(ValueError):validate(self.csv(rows),self.ids,self.grid,self.expected)

    def test_identity_and_status_rejections(self):
        for column,value in [(0,999),(1,9),(2,7),(3,20),(4,2),(7,'9;8;7;6;5;4;3;2;1;0'),(8,'STOP')]:
            with self.subTest(column=column):
                rows=[r[:] for r in self.rows];rows[0][column]=value
                with self.assertRaises(ValueError):validate(self.csv(rows),self.ids,self.grid,self.expected)

    def test_schema_rejection(self):
        with self.assertRaises(ValueError):validate(self.csv(fields=FIELDS[:-1]+['other']),self.ids,self.grid,self.expected)

    def test_query_eof_duplicate_and_shape(self):
        p=self.root/'queries.qbin'
        data=b'E1AQ0001'+struct.pack('<QQ',1000,1)+b''.join(struct.pack('<qf',i,float(i)) for i in range(1000))
        p.write_bytes(data);self.assertEqual(query_ids(p),list(range(1000)))
        for bad in (data+b'x',data[:-1],data[:8]+struct.pack('<Q',999)+data[16:],data[:36]+struct.pack('<qf',0,1)+data[48:]):
            p.write_bytes(bad)
            with self.assertRaises(ValueError):query_ids(p)

    def test_reference_order_and_ndc(self):
        p=self.root/'reference.csv'
        rows=[[q,e,10,';'.join(map(str,range(10)))] for e in self.grid for q in self.ids]
        with p.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['query_id','ef','ndc','topk']);w.writerows(rows)
        self.assertEqual(reference(p,self.ids,self.grid),self.expected)
        with self.assertRaises(ValueError):reference(p,list(reversed(self.ids)),self.grid)

    def test_arrays_and_selection_shape(self):
        wall,cpu,_=validate(self.csv(),self.ids,self.grid,self.expected);p=self.root/'arrays.npz'
        save_arrays(p,self.ids,self.grid,wall,cpu)
        with np.load(p,allow_pickle=False) as d:
            self.assertEqual(d.files,['query_ids','action_grid','wall_ns','cpu_ns'])
            np.testing.assert_array_equal(d['wall_ns'],wall)
        with self.assertRaises(FileExistsError):save_arrays(p,self.ids,self.grid,wall,cpu)
        for action in ([0],[-1,0],[2,0],[0.0,1.0]):
            with self.assertRaises(ValueError):mean_service(wall,action)

    def test_build_receipt_identity_rejection(self):
        from run_timing import validated_native
        cfg=json.loads((HERE/'config.json').read_text())
        (self.root/'completed.json').write_text(json.dumps({'status':'OLD_OR_FAILED_BUILD'}))
        with self.assertRaises(ValueError):validated_native(self.root,cfg)

    def test_profile_role_rejection(self):
        from run_timing import validated_profile
        cfg=json.loads((HERE/'config.json').read_text())
        (self.root/'completed.json').write_text(json.dumps({'status':'NEW_PROFILES_MATCH_ALL_FROZEN_CSVS','dataset':'sift','role':'source_design'}))
        (self.root/'start.json').write_text('{}')
        with self.assertRaises(ValueError):validated_profile(self.root,'sift',cfg['build_ids'][0],cfg)

    @unittest.skipUnless(platform.system()=='Linux' and platform.machine()=='x86_64' and sys.version_info[:2]==(3,11),'Linux x86_64 Python3.11 native CI')
    def test_unchanged_cpp_full_protocol_tiny_graphs(self):
        from build_native import build
        out=self.root/'native';build(out,HERE.parent/'portable_profiles')
        r=json.loads((out/'completed.json').read_text())
        self.assertEqual(r['status'],'PASS_NEW_NATIVE_TIMING_BUILD_AND_SYNTHETIC_CHECKS')
        self.assertEqual([x['rows'] for x in r['synthetic_results']],[77000,77000])
        self.assertEqual(r['original_data_runs'],0)

if __name__=='__main__':unittest.main()
