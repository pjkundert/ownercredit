#!/usr/bin/env python

"""
Filtering functionality used by various other modules.
"""

__author__ 				= "Perry Kundert (perry@kundert.ca)"
__version__				= "$Revision: 45 $"
__date__ 				= "$Date: 2008-09-07 16:29:06 -0600 (Sun, 07 Sep 2008) $"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "GNU General Public License, Version 3 (or later)"

import time
import misc
import math


# 
# averaged		-- Simple average over total specified time period
# weighted		-- Weighted average of individual sample/time periods
# weighted_linear	-- Simple linear weighted average of all samples within period
# 
#     Takes the current value and last average, and returns the new
# average, weighted by the current value and the elapsed time.
# 
            
class averaged( misc.value ):
    """
    Acts like an integer or float, but returns a simple average of values over a time period.
    Samples with identical value/timestamp are ignored.  Using no timestamp (or None) causes the
    class to use the current real time.  Values persist indefinitely 'til replaced by new value(s)
    that are within the time interval window.
    """
    __slots__			= [ 'interval', 'history' ]
    def __init__( self,
                  interval,
                  val		= 0,
                  now		= None ):
        misc.value.__init__( self, val )

        if now is None:
            now			= time.time()

        self.interval		= interval
        self.history		= [ ( val, now ) ]

    def purge( self, now ):
        """
        Discard outdated samples.  May empty history.
        """
        deadline		= now - self.interval
        while len( self.history ) > 0 and self.history[-1][1] <= deadline:
            self.history.pop()

    def compute( self ):
        """
        Return simple average of samples.  Assumes history is not empty, is it will never be so long
        as a sample is added after purge is invoked.  Returns value.
        """
        self.value		= 0
        for v,t in self.history:
            self.value	       += v
        self.value	       /= len( self.history )
        return self.value

    def sample( self,
                value		= None,
                now		= None ):
        """
        Add sample, and re-compute value (simple average, only values within interval).  Should be
        usable without change, if derived classes implement appropriate purge and/or compute
        methods.  Returns newly computed result.  If no value given, uses last value (may raise
        IndexError exception).
        """
        if value is None:
            value		= self.history[0][0]
        if now is None:
            now			= time.time()

        # Reject simple duplicates, so py.test works (calls multiple
        # times on assertion failures, expects no side effects)
        if self.history[0] == ( value, now ):
            return self.value

        self.purge( now )
        self.history.insert( 0, ( value, now ) )
        return self.compute()


class weighted( averaged ):
    """
    Acts like an integer or float in most situations, but returns a time-weighted average of the
    samples presented to it.  Results of adding zero or negative time-interval samples is undefined.
    
    Each pair of values defines minimum and maximum value for the area between them.  Therefore,
    each newly added value contributes to the result, using a simple average of the two values,
    weighted by the time between the two values vs. the total duration.
    """
    def __init__( self,
                  interval,
                  value		= 0,
                  now		= None ):
        averaged.__init__( self, interval, value, now )
        
    def purge( self, now ):
        """
        Discard outdated samples, leaving one that is exactly at or outside the interval window.
        The timestamp of the last value in self.history defines the duration used in computing the
        average, if less than self.interval.  Entries must be in ascending timestamp order.
        """
        deadline		= now - self.interval
        while len( self.history ) > 1 and self.history[-2][1] <= deadline:
            # Second-last value is still at or outside window; discard the last one
            self.history.pop()

    def compute( self ):
        """
        Time-weighted average.  Oldest value (outside interval window) only used for portion
        of interval where no in-window value is available.
        """
        # Determine either the end of the interval, or the oldest supplied value, whichever
        # is latest (highest timestamp).  Remember the oldest known value (may be outside
        # of interval, and hence just clamped its timestamp 'then' to the end of interval).
        # 
        # 
        # v0     v1                  v2          v3
        # |---------- interval ------------|
        #                          then == ^
        #                          last == v3
        # 
        if len( self.history ) < 2 or self.history[0][1] == self.history[-1][1]:
            # Single value, or 0 interval
            self.value		= self.history[0][0]
            return self.value
        
        # We have at least 2 samples; clip off the portion of the difference "outside" interval.
        start			= self.history[0][1]
        offset			= 0					# First value at 0 offset; will *always* end up > 0!
        last			= self.history[0][0]
        then			= offset

        self.value		= 0
        for v,t in self.history[1:]:					# Start with second value
            offset		= start - t
            vclip		= v
            if offset > self.interval:
                # Clip to self.interval, linearly last --> v
                outside		= offset - self.interval
                offset		= self.interval
                vclip	       -= last
                vclip		= vclip * self.interval / offset
                vclip	       += last

            dt			= offset - then
            vavg		= ( last + vclip ) / 2
            if dt >= 0:
                # This value is not in reverse time order; use it
                #print " --> " + str( vavg ) + "(" + str( vclip ) + ") * " + str( dt ),
                self.value     += vavg * dt
                last		= v
                then		= offset

        #print " == " + str( self.value ) + " / " + str( offset ),
        self.value	       /= offset
        #print " == " + str( self.value )
        return self.value


