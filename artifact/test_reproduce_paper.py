"""Bounded controls for the new portable saved-record entry."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np

spec=importlib.util.spec_from_file_location('paper',Path(__file__).with_name('reproduce_paper.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PaperControls(unittest.TestCase):
    def test_input_manifest(self):
        self.assertEqual(len(m.check_inputs()['files']),12)
    def test_tampered_input_rejected(self):
        original=Path.read_bytes
        def changed(path):
            data=original(path)
            return data+b'bad' if path.name=='sift_paired.npz' else data
        with patch.object(Path,'read_bytes',changed):
            with self.assertRaisesRegex(ValueError,'Input identity mismatch'):
                m.check_inputs()
    def test_nonfinite_rejected(self):
        for value in (float('nan'),float('inf')):
            with self.assertRaises(ValueError):m.close(value,value,'not finite')
    def test_tolerance(self):
        m.close(1+1e-12,1,'small roundoff')
        with self.assertRaises(ValueError):m.close(2,1,'changed value')
    def test_crossed_requires_full_panel(self):
        with self.assertRaises(ValueError):m.crossed(np.zeros((7,1000)))
    def test_strict_repayment(self):
        B,D=20,10
        V=m.math.floor(B/D)+1
        self.assertEqual(V,3)
        self.assertLess(B-V*D,0)
        self.assertEqual(B-(V-1)*D,0)

if __name__=='__main__':unittest.main()
