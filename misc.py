#!/usr/bin/env python

"""
Miscellaneous functionality used by various other modules.
"""

__author__ 				= "Perry Kundert (perry@kundert.ca)"
__version__				= "$Revision: 45 $"
__date__ 				= "$Date: 2008-09-07 16:29:06 -0600 (Sun, 07 Sep 2008) $"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "GNU General Public License, Version 3 (or later)"

import math
import time

# 
# math.nan	-- IEEE NaN (Not a Number)
# math.isnan	-- True iff the provided value is math.nan
# 
# Augment math with some useful constants.  Note that IEEE NaN is the
# only floating point number that won't equal itself.
math.nan			= float( 'nan' )
def isnan( f ):
    return f != f

# 
# near		-- True iff the specified values are within 'significance' of each-other
# 
def near( a, b, significance = 1.0e-4 ):
    """ Returns True iff the difference between the values is within the factor 'significance' of
    one of the original values.  Default is to within 4 decimal places. """
    return abs( a - b ) <= significance * max( abs( a ), abs( b ))

# 
# clamp		-- Clamps a value to within a tuple of limits.
# 
#     Limits that are math.nan are automatically ignored, with no special code (comparisons
# against NaN always return False).
# 
def clamp( val, lim ):
    """ Limit val to between 2 (optional, if nan) limits """
    if ( val < lim[0] ):
        return lim[0]
    if ( val > lim[1] ):
        return lim[1]
    return val

# 
# scale		-- Transform a value from one range to another, without clipping
#
#     No math.nan allowed or zero-sized domains or ranges.  Works for either
# increasing or decreasing ordering of domains or ranges.
# 
def scale( val, dom, rng ):
    """Map 'val' from domain 'dom', to new range 'rng'"""
    return ( rng[0]
             + ( val    - dom[0] )
             * ( rng[1] - rng[0] )
             / ( dom[1] - dom[0] ))

# 
# magnitude	-- Return the approximate base magnitude of the value, in 'base' ( 10 )
#
#     Handy for computing up/down modifiers for values.  For example:
#
#      23 ==> 1.
#     .23 ==>  .1
# 
def magnitude( val, base = 10 ):
    return pow( base, round( math.log( val ) / math.log( base )) - 1 )

# 
# misc.value	-- Base class for things that should generally act like a float/int
# 
class value:
    """
    Acts like an integer or float in most use cases.  Use as a base class for
    things that want to have a simple integer or float value type interface.
    """
    __slots__			= [ 'value' ]
    def __init__( self,
                  value		= 0 ):

        self.value		= value

    def __str__( self ):
        return str( self.value )
    def __int__( self ):
        return int( self.value )
    def __float__( self ):
        return float( self.value )
        
    def __sub__( self, rhs ):
        return self.value - rhs
    def __rsub__( self, lhs ):
        return lhs - self.value

    def __add__( self, rhs ):
        return self.value + rhs
    def __radd__( self, lhs ):
        return lhs + self.value

    def __mul__( self, rhs ):
        return self.value * rhs
    def __rmul__( self, lhs ):
        return lhs * self.value

    def __div__( self, rhs ):
        return self.value / rhs
    def __rdiv__( self, lhs ):
        return lhs / self.value

    def __abs__( self ):
        return abs( self.value )
