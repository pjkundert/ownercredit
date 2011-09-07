#!/usr/bin/env python

"""
Filtering functionality used by various other modules.
"""

__author__                              = "Perry Kundert (perry@kundert.ca)"
__version__                             = "$Revision: 45 $"
__date__                                = "$Date: 2008-09-07 16:29:06 -0600 (Sun, 07 Sep 2008) $"
__copyright__                           = "Copyright (c) 2006 Perry Kundert"
__license__                             = "GNU General Public License, Version 3 (or later)"

import misc
import math
import collections

# 
# averaged              -- Simple average over total specified time period
# weighted              -- Weighted average of individual sample/time periods
# weighted_linear       -- Simple linear weighted average of all samples within period
# 
#     Evaluates and returns the new average, optionally weighted by the current value and the
# elapsed time.
# 
#     Handles an intial value (or None, representing no samples yet).  Also handles samples of NaN,
# indicating that a problem occured and there are no new samples available; in this case, when the
# averaging interval expires, the result will revert to NaN.  Otherwise, it will retain the last
# known value.
            
class averaged( misc.value ):
    """
    Acts like an integer or float, but returns a simple average of values over a time period.
    Samples with identical value/timestamp are ignored.  Using no timestamp (or None) causes the
    class to use the current real time.  Values persist indefinitely 'til replaced by new value(s)
    that are within the time interval window.
    """
    __slots__                   = [ 'interval', 'history' ]
    def __init__( self,
                  interval,
                  value         = 0,
                  now           = None,
                  lock          = misc.value.NoOpRLock()):

        self.interval           = interval
        self.history            = collections.deque()

        # Initial sample
        misc.value.__init__( self, value, now, lock )

    def purge( self ):
        """
        Discard outdated samples, leaving one that is exactly at or outside the interval window.
        The timestamp of the last value in self.history defines the duration used in computing the
        average, if less than self.interval.  Entries must be in ascending timestamp order.
        """
        with self.lock:
            deadline            = self.now - self.interval
            while len( self.history ) > 1 and self.history[-2][1] <= deadline:
                # Second-last value is still at or outside window; discard the last one
                self.history.pop()

    def compute( self,
                 now            = None ):
        """
        Return simple average of samples.  Recomputes value if history is not empty, is it will
        never be so long as a sample is added after purge is invoked.  Returns value (without
        recomputing if history is empty of relevant values.)

        Simple average uses the exclusive range, to retain the idea of an integer interval value
        only containing up to its own number of samples.  Note that our 'purge' method may retain
        unnecessary samples, for more complex (derived) averaging methods.
        """
        with self.lock:
            if now is None:
                now             = self.now
            value               = 0
            count               = 0
            for v,t in self.history:
                if t > now - self.interval:
                    # sample is within (now, now-interval]; use it.
                    value      += v
                    #print " --> + " + str( v ),
                else:
                    break
                count          += 1
            if count:
                #print " == " + str( value ) + " / " + str( count ),
                value          /= count
            else:
                # No relevant history...
                if not self.history or math.isnan( self.value ):
                    # No history at all, or last computed value has been set to NaN; retain.
                    #print " (no history) "
                    value       = self.value
                else:
                    # We do have history, and a valid computed value.  Retain historical value.
                    #print " (historical) "
                    value       = self.history[0][0]
            #print " == " + str( value )
        return value

    def sample( self,
                value           = None,
                now             = None ):
        """
        Add sample, and re-compute value (simple average, only values within interval).  Should be
        usable without change for derived classes that use this history mechanism, if derived
        classes implement appropriate purge and/or compute methods.  Returns newly computed result.
        If None value provided, uses last value (may raise IndexError exception).
        """
        if isinstance( value, misc.value ):
            # Another misc.value, then we'll compute its current value relative to the timestamp
            # we're given (if None; obtain from other value, holding its lock for consistency)
            with value.lock:
                if now is None:
                    now         = value.now
                value           = value.compute( now=now )
        else:
            # No lock required; single value, atomic access
            if value is None:
                value           = self.history[0][0]
            if now is None:
                now             = misc.timer()

        # We cannot allow revision of history, but multiple samples at the same instant is OK
        if now < self.now:
            raise ZeroDivisionError( "Invalid sample; attempting to use out-of-order 'now' time value" )

        # Reject simple duplicates, so py.test works (calls multiple times on assertion failures,
        # expects no side effects).  No lock required; self.history is not allowed to disappear, and 
        # tuples are immutable
        if self.history and self.history[0] == ( value, now ):
            return self.value

        # Lock required to ensure consistent multi-step update.  Updating with a NaN will update our
        # time, but will not contaminate our history.  In other words, it will indicate a problem
        # with the value, but when corrected, correct computation of values will resume.
        with self.lock:
            self.now            = now
            self.purge()

            if value is None or misc.isnan( value ):
                # A non-numeric, but allowed value.  Remember it; we may use it or overwrite it, if
                # valid history remains to compute a more appropriate value..
                self.value      = value
            else:
                # Otherwise, encode the sample in history.
                self.history.appendleft( ( value, now ) )

            self.value          = self.compute()
            return self.value


