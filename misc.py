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
