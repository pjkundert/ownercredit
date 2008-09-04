#!/usr/bin/env python

"""
Miscellaneous functionality used by various other modules.
"""

__author__ 				= "Perry Kundert (perry@kundert.ca)"
__version__ 				= "$Revision$"
__date__ 				= "$Date$"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "GNU General Public License, Version 3 (or later)"

from math import *

def near( a, b, significance = 1.0e-4 ):

    """ Returns True iff the difference between the values is within the factor 'significance' of
    one of the original values.  Default is to within 4 decimal places. """

    return abs( a - b ) <= significance * abs( a and a or b )

def clamp( val, lim ):
    """ Limit val to between 2 (optional) limits """
    if (( lim[0] or type( lim[0] ) != bool ) and val < lim[0] ):
        val		= lim[0]
    if (( lim[1] or type( lim[1] ) != bool ) and val > lim[1] ):
        val		= lim[1]
    return val

# Compute a smoothly accelerating then decelerating path between 2 values.
# Just fake it by computing the proportion of the square of the distance from each end, taking
# the minimum and then the root.

def updown( start, end, begin, finish, now ):
    distance			= end - start
    duration			= finish - begin
    elapsed			= now - begin

    halftime			= duration / 2
    if elapsed < 0:
        return start
    if elapsed < duration:
        fraction		= float( elapsed ) / duration
        return start + distance * ((( fraction * fraction ) - (( 1. - fraction ) * ( 1. - fraction ))) + 1. ) / 2
    return end
    
