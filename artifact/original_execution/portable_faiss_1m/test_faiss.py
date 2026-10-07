import contextlib,importlib.util,io,json,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('faiss1m_core',HERE/'historical_core.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
s=importlib.util.spec_from_file_location('faiss1m_entry',HERE/'run_faiss.py');entry=importlib.util.module_from_spec(s);s.loader.exec_module(entry)
class Tests(unittest.TestCase):
    def test_all_sibling_dependency_pins_before_native_compile(self):
        cfg=json.loads((HERE/'config.json').read_text())
        for relative,digest in cfg['dependencies'].items():
            with self.subTest(dependency=relative):entry.pin(HERE.parent/relative,digest)
    def test_truth_uses_own_predecessor_before_data_access(self):
        for phase,previous in [('selection','source'),('certify','selection'),('evaluate','certify')]:
            with patch.object(entry,'panel',side_effect=ValueError('gate')) as gate,patch.object(entry,'load') as native:
                with self.assertRaisesRegex(ValueError,'gate'):
                    entry.generate_truth({'phase':phase,'prior_panel':'faiss-only'},Path('never-created'),{},None)
                gate.assert_called_once_with('faiss-only',{},previous);native.assert_not_called()
        self.assertIsNone(entry.predecessor({'phase':'source'},{}))
    def test_truth_core_pin_and_roles(self):
        cfg=json.loads((HERE/'config.json').read_text())
        entry.pin(HERE.parent/'portable_transfer_1m/historical_core.py',cfg['dependencies']['portable_transfer_1m/historical_core.py'])
        tc=json.loads((HERE.parent/'portable_transfer_1m/config.json').read_text())
        self.assertEqual(cfg['truth_pins'],tc['e1a_truth_pins'])
        self.assertEqual(cfg['datasets'],tc['datasets'])
    def test_cp_boundary(self):
        self.assertEqual(core.source_cp_upper(500,500,.05),1)
        self.assertAlmostEqual(core.source_cp_upper(0,500,.05),core.cp_upper(0,500,.05),places=14)
    def test_full_selection_and_certification(self):
        bids=[core.build_id(s,h) for s in core.SEEDS for h in core.HISTORIES]
        sources=[{'dataset':'tiny','seed':s,'history':h,'selected_source_action':16} for s in core.SEEDS for h in core.HISTORIES]
        responses={b:{'z_abs':np.zeros((9,500),dtype=bool),'array_sha':'abc'} for b in bids}
        lock=core.select_dataset('tiny',responses,sources)
        self.assertEqual(len(lock['directed_pair_actions']),552);self.assertEqual(len(lock['target_global_actions']),24)
        decisions=core.certify_dataset('tiny',{b:({a:np.zeros(500,dtype=bool) for a in core.GRID},'abc') for b in bids},lock)
        self.assertEqual(len(decisions),1704);self.assertTrue(all(r['decision'] in ('EXECUTE_CANDIDATE','EXECUTE_ENDPOINT') for r in decisions))
    def test_unqualified_endpoint_abstains(self):
        r=core.decide('tiny','target','source','candidate',16,{16:np.zeros(500,dtype=bool),4096:np.ones(500,dtype=bool)},'abc')
        self.assertEqual(r['decision'],'ABSTAIN');self.assertIsNone(r['execute_efSearch'])
    def test_required_actions_preserve_all_candidates(self):
        rows=[dict(dataset='tiny',target_build_id='t',candidate_efSearch=16,execute_efSearch=4096) for _ in range(71)]
        self.assertEqual(entry.actions({'policy':{'decisions':rows}},'evaluate','tiny','t',core.GRID),[16,4096])
        with self.assertRaises(ValueError):entry.actions({'policy':{'decisions':rows[:-1]}},'evaluate','tiny','t',core.GRID)
    def test_key_distinguishes_seed_records_not_content(self):
        self.assertNotEqual(entry.key({'dataset':'tiny','seed':13,'history':'norm_ascending'}),entry.key({'dataset':'tiny','seed':83,'history':'norm_ascending'}))
if __name__=='__main__':unittest.main()
