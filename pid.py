#!/usr/bin/env python

"""
pid.controller	-- PID loop controller

    Implements a PID loop controller.  Controls an output value based on the input value's velocity
and acceleration (change and rate of change) away from a setpoint.

    PID contants are provided in Kpid = ( Kp, Ki, Kd ), and specify what proportion of each
error component should be fed back into computing the output.

        Kp -- amount of latest error should be fed back into output
        Ki -- amount of total error integral (sum of errors) should be fed back into output
        Kd -- amount of the last error derivative (rate of change) to included in output

    Depending on the relationship between the setpoint/value and the output, these factors will need
to be tuned.
"""

__author__ 			= "Perry Kundert (perry.kundert@enbridge.com)"
__version__ 			= "$Revision: 1.2 $"
__date__ 			= "$Date: 2006/05/10 16:51:11 $"
__copyright__			= "Copyright (c) 2008 Perry Kundert"
__license__			= "GNU General Public License V3 (or higher)"

import time
import filtered
from misc import *

# 
# pid.controller-- Collect error and adjust output to compensate
# 
#     Implements a PID control loop, but acts like a simple integer or float value
# in most use cases.
# 
class controller:
    """
    Modulates output based on error between current value and desired setpoint.

    """
    def __init__( self,
                  Kpid 		= ( 1.0, 1.0, 1.0 ),			# PID loop constants
                  Fset		= ( 0.0, math.nan ),			# Filter setpoint and/or input valus over simple averaged interval
                  Finp		= ( 0.0, math.nan ),			#  or, (optionally) time-weighted w/ non-NaN initial value
                  Li		= ( math.nan, math.nan ),		# Limit integral (anti-windup)
                  Lout		= ( math.nan, math.nan ),		# Limit output (anti-saturation)
                  now		= None ):
        """
        Given the initial PID loop constants Kpid, setpoint, input and target output, computes the
        appropriate instantaneous I (Integral) and D (Derivative) to yield the target output.  This
        means that, so long as the error term (setpoint - input) doesn't change, the output value
        won't change.

        If set of output limits are provided, then the Integral will automatically be limited
        """
        if now is None:
            now			= time.time()

	self.set		= filtered.filter( Fset, now )			# Optionally time-weighted filtering w/ non-NaN initial values
        self.inp		= filtered.filter( Finp, now )
        self.out		= 0.					# Raw output, before clamping to Lout
        
        self.Finp		= Finp
        self.Fset		= Fset
        self.Kpid		= Kpid
        self.Li			= Li		# Integral anti-wind-up (eg. output saturated, doesn't reduce error term)
        self.Lout		= Lout		# Output limiting (eg. output saturated)

        self.now		= now		# Last time computed
        self.err		= 0.		#   with this error term
	self.I			= 0.		#   and integral of error over time
        self.D			= 0.		# Remember for dt == 0. case...

        self.err		= 0.		# Assume we are at setpoint

    def loop( self,
              setpt,				# Current setpoint
              value,				# Current value
              now 		= None ):
        if now is None:
            now			= time.time()
        dt			= now - self.now
        if dt > 0:
            # New input, setpoint and error term only contribute if time has elapsed!  Get the
            # filtered value.  Simple or time-weighted selected at construction.
            inp			= self.inp.add( value, now )
            sep			= self.set.add( setpt, now )
            err			= sep - inp

            # Avoid integral wind-up by clamping to range limits Li
            self.I		= clamp( self.I + err * dt, self.Li )
            self.D		= ( err - self.err ) / dt
            self.err		= err
            self.now		= now

            self.out		= (      err * self.Kpid[0]
                                    + self.I * self.Kpid[1]
                                    + self.D * self.Kpid[2] )
        return clamp( self.out, self.Lout )

    # Supply the basic behaviours of an integer or float value.
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


