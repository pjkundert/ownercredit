from misc import *

def test_nan():
    assert True  == isnan( float( 'nan' ))
    assert False == isnan( 1.0 )