class weighted_linear( averaged ):
    """
    Acts like an integer or float in most situations, but returns a time-weighted linear average of the
    samples presented to it.  Results of adding zero or negative time-interval samples is undefined.
    
    Each value is considered to persist linearly, until a new value is added with a later timestamp.
    Therefore, (perhaps surprisingly) each newly added value doesn't actually influence the result
    'til time has "passed" (the next value is added).
    """
    def __init__( self,
                  interval,
                  value		= 0,
                  now		= None ):
        averaged.__init__( self, interval, value, now )
        
    def purge( self, now ):
        """
        Discard outdated samples, leaving one that is exactly at or outside the interval window.
        """
        deadline		= now - self.interval
        while len( self.history ) > 1 and self.history[-2][1] <= deadline:
            # Second-last value is still at or outside window; discard the last one
            self.history.pop()

    def compute( self ):
        """
        Time-weighted linear average.  Oldest value (outside interval window) only used for portion
        of interval where no in-window value is available; values are considered to persist 'til a
        newer value is supplied.
        """
        # Determine either the end of the interval, or the oldest supplied value, whichever
        # is latest (highest timestamp).  Remember the oldest known value (may be outside
        # of interval, and hence just clamped its timestamp 'then' to the end of interval).
        # 
        # 
        # v0     v1                  v2          v3
        # |---------- interval ------------|
        #                          then == ^
        #                          last == v3
        # 
        if len( self.history ) < 2 or self.history[0][1] == self.history[-1][1]:
            # Single value, or 0 interval (guantees !0 final 'offset', below)
            self.value		= self.history[0][0]
            return self.value

        # We have at least 2 samples; clip off the portion of the difference "outside" interval.
        start			= self.history[0][1]
        offset			= 0					# First value at 0 offset; will *always* end up > 0!
        last			= self.history[0][0]
        then			= offset

        self.value		= 0
        for v,t in self.history[1:]:					# Start with second value
            offset		= start - t
            if offset > self.interval:					# Clip to self.interval
                offset		= self.interval
            dt			= offset - then
            if dt >= 0:
                # This value is not in reverse time order; use it
                # print " --> " + str( v ) + " * " + str( dt ),
                self.value     += v * dt
                last		= v
                then		= offset

        # print " == " + str( self.value ) + " / " + str( offset ),
        self.value	       /= offset
        # print " == " + str( self.value )
        return self.value


