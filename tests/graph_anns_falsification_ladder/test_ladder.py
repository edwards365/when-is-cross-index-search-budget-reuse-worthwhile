import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "scripts" / "graph_anns_falsification_ladder" / "validate_ladder.py"
SPEC = importlib.util.spec_from_file_location("validate_ladder", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class FalsificationLadderTest(unittest.TestCase):
    def test_twenty_contract_checks(self):
        self.assertEqual(len(MODULE.validate()), 20)


if __name__ == "__main__":
    unittest.main()
