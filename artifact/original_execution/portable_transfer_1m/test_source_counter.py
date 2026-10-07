import csv,tempfile,unittest
from pathlib import Path
import numpy as np
from source_counter import validate

class CounterTests(unittest.TestCase):
    def test_distinct_source_array_schema_and_mismatch_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'response.csv';ids=np.array([100,101]);grid=[10,2400];top=np.tile(np.arange(10),(2,2,1));original={'topk':top,'hits':np.full((2,2),10),'z_abs':np.zeros((2,2),bool)};neighbors=top[0]
            with p.open('x',newline='') as f:
                w=csv.writer(f);w.writerow(['query_id','ef','ndc','topk'])
                for ef in grid:
                    for q in ids:w.writerow([q,ef,33,';'.join(map(str,range(10)))])
            np.testing.assert_array_equal(validate(p,ids,grid,original,neighbors,np),np.full((2,2),33))
            original['hits'][0,0]=9
            with self.assertRaises(ValueError):validate(p,ids,grid,original,neighbors,np)

if __name__=='__main__':unittest.main()