class level( misc.value ):
    """
    Filter the incoming values into levels. 

    The minimal configuration requires a normal value (and no
    hysteresis).  Incoming values will be either hi (1) or lo (-1)
    state; only exact matches will be considered in the normal (0)
    state:

            hi
                            o 
normal  0.0 ---------------o---
                          o 
            lo         o o  ^
                      o o  ^|
                      ^    |+-- hi
                      |    +--- normal
                      +-------- lo


        normal = 0.0
        levels = [
          -3.0,
          -1.0,
           1.0,
           3.0
        ]
        hysteresis = .1

            hi hi
        3.0 -------------------
        2.9 . . . . . . . . . .
        
            hi
        1.0 -----------------o-
         .9 . . . . . . . . o .
normal  0.0                o
        -.9 . \ . . . . o o  
       -1.0 ---\-------o-o   ^
            lo  \     o    ^ |
                 \   o     | |
       -2.9 . . . o o . .  | |
       -3.0 -------v-----  | |
      /     lo lo          | |
  levels       ^   ^ ^     | |
               |   | |     | | 
               |   | |     | +- hi
               |   | |     +--- normal - must exceed hysteresis toward normal!
               |   | +--------- lo     - must exceed hysteresis toward normal!
               |   +----------- lo lo
               +--------------- lo
        
        
    """
    def __init__( self,
                  normal	= 0,		# Normal value ==> 2 states (1 hi, -1 lo)
                  hysteresis	= 0,		# Value hysteresis; must exceed toward normal state
                  limits	= None,		# Each level adds a state (0 normal, -2 lo lo, 2 hi hi, ...)
                  interval	= None,		# Time hysteresis; state change even within hysteresis
                  value		= 0,		# Initial value
                  now		= None ):
        if now is None:
            now 		= time.time()
        misc.value.__init__( self, value )
        self.normal             = normal	# The value considered in "normal" level 
        self.limits		= limits or []
        self.hysteresis		= hysteresis
        self.interval		= interval
        self.state		= 0
        self.now		= now
        self.sample( value, now )

    def level( self ):
        return self.state

    def name( self ):
        lvl			= self.level()
        if lvl == 0:
            return "normal"
        return ' '.join( [ lvl < 0 and 'lo' or 'hi' ] * abs( lvl ))

    def sample( self,
                value		= None,
                now		= None ):
        # Compute the limits, for going upwards and downwards
        # 
	# Yes, these will skip normal iff hysteresis > than the
        # distance between the two adjacent states!
        # 
        #     self.limits: [-1, 1]
        # self.hysteresis: .25
        # 
        #              up: [-.75, 1.0]
        #              dn: [-1.0, .75]
        # 
        #          hi_sta:  1
        #          lo_sta: -1

        state			= self.state
        limits			= sorted( self.limits )
        
        up	 		= [ self.normal + lim + ( lim <  0 and self.hysteresis or 0 )
                                    for lim in limits ]
        dn		        = [ self.normal + lim - ( lim >= 0 and self.hysteresis or 0 )
                                    for lim in limits ]

        lo_sta			= -len( [ lim for lim in limits
                                         if lim <  0 ] )
        hi_sta			= lo_sta + len( limits )
        state			= misc.clamp( state, ( lo_sta, hi_sta ))

        #print "state == ", state
        #print "lo_sta == ", lo_sta
        #print "hi_sta == ", hi_sta
        #print up
        #print dn

        # Did we exit our state upwards?
        while state < hi_sta:
            lim = up[state - lo_sta]
            if state < 0:
                # Must exceed limit towards normal
                if value >  lim:
                    state      += 1
                    #print "Value %s exceeds %s, moves us up, to state %s" % (
                    #    value, lim, state )
                else:
                    break
            else:
                # ... only meet it away from normal
                if value >= lim:
                    state      += 1
                    #print "Value %s meets   %s, moves us up, to state %s" % (
                    #    value, lim, state )
                else:
                    break
        # ... or downards?
        while state > lo_sta:
            lim = dn[state - lo_sta - 1]
            if state > 0:
                if value <  lim:
                    state      -= 1
                    #print "Value %s exceeds %s, moves down,  to state %s" % (
                    #    value, lim, state )
                else:
                    break
            else:
                if value <= lim:
                    state      -= 1
                    #print "Value %s meets   %s, moves down,  to state %s" % (
                    #    value, lim, state )
                else:
                    break

        if ( state != self.state
             or value > self.value + self.hysteresis
             or value < self.value - self.hysteresis ):
            self.value		= value
            self.state		= state

        self.now		= now
        return self.value


