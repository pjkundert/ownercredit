from misc import *

def test_nan():
    assert True  == isnan( float( 'nan' ))
    assert False == isnan( 1.0 )


def test_scale():
    assert near( scale(   0., ( 0., 100. ), ( 32., 212. )),  32. )
    assert near( scale( -40., ( 0., 100. ), ( 32., 212. )), -40. )
    assert near( scale(  20., ( 0., 100. ), ( 32., 212. )),  68. )

    # Try an inverted mapping (a reverse-ordered range)
    assert near( scale(   0., ( 0., 100. ), ( 1., -1.   )),   1. )
    assert near( scale( -40., ( 0., 100. ), ( 1., -1.   )),   1.80 )
    assert near( scale(  20., ( 0., 100. ), ( 1., -1.   )),   0.60 )
    assert near( scale( 120., ( 0., 100. ), ( 1., -1.   )),  -1.40 )

    # Try a reverse-ordered domain
    assert near( scale(   0., ( 100., 0. ), ( 32., 212. )), 212. )
    assert near( scale( -40., ( 100., 0. ), ( 32., 212. )), 284. )
    assert near( scale(  20., ( 100., 0. ), ( 32., 212. )), 176. )

def test_magnitude():
    # base 10 (the default)
    assert near( magnitude( 23.   ),  1.   )
    assert near( magnitude(   .23 ),  .01  )
    
    assert near( magnitude( 75.   ), 10.   )
    assert near( magnitude(   .03 ),  .001 )

    # base 2
    assert near( magnitude( 33., 2 ),  16. )
    assert near( magnitude( 50., 2 ),  32. )
