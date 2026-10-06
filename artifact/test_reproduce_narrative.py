import unittest
import numpy as np
from reproduce_narrative import cube,crossed_mean_ratio

class NarrativeControls(unittest.TestCase):
    def test_missing_cube_rejected(self):
        with self.assertRaises(ValueError):cube([],['failure'])
    def test_bad_query_count(self):
        with self.assertRaises(ValueError):crossed_mean_ratio(np.zeros((8,499)),np.ones((8,499)),np.ones((8,499)))
    def test_zero_endpoint_cost_rejected(self):
        with self.assertRaises(ValueError):crossed_mean_ratio(np.zeros((8,500)),np.ones((8,500)),np.zeros((8,500)))
    def test_exact_constant_interval(self):
        ci=crossed_mean_ratio(np.full((8,500),.1),np.ones((8,500)),np.full((8,500),2.),reps=8)
        np.testing.assert_allclose(ci,[[.1,.5],[.1,.5]])

if __name__=='__main__':unittest.main()
