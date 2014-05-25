#!/usr/bin/env python

"""
Miscellaneous functionality used by various other modules.
"""

# This file is part of Owner Credit
# 
# Owner Credit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# Owner Credit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Owner Credit.  If not, see <http://www.gnu.org/licenses/>.

__author__                      = "Perry Kundert"
__email__                       = "perry@kundert.ca"
__copyright__                   = "Copyright (c) 2006 Perry Kundert"
__license__                     = "GNU General Public License, Version 2 (or later)"

import math
import sys
import time

# 
# misc.timer
# 
# Select platform appropriate timer function
# 
if sys.platform == 'win32':
    # On Windows, the best timer is time.clock
    timer 			= time.clock
else:
    # On most other platforms the best timer is time.time
    timer			= time.time

# 
# misc.nan	-- IEEE NaN (Not a Number)
# misc.isnan	-- True iff the provided value is nan
# misc.inf	-- IEEE inf (Infinity)
# misc.isinf	-- True iff the provided value is inf
# 
#     Augment math with some useful constants.  Note that IEEE NaN is the
# only floating point number that won't equal itself.
# 
#     Numpy has these, but we can't assume it is available.
# 
if hasattr( math, 'nan' ):
    nan                         = math.nan
else:
    nan                         = float( 'nan' )
    math.nan                    = nan
if hasattr( math, 'isnan' ):
    isnan                       = math.isnan
else:
    def isnan( f ):
        return f != f
    math.isnan = isnan

if hasattr( math, 'inf' ):
    inf				= math.inf
else:
    inf				= float( 'inf' )
    math.inf			= inf
if hasattr( math, 'isinf' ):
    isinf			= math.isinf
else:
    def isinf( f ):
        return abs( f ) == inf
    math.isinf = isinf

# 
# near          -- True iff the specified values are within 'significance' of each-other
# 
def near( a, b, significance = 1.0e-4 ):
    """ Returns True iff the difference between the values is within the factor 'significance' of
    one of the original values.  Default is to within 4 decimal places. """
    return abs( a - b ) <= significance * max( abs( a ), abs( b ))

# 
# clamp         -- Clamps a value to within a tuple of limits.
# 
#     Limits that are math.nan are automatically ignored, with no special code (comparisons
# against NaN always return False).
# 
#     The ordering of 'lim' is assumed to be (min, max).  We don't attempt to reorder, because 'lim'
# may contain NaN.
# 
def clamp( val, lim ):
    """ Limit val to between 2 (optional, if nan) limits """
    if ( val < lim[0] ):
        return lim[0]
    if ( val > lim[1] ):
        return lim[1]
    return val

# 
# scale         -- Transform a value from one range to another, without clipping
#
#     No math.nan allowed or zero-sized domains or ranges.  Works for either increasing or
# decreasing ordering of domains or ranges.  If clamped, we will ensure that the rng is (re)ordered
# appropriately.
# 
def scale( val, dom, rng, clamped=False ):
    """Map 'val' from domain 'dom', to new range 'rng'"""
    result                      = ( rng[0]
                                    + ( val    - dom[0] )
                                    * ( rng[1] - rng[0] )
                                    / ( dom[1] - dom[0] ))
    if clamped:
        result                  = clamp( result, (min(rng), max(rng)))
    return result

# 
# magnitude     -- Return the approximate base magnitude of the value, in 'base' ( 10 )
#
#     Handy for computing up/down modifiers for values.  For example:
#
#      23 ==> 1.
#     .23 ==>  .1
# 
# The magnitude shifts to the next higher value about 1/4 of the way
# past each multiple of base.

def magnitude( val, base = 10 ):
    if val <= 0:
        return nan
    return pow( base, round( math.log( val, base )) - 1 )


# 
# sort order key=... methods
# 
# natural	-- Strings containing numbers sort in natural order
# nan_first	-- NaN/None sorts lower than any number
# nan_last	-- NaN/None sorts higher than any number
# 
def natural( string ):
    '''
    A natural sort key helper function for sort() and sorted() without
    using regular expressions or exceptions.

    >>> items = ('Z', 'a', '10th', '1st', '9')
    >>> sorted(items)
    ['10th', '1st', '9', 'Z', 'a']
    >>> sorted(items, key=natural)
    ['1st', '9', '10th', 'a', 'Z']    
    '''
    it = type( 1 )
    r = []
    for c in string:
        if c.isdigit():
            d = int( c )
            if r and type( r[-1] ) == it: 
                r[-1] = r[-1] * 10 + d
            else: 
                r.append( d )
        else:
            r.append( c.lower() )
    return r

def non_value( number ):
    return number is None or isnan( number )

def nan_first( number ):
    if non_value( number ):
        return -inf
    return number

def nan_last( number ):
    if non_value( number ):
        return inf
    return number