# 
# pid.pid	-- Collect error and adjust output to compensate, using explicitly supplied constraints
# 
# WARNING
# 
#     This original implementation of a PID loop used explicitly supplied constraints to
# (optionally) filter various input and output parameters.  This turned out to be clumsy.  Use
# pid.controller instead.
# 
class pid:
    """
    Modulates output based on error between current value and desired setpoint.

    The setpoint and input can optionally be filtered (averaged) over a time period, by providing
    non-zero Finp/Fset.  In addition, time-weighted filtering can be selected by providing a non-NaN
    initial value for setpt and/or value.  Otherwise, simple averaging is used over the time period
    (fine, if identical time sample periods are used; responds quicker to new values, but won't
    provide a smooth ramp on start-up).
    
    """
    def __init__( self,
                  Kpid 		= ( 1.0, 1.0, 1.0 ),			# PID loop constants
                  Fset		= ( 0.0, math.nan ),			# Filter setpoint and/or input valus over simple averaged interval
                  Finp		= ( 0.0, math.nan ),			#  or, (optionally) time-weighted w/ non-NaN initial value
                  Li		= ( math.nan, math.nan ),		# Limit integral (anti-windup)
                  Lout		= ( math.nan, math.nan ),		# Limit output (anti-saturation)
                  now		= None ):
        if now is None:
            now			= time.time()

	self.set		= filtered.filter( Fset, now )			# Optionally time-weighted filtering w/ non-NaN initial values
        self.inp		= filtered.filter( Finp, now )
        self.out		= 0.					# Raw output, before clamping to Lout
        
        self.Finp		= Finp
        self.Fset		= Fset
        self.Kpid		= Kpid
        self.Li			= Li		# Integral anti-wind-up (eg. output saturated, doesn't reduce error term)
        self.Lout		= Lout		# Output limiting (eg. output saturated)

        self.now		= now		# Last time computed
        self.err		= 0.		#   with this error term
	self.I			= 0.		#   and integral of error over time
        self.D			= 0.		# Remember for dt == 0. case...

        self.err		= 0.		# Assume we are at setpoint

    def loop( self,
              setpt,				# Current setpoint
              value,				# Current value
              now 		= None ):
        if now is None:
            now			= time.time()
        dt			= now - self.now
        if dt > 0:
            # New input, setpoint and error term only contribute if time has elapsed!  Get the
            # filtered value.  Simple or time-weighted selected at construction.
            inp			= self.inp.add( value, now )
            sep			= self.set.add( setpt, now )
            err			= sep - inp

            # Avoid integral wind-up by clamping to range limits Li
            self.I		= clamp( self.I + err * dt, self.Li )
            self.D		= ( err - self.err ) / dt
            self.err		= err
            self.now		= now

            self.out		= (      err * self.Kpid[0]
                                    + self.I * self.Kpid[1]
                                    + self.D * self.Kpid[2] )
        return clamp( self.out, self.Lout )

def message( window, text, row = 23 ):
    window.move( row, 0 )
    window.clrtoeol()
    window.addstr( row, 5, text )


