#!/usr/bin/env python

"""
pid.controller	-- PID loop controller

    Implements a PID loop controller.  Controls a variable based on its velocity and acceleration
away from a steady state (0 velocity, 0 acceleration).

"""

__author__ 			= "Perry Kundert (perry.kundert@enbridge.com)"
__version__ 			= "$Revision: 1.2 $"
__date__ 			= "$Date: 2006/05/10 16:51:11 $"
__copyright__			= "Copyright (c) 2008 Perry Kundert"
__license__			= "GNU General Public License V3 (or higher)"

import time
from misc import *



# 
# pid.pid	-- Collect error and adjust output to compensate
# 
class pid:
    """
    Modulates output based on error between current value and desired setpoint.

    PID contants are provided in Kpid = ( Kp, Ki, Kd ), and specify what proportion of each
    error component should be fed back into computing the output.

        Kp -- amount of latest error should be fed back into output
        Ki -- amount of total error integral (sum of errors) should be fed back into output
        Kd -- amount of the last error derivative (rate of change) to included in output

    Depending on the relationship between the setpoint/value and the output, these factors
    will need to be tuned 
    
    The setpoint and input can optionally be filtered (averaged) over a time period, by providing
    non-zero Finp/Fset.
    
    """
    def __init__( self,
                  Kpid 		= ( 1.0, 1.0, 1.0 ),			# PID loop constants
                  Fset		= 0.0,					# Filter setpoint over this interval
                  Finp		= 0.0,					# Filter input over this interval
                  Li		= ( math.nan, math.nan ),		# Limit integral (anti-windup)
                  Lout		= ( math.nan, math.nan ),		# Limit output (anti-saturation)
                  now		= time.time() ):

	self.set		= filter( Fset, now )
        self.inp		= filter( Finp, now )
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
              setpoint,				# Current setpoint
              input,				# Current value
              now 		= time.time() ):
        dt			= now - self.now
        if dt > 0:

            # New input, setpoint and error term only contribute if time has elapsed!  Get the
            # filtered value.
            inp			= self.inp.add( input,    now )
            set			= self.set.add( setpoint, now )
            err			= set - inp

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
    goal			= platform + rows / 2.			# m


    Finp			= 0.					# Filter input?
    Fset			= 1.0					#   or setpoint?

    Kpid			= (    2.0,      0.1,      1.0   )	# PID loop tuning
    Lout			= ( math.nan, math.nan )		# No -'vethrust available, limit +'ve? Causes integral wind-up and overshoot
    #Lout			= (    0.0,     50.0   )
    #Lout			= (    0.0,   math.nan )
    #Lout			= (    0.0,    100.0   )
    Li				= ( math.nan, math.nan )
    #Li				= (    0.0,    100.0   ) 		# error integral limits; avoiding integral loading causes uncorrected error?
    Ly				= ( math.nan, math.nan )		# Lauch pad height
    #Ly				= ( platform, math.nan )		# Lauch pad height


    a0				= 0.0
    v0				= 0.0
    y0				= platform
    thrust			= 0.0					# N (kg.m/s^2)

    now				= 0.0
    autopilot			= pid( Kpid, Fset, Finp, Li, Lout, now )
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
                 "  Y: % 7.2fm        (err:% 7.2f, goal:% 7.2f [k/j])"
                 % ( y, autopilot.err, goal ),
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
            win.addstr( int( fc )     , cols / 2+1, '<-set' )
	if int( fi ) >= 0 and int( fi ) < rows:
            win.addstr( int( fi )     , cols / 2+1, '<-inp' )
	if int(  r)  >= 2 and int(  r ) < rows + 2:
	    win.addstr( int( r ) - 2 , cols / 2,   '^' ) # rocket
	if int(  r)  >= 1 and int(  r ) < rows + 1:
	    win.addstr( int( r ) - 1 , cols / 2,   '|' )
	if int(  r)  >= 0 and int(  r ) < rows:
	    win.addstr( int( r )     , cols / 2,   ";'`^!."[ int( now * 100 ) % 6 ] )



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