# 
# misc.value    -- Base class for things that should generally act like a float/int
# 
class value( object ):
    """
    Acts like an integer or float in most use cases.  Use as a base class for things that want to
    have a simple integer or float value type interface for arithmetic expressions.  Also handles
    several non-values correctly: None, misc.nan.  If supplied

    By default, uses a fake Lock which exposes acquisition semantics, but does nothing.  If uses in
    the multithreaded environment, it is recommended that a threading.RLock be used.

    Great care must be taken to ensure that only one lock is held during updates or access (ie. to
    obtain self-consistent value and now times).  If multiples locks can ever be held during access
    of the current value of an object, it will be possible to "deadlock" any program that ever has
    two threads lock the same locks in opposite order.
    """
    __slots__                   = [ 'value', 'now', 'lock' ]

    class NoOpRLock( object ):
        def acquire(self, *args, **kwargs):
            pass
        __enter__ = acquire
        def release(self):
            pass
        def __exit__(self, *args, **kwargs):
            self.release()

    def __init__( self,
                  value         = 0,
                  now           = None,
                  lock          = NoOpRLock()):
        """
        The base constructor initializes the value and time, and if a non-None value is provided,
        uses it for the initial sample invocation.  The default is zero, but None or math.nan is
        appropriate, if the user is prepared to handle non-numeric values until the first sample is
        provided.
        """
        if now is None:
            now                 = timer()
        self.lock               = lock
        with self.lock:
            self.now            = now
            self.value          = value
            if not non_value( value ):
                self.sample( value, now )

    def sample( self,
               value            = None,
               now              = None ):
        """
        The default sample method simply assigns the given value and time.  The new value 
        may be a legitimate float or int value, or a non-value (eg. None or NaN).
        """
        if isinstance( value, self.__class__ ):
            # Another misc.value; we'll compute its current value relative to the timestamp we're
            # given (if None; obtain from other value, holding its lock for consistency)
            with value.lock:
                if now is None:
                    now         = value.now
                value           = value.compute( now=now )
        # Now, update ourself with the (possibly computed) value and time
        if  now is None:
            now                 = timer()
        with self.lock:
            self.now            = now
            self.value  	= value
        return self.value

    def compute( self,
                 now            = None ):
        """
        Compute an updated value, relative to the specified time.  The default method just returns
        the current value.
        """
        return self.value

    # Rich comparison
    def __eq__( self, rhs ):
        if isinstance( rhs, value ):
            return self.value == rhs.value
        return self.value == rhs
    def __ne__( self, rhs ):
        if isinstance( rhs, value ):
            return self.value != rhs.value
        return self.value != rhs

    def __lt__( self, rhs ):
        if isinstance( rhs, value ):
            return self.value < rhs.value
        return self.value < rhs
    def __le__( self, rhs ):
        if isinstance( rhs, value ):
            return self.value <= rhs.value
        return self.value <= rhs

    def __gt__( self, rhs ):
        if isinstance( rhs, value ):
            return self.value > rhs.value
        return self.value > rhs
    def __ge__( self, rhs ):
        if isinstance( rhs, value ):
            return self.value >= rhs.value
        return self.value >= rhs

    # Casts
    def __bool__( self ):
        return bool( self.value )
    def __str__( self ):
        return str( self.value )
    def __int__( self ):
        return int( self.value )
    def __float__( self ):
        return float( self.value )
        
    # Arithmetic operators.  The in-place operators (+=, etc.) use the apply the rhs value as a
    # sample; if the rhs is a misc.value, then it also knows to use the 'now' time.
    def __sub__( self, rhs ):
        return self.value - rhs
    def __rsub__( self, lhs ):
        return lhs - self.value
    def __isub__( self, rhs ):
        if isinstance( rhs, value ):
            self.sample( self.value - rhs.value, rhs.now )
        else:
            self.sample( self.value - rhs )
        return self

    def __add__( self, rhs ):
        return self.value + rhs
    def __radd__( self, lhs ):
        return lhs + self.value
    def __iadd__( self, rhs ):
        if isinstance( rhs, value ):
            self.sample( self.value + rhs.value, rhs.now )
        else:
            self.sample( self.value + rhs )
        return self

    def __mul__( self, rhs ):
        return self.value * rhs
    def __rmul__( self, lhs ):
        return lhs * self.value
    def __imul__( self, rhs ):
        if isinstance( rhs, value ):
            self.sample( self.value * rhs.value, rhs.now )
        else:
            self.sample( self.value * rhs )
        return self

    def __div__( self, rhs ):
        return self.value / rhs
    def __rdiv__( self, lhs ):
        return lhs / self.value
    def __idiv__( self, rhs ):
        if isinstance( rhs, value ):
            self.sample( self.value / rhs.value, rhs.now )
        else:
            self.sample( self.value / rhs )
        return self

    # Various mathematical operators
    def __abs__( self ):
        return abs( self.value )
    def __neg__( self ):
        return -self.value
    def __pos__( self ):
        return +self.value
