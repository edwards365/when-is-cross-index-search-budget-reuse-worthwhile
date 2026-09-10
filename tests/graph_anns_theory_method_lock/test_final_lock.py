import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "graph_anns_theory_method_lock" / "validate_lock.py"
SPEC = importlib.util.spec_from_file_location("validate_lock", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class FinalLockTest(unittest.TestCase):
    def test_all_twenty_contract_checks(self):
        passed = MODULE.validate()
        self.assertEqual(len(passed), 20)


if __name__ == "__main__":
    unittest.main()
