#!/usr/bin/env python

"""
Miscellaneous functionality used by various other modules.
"""

__author__ 				= "Perry Kundert (perry@kundert.ca)"
__version__ 				= "$Revision$"
__date__ 				= "$Date$"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "GNU General Public License, Version 3 (or later)"

import math
import time

# Augment math with some useful constants
math.nan			= float( 'nan' )

def near( a, b, significance = 1.0e-4 ):

    """ Returns True iff the difference between the values is within the factor 'significance' of
    one of the original values.  Default is to within 4 decimal places. """

    return abs( a - b ) <= significance * abs( a and a or b )

# clamp a value to a tuple of limits.
# 
#     Limits that are math.nan are automatically ignored, with no special code.
# 
def clamp( val, lim ):
    """ Limit val to between 2 (optional, if nan) limits """
    if ( val < lim[0] ):
        return lim[0]
    if ( val > lim[1] ):
        return lim[1]
    return val

# filter
# 
#     Takes the current value and last average, and returns the new
# average, weighted by the current value and the elapsed time.
# 
def weighted( val, dt, avg, period ):
    """ Returns the average with the delta-time weighted new value """
    if dt >= period:
        return val
    fraction			= dt / period
    return (   val *        fraction
             + avg * ( 1. - fraction ))

class filter:
    def __init__( self,
                  interval,
                  now		= time.time() ):
        self.interval		= interval		# Changing will take effect after next 'add'
        self.now		= now
        self.history		= [  ]
        self.sum		= 0.
        
    def get( self ):
        return self.sum / len( self.history )

    def add( self,
             value,
             now		= time.time() ):
        # Purge dead values
        dead			= now - self.interval
        while len( self.history ) and self.history[-1][1] < dead:
            self.history.pop()

        # Save new value
        self.history.insert( 0, ( value, now ) )

        # Return average of remaining values
        self.sum		= 0.
        for v,t in self.history:
            self.sum	       += v
        return self.sum / len( self.history )
            
        

# 
# linear	-- linear motion
# 
#     Compute linear motion between 2 values.
# 
def linear( start, end, begin, finish, now ):
    distance			= end - start
    duration			= finish - begin
    elapsed			= now - begin

    if elapsed < 0:
        return start
    if elapsed < duration:
        fraction		= float( elapsed ) / duration
        return start + distance * fraction
    return end