class weighted( averaged ):
    """
    Acts like an integer or float in most situations, but returns a time-weighted average of the
    samples presented to it.  Results of adding zero or negative time-interval samples is undefined.
    
    Each pair of values defines minimum and maximum value for the area between them.  Therefore,
    each newly added value contributes to the result immediately, using a simple average of the two
    values, weighted by the time between the two values vs. the total duration.

    Note that this will make the output non-continuous, over time -- adding a new sample will result
    in large jumps in output value, because the new value influences the effective value over the
    entire range of time between the current and previous sample!
    """
    def __init__( self,
                  interval,
                  value         = 0,
                  now           = None,
                  lock          = averaged.NoOpRLock()):
        averaged.__init__( self, interval, value, now, lock )
        
    def compute( self,
                 now           = None ):
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
        # If no history is available (no samples), then return value unchanged.  This should be
        # None, if that was what was supplied at initialization.
        with self.lock:
            if now is None:
                now             = self.now
            if not self.history or now - self.interval > self.history[0][1]:
                if self.value is None or math.isnan( self.value ):
                    # No history, or expired, and our last sample is NaN/None; retain value
                    return self.value
            if not( now >= self.history[0][1]
                    and now > self.history[-1][1] ):
                # No net offset between now and first/last historical value; we only have single
                # usable historical value.
                return self.history[0][0]
            
            # We have at least one non-empty sample period; clip off the portion of the difference
            # "outside" interval.
            start               = now
            last                = self.history[0][0]
            offset              = 0                     # First value at 0 offset; will *always* end up > 0!
            then                = offset
            
            value               = 0
            for v,t in self.history:
                offset          = start - t
                vclip           = v
                if offset > self.interval:
                    # Clip to self.interval, linearly last --> v
                    outside     = offset - self.interval
                    offset      = self.interval
                    vclip      -= last
                    vclip       = vclip * self.interval / offset
                    vclip      += last
            
                dt              = offset - then
                vavg            = ( last + vclip ) / 2
                if dt >= 0:
                    # This value is not in reverse time order; use it
                    #print " --> " + str( vavg ) + "(" + str( vclip ) + ") * " + str( dt ),
                    value      += vavg * dt
                    last        = v
                    then        = offset
            
            #print " == " + str( value ) + " / " + str( offset ),
            value         /= offset
            #print " == " + str( value )
            return value