# 
# filter	-- filter values over time
# 
#     Takes the current value and last average, and returns the new
# average, weighted by the current value and the elapsed time.
# 
#     Optionally specify time-weighted averages by specifying a
# non-'nan' value for weighted, which will also serve as the initial
# interval's value.
# 
#     The relevant time-range of values is between now and
# now-interval, exclusive: (now, now-interval]
# 
#     In other words, if interval == 10, and you insert 4 values, that
# last at time now == 100:
# 
#         [ ( 3, 100 ), ( 2, 94 ), ( 1, 91 ), ( 0, 90 ) ]
# 
# then the latest three values 3, 2 and 1 will be included in the
# simple filter with equal weight, while the oldest 3 values 2, 1 and
# 0 will be included in the time-weighted average, with weights 0 * 1,
# 1 * 3, and 2 * 6.  The most recent value discarded ( 0 ) becomes the
# new self.weighted, so that its value "persists" until replaced by
# the next value within the interval.
# 
# WARNING
# 
#     Simple filtering (scalar window) treats each value as if it was
# an average value across an identical period of time with each other
# value, thus rejecting the oldest value that just fell out of the
# time window, and including the latest.  Time-weighted averaging
# (interval,value tuple window) treats each value as if it were the
# value for the duration beginning at its timestamp, 'til the next
# value.  Therefore, the oldest value discarded is remembered (as its
# value extends into the end of the window), and the newest value is
# not used (as it has a 0. duration).
# 
#     Therefore, the latest value added will *not* influence the
# time-weighted average, but the oldest (just discarded) value
# *will*..  This may be surprising to most users, but makes sense when
# you consider it.  If a value has a certain known persistence, you
# may want to enter it twice -- first with a timestamp indicating when
# it took effect, and once more with the current timestamp, to get its
# effect on the output value.
# 
#     Basically, if you use identically spaced samples, then simple
# filtering treats the samples as the value over the period *ending*
# at the given timestamp, while time-weighted filtering treats the
# samples as the value at the *beginning* at the given timestamp.
# 
#     Result of get() indeterminate 'til first sample added...
# 
# SUMMARY
# 
# 
#     Overall, too complex (mixes simple/time average), and must be
# explicitly supported by the target.  Use 'averaged' and derived
# classes, which act like integers or floats (and can often be used as
# such), but implement similar filtering features.
# 
class filter( object ):
    def __init__( self,
                  interval,				# May be a scalar interval, or tuple/list of interval, initial value
                  now		= None ):
        if now is None:
            now			= time.time()
        try:						# Changing will take effect after next 'add'
            self.interval	= interval[0]		# The filter window interval
            self.weighted	= interval[1]		# Latest value to pass beyond time interval window
        except:
            self.interval	= interval
            self.weighted	= math.nan

        self.now		= now

        self.history		= []
        if not self.interval and not( math.isnan( self.weighted )):
            # Zero timed weighting w/initial value; could be non-zero later, but make it work initially
            self.history.insert( 0, ( self.weighted, self.now ))
        self.sum		= 0.
        
    def get( self ):
        if math.isnan( self.weighted ):
            return self.sum / len( self.history )

        if self.interval:				# time-weighted...
            return self.sum / self.interval
        return self.history[0][0]			# but interval set to 0.!  Return instaneous value.

    def add( self,
             value,
             now		= None ):
        if now is None:
            now			= time.time()

        # Reject simple duplicates, so py.test works (calls multiple
        # times on assertion failures, expects no side effects)
        if len( self.history ):
            if self.history[0] == ( value, now ):
                return self.get();

        # Purge dead values.  The oldest one discarded becomes the
        # current self.weighted (if non-'nan').  As soon as a value
        # reaches the end of the window, it is discarded.
        dead			= now - self.interval
        while len( self.history ) and self.history[-1][1] <= dead:
            if not math.isnan( self.weighted ):
                if not math.isnan( self.history[-1][0] ):
                    self.weighted = self.history[-1][0]
            self.history.pop()

        # Save new value
        self.history.insert( 0, ( value, now ) )

        # Compute time-weighted or simple average of remaining values
        self.sum		= 0.
        if math.isnan( self.weighted ):
            # Simple average
            for v,t in self.history:
                self.sum       += v
        else:
            # Time-weighted.  If multiple values at same time, latest is used.
            # Out-of-order values discarded.
            then		= self.history[0][1] - self.interval
            last		= self.weighted
            for v,t in reversed( self.history ):
                dt		= t - then
                if dt >= 0:
                    self.sum   += last * dt
                    last	= v
                    then	= t

        return self.get()