def ui( win, title = "Test" ):
    # Run a little rocket up to 25m, and then station-keep

    rows, cols			= win.getmaxyx()

    timewarp			= 1.0					# Slow down real-time by this factor
    increment			= 0.1					# Process no time change increments smaller than this

    g				= -9.81					# m/s^2
    mass			= 1.					# kg
    platform			= 0.0					# m, height of launch pad
    goal			= platform + rows / 4.			# m

    Kpid			= (    5.0,      1.0,     2.0   )	# PID loop tuning
    #Lout			= ( math.nan, math.nan )		# No -'ve thrust available, limit +'ve? Causes integral wind-up and overshoot
    #Lout			= (    0.0,     50.0   )
    #Lout			= (    0.0,   math.nan )
    #Lout			= (    0.0,    100.0   )
    Lout			= (    0.0,    mass * 100.0   )

    #Li				= ( math.nan, math.nan )
    Li				= (    0.0,   math.nan )
    #Li				= (    0.0,    100.0   ) 		# error integral limits; avoiding integral loading causes uncorrected error?

    #Ly				= ( math.nan, math.nan )		# Lauch pad height
    Ly				= ( platform, math.nan )		# Lauch pad height


    a0				= 0.0
    v0				= 0.0
    y0				= platform
    thrust			= 0.0					# N (kg.m/s^2)

    Fset			= ( 1.0, platform )			# Filter setpoint?
    Finp			= ( 0.0, math.nan )			#   or input?

    now				= 0.0
    autopilot			= pid( Kpid, Fset, Finp, Li, Lout, now )
    #autopilot.I			= - g / Kpid[1]				# Pre-load integral for static balanced thrust
    start			= autopilot.now

    last			= time.time()
    while 1:
        message( win, "Quit [qy/n]?, Timewarp:% 7.2f [W/w], Increment:% 7.2f, Filter setp.:% 7.2f[S/s], value:% 7.2f[V/v]"
                 % ( timewarp, increment, autopilot.set.interval, autopilot.inp.interval ),
                 row = 0 )
        win.refresh()
        input			= win.getch()

        # Compute time advance, after time warp
        real			= time.time()
        delta			= ( real - last ) / timewarp
        last			= real

        now		       += delta

        rows, cols		= win.getmaxyx()

        if input >= 0 and input <= 255:
            if chr( input ) == 'y' or chr( input ) == 'q':
                break

            if chr( input ) == 'S':
                autopilot.set.interval += .1
            if chr( input ) == 's':
                autopilot.set.interval -= .1
                if autopilot.set.interval - .0999 < 0.:			# Ensure we don't go "tiny" (eg. 0.0000000001232)
                    autopilot.set.interval = 0.

            if chr( input ) == 'V':
                autopilot.inp.interval += .1
            if chr( input ) == 'v':
                autopilot.inp.interval -= .1

            if chr( input ) == 'W':
                timewarp       += .1
            if chr( input ) == 'w':
                timewarp       -= .1

            if chr( input ) == 'j':
                goal	        = max(    0, goal - 1. )
            if chr( input ) == 'k':
                goal	        = min( rows, goal + 1. )

            # Adjust Kp
            if chr( input) == 'P':
                autopilot.Kpid	= ( autopilot.Kpid[0] + .1, autopilot.Kpid[1], autopilot.Kpid[2] )
            if chr( input) == 'p':
                autopilot.Kpid	= ( autopilot.Kpid[0] - .1, autopilot.Kpid[1], autopilot.Kpid[2] )

            # Adjust Ki
            if chr( input) == 'I':
                autopilot.Kpid	= ( autopilot.Kpid[0], autopilot.Kpid[1] + .1, autopilot.Kpid[2] )
            if chr( input) == 'i':
                autopilot.Kpid	= ( autopilot.Kpid[0], autopilot.Kpid[1] - .1, autopilot.Kpid[2] )

            # Adjust Kd
            if chr( input) == 'D':
                autopilot.Kpid	= ( autopilot.Kpid[0], autopilot.Kpid[1], autopilot.Kpid[2] + .1 )
            if chr( input) == 'd':
                autopilot.Kpid	= ( autopilot.Kpid[0], autopilot.Kpid[1], autopilot.Kpid[2] - .1 )

            # Adjust Mass
            if chr( input) == 'M':
                mass	       += .1
            if chr( input) == 'm':
                mass	       -= .1

        
            
        dt			= now - autopilot.now			# last computed

        # Compute current altitude 'y', based on elapsed time 'dt' Compute acceleration f = ma,
        # a=f/m, including g.
        a			= g + thrust / mass

        # Compute ending velocity v = v0 + at
        dv			= a * dt
        v			= v0 + dv
        v_ave			= ( v0 + v ) / 2.

        # Clamp y to launch pad, and eliminate -'ve velocity at pad
        dy			= v_ave * dt
        y			= clamp( y0 + dy, Ly )
        if v < 0 and near( y, Ly[0]):
            v			= 0.

        # and compute actual displacement and hence actual net acceleration for period dt
        v_ave_act		= ( y - y0 ) / dt

        # we have an average velocity over the time period; we can deduce ending velocity, and
        # from that, the actual net acceleration experienced over the period by a = ( v - v0 ) / t
        v_act			= ( v_ave_act - v0 ) * 2.
        a_act			= ( v_act - v0 ) / dt

        # Frame of animation
        win.clear()
        message( win,
                 "T%+7.2f: ([P/p]: % 8.4f [I/i]: % 8.4f/% 8.4f [D/d]: %8.4f/% 8.4f)"
                   % ( now - start,
                       autopilot.Kpid[0],
                       autopilot.Kpid[1],
                       autopilot.I,
                       autopilot.Kpid[2],
                       autopilot.D ),
                 row = 1 )
        message( win,
                 "  f: % 7.2fkg.m/s^2 (raw:% 7.2f, min:% 7.2f, max:% 7.2f, mass % 7.2fkg [M/m])"
                 % ( thrust, autopilot.out, autopilot.Lout[0], autopilot.Lout[1], mass ),
                 row = 2 )
        message( win,
                 "  a: % 7.2fm/s^2    (flt:% 7.2f)"
                 % ( a, a_act ), 
                 row = 3 )
        message( win,
                 "  v: % 7.2fm/s      (flt:% 7.2f, ave:% 7.2f))"
                 % ( v, v_act, v_ave_act ),
                 row = 4 )
        message( win,
                 "  Y: % 7.2fm        (err:% 7.2f, goal:% 7.2f [k/j], setp:% 7.2f"
                 % ( y, autopilot.err, goal, autopilot.set.get() ),
                 row = 5 )

        # a0			= a_act
        a0			= a
        # v0			= v_act
        v0			= v
        y0			= y
        
        # Compute new thrust output for next time period based on current actual
        # altitude, and new goal setpoint.  

        thrust			= autopilot.loop( goal, y0, now )

        c			= rows - goal
        fc			= rows - autopilot.set.get()
        fi			= rows - autopilot.inp.get()
        r			= rows - y0

	if int(  c ) >= 0 and int(  c ) < rows:
            win.addstr( int( c )     , cols / 2-7, 'goal->' )
	if int( fc ) >= 0 and int( fc ) < rows:
            win.addstr( int( fc )    , cols / 2+1, '<-set' )
	if int( fi ) >= 0 and int( fi ) < rows:
            win.addstr( int( fi )    , cols / 2+1, '<-inp' )
	if int(  r)  >= 2 and int(  r ) < rows + 2:
	    win.addstr( int( r ) - 2 , cols / 2,   '^' ) # rocket
	if int(  r)  >= 1 and int(  r ) < rows + 1:
	    win.addstr( int( r ) - 1 , cols / 2,   '|' )
	if int(  r)  >= 0 and int(  r ) < rows:
	    win.addstr( int( r )     , cols / 2,   ";'`^!."[ int( now * 97 ) % 6 ] )



if __name__=='__main__':
    import curses, traceback
    try:        # Initialize curses
        stdscr=curses.initscr()
        curses.noecho() ; curses.cbreak(); curses.halfdelay( 1 )
        stdscr.keypad(1)
        ui( stdscr, title="Rocket" )        # Enter the mainloop
        stdscr.keypad(0)
        curses.echo() ; curses.nocbreak()
        curses.endwin()                 # Terminate curses
    except:
        stdscr.keypad(0)
        curses.echo() ; curses.nocbreak()
        curses.endwin()
        traceback.print_exc()           # Print the exception

