from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from ownercredit.misc import *

def test_nan():
    assert True  == isnan( float( 'nan' ))
    assert False == isnan( 1.0 )
    l = [1.0, nan, 0.0]
    l.sort( key=nan_first )
    assert isnan( l[0] )
    l.sort( key=nan_last )
    assert isnan( l[-1] )

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

    # An exponential mapping
    assert near( scale(  40,       ( 25  , 40 ), ( 0, 1 )),              1 )
    assert near( scale(  40,       ( 25  , 40 ), ( 0, 1 ), exponent=2),  1 )
    assert near( scale(  25,       ( 25  , 40 ), ( 0, 1 )),              0 )
    assert near( scale(  25,       ( 25  , 40 ), ( 0, 1 ), exponent=2),  0 )
    assert near( scale(  25+15/2 , ( 25  , 40 ), ( 0, 1 )),               .5 )
    assert near( scale(  25+15/2 , ( 25  , 40 ), ( 0, 1 ), exponent=2),   .25 )
    assert near( scale(  39      , ( 25  , 40 ), ( 0, 1 )),               .9333 )
    assert near( scale(  39      , ( 25  , 40 ), ( 0, 1 ), exponent=2),   .8711 )
    assert near( scale(  26      , ( 25  , 40 ), ( 0, 1 )),               .066667 )
    assert near( scale(  26      , ( 25  , 40 ), ( 0, 1 ), exponent=2),   .004444 )

    # Ensure non-linear scaling ensures negatives may be handled by clamping domain
    assert near( scale(  24      , ( 25  , 40 ), ( 0, 1 ), exponent=2, clamped=True ),  0 )
    

def test_magnitude():
    # base 10 (the default)
    assert near( magnitude( 23.   ),  1.   )
    assert near( magnitude(   .23 ),  .01  )
    
    assert near( magnitude( 75.   ), 10.   )
    assert near( magnitude(   .03 ),  .001 )

    # base 2
    assert near( magnitude( 33., 2 ),  16. )
    assert near( magnitude( 50., 2 ),  32. )

def test_value():
    v = value( 1 )
    v *= 5      # __imul__
    assert 5 == v
    i = 5
    i //= v      # __rfloordiv__
    assert i == 1
    i
    assert type( i ) == int
    x = v + 5
    assert type( x ) == int
    x = 5 + v
    assert type( x ) == int


