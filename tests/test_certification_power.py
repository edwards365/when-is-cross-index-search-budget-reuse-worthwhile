from icba_theory import certification_k,certification_power
def test_preregistered_number():assert certification_k(256,16,.05,.05)==3
def test_more_candidates_reduce_power():
 assert certification_power(256,1,.05,.05,.02)>certification_power(256,16,.05,.05,.02)
def test_more_samples_help_for_safe_rate():
 assert certification_power(1024,16,.05,.05,.02)>certification_power(64,16,.05,.05,.02)