class weighted_linear( averaged ):
    """
    Acts like an integer or float in most situations, but returns a time-weighted linear average of the
    samples presented to it.  Results of adding zero or negative time-interval samples is undefined.
    
    Each value is considered to persist linearly, until a new value is added with a later timestamp.
    Therefore, (perhaps surprisingly) each newly added value doesn't actually influence the result
    'til time has "passed" (eg. time is advanced when the next value is added).

    This form of weighted average is more what is normally expected; over the duration of the
    interval, the result will gradually reflect more of the new sample, and less of the old.
    """
    def __init__( self,
                  interval,
                  value         = 0,
                  now           = None,
                  lock          = averaged.NoOpRLock()):
        averaged.__init__( self, interval, value, now, lock )
        
    def compute( self,
                 now            = None ):
        """
        Time-weighted linear average.  Oldest value (outside interval window) only used for portion
        of interval where no in-window value is available; values are considered to persist 'til a
        newer value is supplied.  If now is supplied, computes relative to that instant, instead of
        self.now.

        By considering the initial sample to be now and the most recent historical value, we can
        avoid specially handling the first history entry.
        

        Does not alter self.value (or any other attribute), but takes the lock to ensure consistency.
        """
        # Determine either the end of the interval, or the oldest supplied value, whichever
        # is latest (highest timestamp).  Remember the oldest known value (may be outside
        # of interval, and hence just clamped its timestamp 'then' to the end of interval).
        # 
        # 
        # .history entries:                   final
        #                                   v--dt--v------3
        #                                          |   
        #           ------1                        |
        #                  -----------------2      |
        #         0                                |      
        #         |---------- interval ------------|
        # ^---dt--^                        then == ^
        # now B   now A                    last == 3
        # 
        # If now (A) is coincident with history[0], that value will not be represented (dt == 0 in
        # initial loop).  If now is future (B), then the initial dt will reflect the 0'th value.
        # 
        # Handles no history, returning value unchanged.
        with self.lock:
            if now is None:
                now             = self.now
            if not self.history or now - self.interval > self.history[0][1]:
                if self.value is None or math.isnan( self.value ):
                    # No history, or expired, and our last sample is NaN/None; retain value
                    return self.value
            if not( now >= self.history[0][1]
                    and now > self.history[-1][1] ):
                # Good value and history, but no net offset between now and first/last historical
                # value; we only have single usable historical value.
                return self.history[0][0]
            
            # We have at least 2 samples and a non-empty range within self.interval; clip off the
            # portion of the difference "outside" interval.
            start               = now
            offset              = 0                     # First value at 0 offset; must *always* end up > 0!
            then                = offset
            
            value               = 0
            for v,t in self.history:
                offset          = start - t
                if offset > self.interval:              # Clip to self.interval
                    offset      = self.interval
                dt              = offset - then
                if dt >= 0:
                    # This value is not in reverse time order; and is at least partially within the
                    # interval; use it
                    
                    #print " --> " + str( v ) + " * " + str( dt ),
                    value      += v * dt
                    then        = offset
            
            #print " == " + str( value ) + " / " + str( offset ),
            value              /= offset
            #print " == " + str( value )
            return value


