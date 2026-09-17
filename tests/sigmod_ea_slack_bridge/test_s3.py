import importlib.util
import pathlib
import sys
import unittest

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sigmod_ea_slack_bridge" / "analyze_s3.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("s3", SCRIPT)
s3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s3)


class S3BridgeTests(unittest.TestCase):
    def test_roles_have_registered_sizes(self):
        roles, _ = s3.role_manifest()
        self.assertEqual([len(roles[k]) for k in roles], [375, 94, 281])

    def test_roles_are_disjoint_and_cover_750(self):
        roles, _ = s3.role_manifest()
        sets = [set(v) for v in roles.values()]
        self.assertFalse(sets[0] & sets[1])
        self.assertFalse(sets[0] & sets[2])
        self.assertFalse(sets[1] & sets[2])
        self.assertEqual(len(set.union(*sets)), 750)

    def test_role_hashes_are_deterministic(self):
        self.assertEqual(s3.role_manifest()[1], s3.role_manifest()[1])

    def test_source_selection_uses_only_source_cube(self):
        hit = np.full((2, 375, 3), 10, dtype=np.int16)
        hit[0, :, 0] = 9
        first = s3.select_source_actions(hit, np.asarray([10, 20, 40]), np.arange(375))
        altered_target = hit.copy()
        altered_target[1, :, :] = 9
        second = s3.select_source_actions(altered_target, np.asarray([10, 20, 40]), np.arange(375))
        self.assertEqual(first[0][0], second[0][0])

    def test_no_qualified_action_falls_back_to_endpoint(self):
        hit = np.full((1, 375, 3), 9, dtype=np.int16)
        result = s3.select_source_actions(hit, np.asarray([10, 20, 40]), np.arange(375))[0]
        self.assertEqual(result[0], 2)
        self.assertEqual(result[1], "NO_SOURCE_QUALIFIED_ACTION_ENDPOINT_FALLBACK")


if __name__ == "__main__":
    unittest.main()
