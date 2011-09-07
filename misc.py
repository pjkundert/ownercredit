#!/usr/bin/env python

"""
Miscellaneous functionality used by various other modules.
"""

__author__                              = "Perry Kundert (perry@kundert.ca)"
__version__                             = "$Revision: 45 $"
__date__                                = "$Date: 2008-09-07 16:29:06 -0600 (Sun, 07 Sep 2008) $"
__copyright__                           = "Copyright (c) 2006 Perry Kundert"
__license__                             = "GNU General Public License, Version 3 (or later)"

import math
import timeit

# 
# misc.timer
# 
# Select platform appropriate timer function
timer = timeit.default_timer

# 
# misc/math.nan -- IEEE NaN (Not a Number)
# misc/math.isnan -- True iff the provided value is math.nan
# 
#     Augment math with some useful constants.  Note that IEEE NaN is the
# only floating point number that won't equal itself.
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
    result 			= ( rng[0]
                                    + ( val    - dom[0] )
                                    * ( rng[1] - rng[0] )
                                    / ( dom[1] - dom[0] ))
    if clamped:
        result			= clamp( result, (min(rng), max(rng)))
    return result

# 
# magnitude     -- Return the approximate base magnitude of the value, in 'base' ( 10 )
#
#     Handy for computing up/down modifiers for values.  For example:
#
#      23 ==> 1.
#     .23 ==>  .1
# 
def magnitude( val, base = 10 ):
    return pow( base, round( math.log( val ) / math.log( base )) - 1 )


# 
# misc.value    -- Base class for things that should generally act like a float/int
# 
class value( object ):
    """
    Acts like an integer or float in most use cases.  Use as a base class for things that want to
    have a simple integer or float value type interface for arithmetic expressions.  Also handles
    several non-values correctly:

        None    If supplied
        

        math.nan

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
            if value not in (None, math.nan):
                self.sample( value, now )

    def sample( self,
               rhs              = None,
               now              = None ):
        """
        The default sample method simply assigns the given value and time.  If no new value is
        provided, the existing one is retained (eg. if used to just advance the 'now' time)
        """
        if isinstance( rhs, value ):
            # Another misc.value, then we'll compute its current value relative to the timestamp
            # we're given (if None; obtain from other value, holding its lock for consistency)
            with rhs.lock:
                if now is None:
                    now         = rhs.now
                rhs		= rhs.compute( now=now )
        # Now, update ourself with the (possibly computed) value and time
        if  now is None:
            now                 = timer()
        with self.lock:
            self.now            = now
            if rhs is not None:
                self.value      = rhs
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
            self.sample( self.value + rhs.value, now )
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