class level( misc.value ):
    """
    Filter the incoming values into levels. 

    The minimal configuration requires a normal value (and no hysteresis).  Incoming values will be
    either normal (0) or lo (-1) state; somewhat oddly, though, a value exaclty at the limit
    (eg. offset [0] from normal, the default) will drive us into the "lo" level!  Remember, we must
    only "meet" the limit when moving away from normal, but must "exceed" it when moving toward
    normal.


            normal
                            o 
normal  0.0 ---------------o---
                          o 
            lo         o o  
                      o o   ^
                      ^     |
                      |     +-- normal
                      +-------- lo

                      

    Here is a 5-state alarm example:

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
    __slots__                   = [ 'normal', 'limits', 'hysteresis', 'interval', 'state' ]
    def __init__( self,
                  normal        = 0,            # Normal value ==> 2 states (1 hi, -1 lo)
                  hysteresis    = 0,            # Value hysteresis; must exceed toward normal state
                  limits        = None,         # Each level adds a state (0 normal, -2 lo lo, 2 hi hi, ...)
                  interval      = None,         # Time hysteresis; state change even within hysteresis
                  value         = 0,            # Initial value
                  now           = None,
                  lock          = misc.value.NoOpRLock()):
        self.normal             = normal        # The value considered in "normal" level 
        self.hysteresis         = hysteresis
        self.limits             = limits or [0] # The default with no limits is "normal" and "lo"
        self.interval           = interval
        self.state              = 0

        # Invokes the initial sample(...)
        misc.value.__init__( self, value, now, lock )

    def level( self ):
        return self.state

    def name( self ):
        lvl                     = self.level()
        if lvl == 0:
            return "normal"
        return ' '.join( [ lvl < 0 and 'lo' or 'hi' ] * abs( lvl ))

    def sample( self,
                value           = None,
                now             = None ):
        # Compute the limits, for going upwards and downwards
        # 
        # Yes, these will skip normal iff hysteresis > than the distance between the two adjacent
        # states!
        # 
        #     self.limits: [-1, 1]
        # self.hysteresis: .25
        # 
        #              up: [-.75, 1.0]
        #              dn: [-1.0, .75]
        # 
        #          hi_sta:  1
        #          lo_sta: -1
        if isinstance( value, misc.value ):
            with value.lock:
                value               = value.value
                if now is None:
                    now             = value.now
        else:
            if value is None:
                value           = self.value
            if now is None:
                now             = misc.timer()

        with self.lock:
            state               = self.state
            limits              = sorted( self.limits )
            
            up                  = [ self.normal + lim + ( lim <= 0 and self.hysteresis or 0 )
                                    for lim in limits ]
            dn                  = [ self.normal + lim - ( lim >  0 and self.hysteresis or 0 )
                                    for lim in limits ]
            
            lo_sta              = -len( [ lim for lim in limits
                                         if lim <= 0 ] )
            hi_sta              = lo_sta + len( limits )
            state               = misc.clamp( state, ( lo_sta, hi_sta ))
            
            '''
            print "state == ", state
            print "lo_sta == ", lo_sta
            print "hi_sta == ", hi_sta
            print up
            print dn
            '''
            
            # Did we exit our state upwards?
            while state < hi_sta:
                lim = up[state - lo_sta]
                if state < 0:
                    # Must exceed limit towards normal
                    if value >  lim:
                        state  += 1
                        #print "Value %s exceeds %s, moves us up, to state %s" % (
                        #    value, lim, state )
                    else:
                        break
                else:
                    # ... only meet it away from normal
                    if value >= lim:
                        state  += 1
                        #print "Value %s meets   %s, moves us up, to state %s" % (
                        #    value, lim, state )
                    else:
                        break
            # ... or downards?
            while state > lo_sta:
                lim = dn[state - lo_sta - 1]
                if state > 0:
                    if value <  lim:
                        state  -= 1
                        #print "Value %s exceeds %s, moves down,  to state %s" % (
                        #    value, lim, state )
                    else:
                        break
                else:
                    if value <= lim:
                        state  -= 1
                        #print "Value %s meets   %s, moves down,  to state %s" % (
                        #    value, lim, state )
                    else:
                        break
            
            if ( state != self.state
                 or value > self.value + self.hysteresis
                 or value < self.value - self.hysteresis ):
                self.value      = value
                self.state      = state
            
            self.now            = now
            return self.value


# 
# filter        -- filter values over time
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
                  interval,                             # May be a scalar interval, or tuple/list of interval, initial value
                  now           = None ):
        if now is None:
            now                 = misc.timer()
        try:                                            # Changing will take effect after next 'add'
            self.interval       = interval[0]           # The filter window interval
            self.weighted       = interval[1]           # Latest value to pass beyond time interval window
        except:
            self.interval       = interval
            self.weighted       = math.nan

        self.now                = now

        self.history            = collections.deque()
        if not self.interval and not( math.isnan( self.weighted )):
            # Zero timed weighting w/initial value; could be non-zero later, but make it work initially
            self.history.appendleft( ( self.weighted, self.now ) )
        self.sum                = 0.
        
    def get( self ):
        if math.isnan( self.weighted ):
            return self.sum / len( self.history )

        if self.interval:                               # time-weighted...
            return self.sum / self.interval
        return self.history[0][0]                       # but interval set to 0.!  Return instaneous value.

    def add( self,
             value,
             now                = None ):
        if now is None:
            now                 = misc.timer()

        # Reject simple duplicates, so py.test works (calls multiple
        # times on assertion failures, expects no side effects)
        if len( self.history ):
            if self.history[0] == ( value, now ):
                return self.get();

        # Purge dead values.  The oldest one discarded becomes the
        # current self.weighted (if non-'nan').  As soon as a value
        # reaches the end of the window, it is discarded.
        dead                    = now - self.interval
        while len( self.history ) and self.history[-1][1] <= dead:
            if not math.isnan( self.weighted ):
                if not math.isnan( self.history[-1][0] ):
                    self.weighted = self.history[-1][0]
            self.history.pop()

        # Save new value
        self.history.appendleft( ( value, now ) )

        # Compute time-weighted or simple average of remaining values
        self.sum                = 0.
        if math.isnan( self.weighted ):
            # Simple average
            for v,t in self.history:
                self.sum       += v
        else:
            # Time-weighted.  If multiple values at same time, latest is used.
            # Out-of-order values discarded.
            then                = self.history[0][1] - self.interval
            last                = self.weighted
            for v,t in reversed( self.history ):
                dt              = t - then
                if dt >= 0:
                    self.sum   += last * dt
                    last        = v
                    then        = t

        return self.get()
