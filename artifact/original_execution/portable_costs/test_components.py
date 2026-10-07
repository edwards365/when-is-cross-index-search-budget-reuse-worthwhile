import copy,tempfile,unittest
from decimal import Decimal
from pathlib import Path
import components as c
class Components(unittest.TestCase):
    def records(self):
        ds='tiny';prefix='datasets__tiny__';rows={prefix+'truth_receipt':{'status':'EXACT_TRUTH_ACQUIRED_NO_ANN_OUTCOME_ACCESSED','exact_base_acquisition_ns':100,
            'roles':{r:{'query_read_ns':10,'exact_search_ns':20} for r in c.ROLES}},
            'profile_audit':{'status':'PASS_FULL_ORDERED_ID_AND_NATIVE_COUNT_AUDIT','rows':[{'dataset':ds,'role':r} for r in c.ROLES]},
            'decision_lock':{'status':'DECISIONS_LOCKED_BEFORE_EVALUATION_ARRAY_READ','decision_compute_ns_including_audited_array_read':8},
            'roles_receipt':{'status':'PASS_NEW_ROLE_AND_CONTENT_FIREWALL_BEFORE_OUTCOME','wall_seconds':Decimal('0.000000020')}}
        for role in c.ROLES:rows[prefix+'profile_finals__'+role]={'dataset':ds,'status':'NATIVE_PROFILES_COMPLETE_AUDIT_PENDING','whole_unit_ns':30,'profiles':[{'build':str(i),'actual_exit_code':0} for i in range(8)]}
        return rows
    def test_exact_allocation(self):self.assertEqual(sum(c.fixed_components('tiny',self.records()).values()),294)
    def test_missing_component_not_zero(self):
        r=self.records();del r['roles_receipt']['wall_seconds']
        with self.assertRaises(KeyError):c.fixed_components('tiny',r)
    def test_new_adapter_not_old_timer(self):
        r=self.records();r['roles_receipt']['status']='NEW_ROLE_BASE_QUERY_PREPARATION_COMPLETED'
        with self.assertRaises(ValueError):c.fixed_components('tiny',r)
    def test_failed_profile(self):
        r=self.records();r['datasets__tiny__profile_finals__source_design']['profiles'][0]['actual_exit_code']=1
        with self.assertRaises(ValueError):c.fixed_components('tiny',r)
    def test_unaudited(self):
        r=self.records();r['profile_audit']['rows'].pop()
        with self.assertRaises(ValueError):c.fixed_components('tiny',r)
    def test_compare(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';p.write_text('dataset,component,seconds\na,b,1\n',encoding='utf-8')
            c.compare_expected([{'dataset':'a','component':'b','seconds':'1.00000000001'}],p)
            with self.assertRaises(ValueError):c.compare_expected([{'dataset':'a','component':'b','seconds':'1.1'}],p)
if __name__=='__main__':unittest.main()
