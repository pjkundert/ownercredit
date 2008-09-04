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

class controller:
    def __init__( self,
                  setpoint	= 0.0,		# Target setpoint
                  Kpid 		= ( 0.1, 0.1, 0.1 ),
                  Li		= ( False, False ),
                  Lout		= ( False, False ),
                  now		= time.time() ):

	self.setpoint		= setpoint

        self.Kpid		= Kpid
        self.Li			= Li		# Integral anti-wind-up (eg. output saturated, doesn't reduce error term)
        self.Lout		= Lout		# Output limiting (eg. output saturated)

        self.now		= now		# Last time computed
        self.err		= 0.		#   with this error term
	self.I			= 0.		#   and integral of error over time
        self.D			= 0.		# Remember for dt == 0. case...

        self.err		= 0.		# Assume we are at setpoint

    def loop( self, inp, now = time.time() ):
        dt			= now - self.now
        err			= self.setpoint - inp

        if dt > 0:
            # New error term only contributes to integral if time has elapsed!
            # Avoid integral wind-up
            self.I		= clamp( self.I + err * dt, self.Li )
            self.D		= ( err - self.err ) / dt
            self.err		= err
            self.now		= now
        
        return clamp(      err * self.Kpid[0]
                      + self.I * self.Kpid[1]
                      + self.D * self.Kpid[2], self.Lout )

def message( window, text, row = 23 ):
    window.move( row, 0 )
    window.clrtoeol()
    window.addstr( row, 5, text )

def ui( win, title = "Test" ):
    # Run a little rocket up to 25m, and then station-keep

    g				= -9.81					# m/s^2
    mass			= 1.					# kg
    goal			= 25.					# m
    ceiling			= 35.
    countdown			= 1.					# s to launch
    duration			= 5.					# s to goal
    platform			= 0.1					# m, height of launch pad

    Kpid			= ( 3.0, 1.0, 0.5 )			# PID loop tuning
    Lout			= ( 0.0, False )			# No negative thrust available
    Li				= ( False, False ) 			# error integral limits; avoiding integral loading causes uncorrected error?
    Ly				= ( platform, False )			# Lauch pad height


    m0				= mass
    a0				= 0.0
    v0				= 0.0
    y0				= Ly[0]
    thrust			= 0.0					# N (kg.m/s^s)

    target			= platform
    autopilot			= controller( target, Kpid, Li, Lout )
    start			= autopilot.now

    liftoff			= start + countdown

    # Motion of target toward goal
    begin			= liftoff
    finish			= liftoff + duration
    while 1:
        message( win, "Quit (y/n)?", row = 0 )
        win.refresh()
        input			= win.getch()
        now			= time.time()
        if input > 0:
            if chr( input ) == 'y':
                break
            if chr( input ) == 'j':
                goal	        = max(       1, goal - 1. )
                if finish < now:
                    begin	= now
                    finish	= now + 2
            if chr( input ) == 'k':
                goal	        = min( ceiling, goal + 1. )
                if finish < now:
                    begin	= now
                    finish	= now + 2

        elapsed			= now - liftoff

        now			= time.time()
        dt			= now - autopilot.now			# last computed

        # Compute current altitude, based on elapsed time 'dt'
        # Compute acceleration f = ma, a=f/m
        a			= g + thrust / m0

        # Compute ending velocity v = v0 + at
        v			= v0 + a * dt
        v_ave			= ( v0 + v ) / 2.

        y_delta			= v_ave * dt

        # Clamp y to launch pad, and compute actual displacement and hence actual net acceleration
        # for period dt
        y_act			= clamp( y0 + y_delta, Ly )

        # v_ave = y_delta / t
        v_ave_act		= ( y_act - y0 ) / dt

        # we have an average velocity over the time period; we can deduce ending velocity, and
        # from that, the actual net acceleration experienced over the period by a = ( v - v0 ) / t
        v_act			= ( v_ave_act - v0 ) * 2.
        a_act			= ( v_act - v0 ) / dt

        # Frame of animation
        win.clear()
        rows, cols		= win.getmaxyx()
        message( win,
                 "T%+7.2f: (P: % 8.4f I: % 8.4f/% 8.4f D: %8.4f/% 8.4f)"
                   % ( now - start,
                       autopilot.Kpid[0],
                       autopilot.Kpid[1],
                       autopilot.I,
                       autopilot.Kpid[2],
                       autopilot.D ),
                 row = 1 )
        message( win,
                 "  f: % 7.2fkg.m/s^s"
                 % ( thrust ),
                 row = 2 )
        message( win,
                 "  a: % 7.2fm/s^2 (raw:% 7.2f)"
                 % ( a_act, a ), 
                 row = 3 )
        message( win,
                 "  v: % 7.2fm/s   (raw:% 7.2f, ave:% 7.2f))"
                 % ( v_act, v, v_ave_act ),
                 row = 4 )
        message( win,
                 "  Y: % 7.2fm     (err: % 7.2f, tar:% 7.2f, goal:% 7.2f)"
                 % ( y_act, autopilot.err, target, goal ),
                 row = 5 )

        a0			= a_act
        v0			= v_act
        y0			= y_act

        # Compute new target and compute thrust output for next time
        # period based on current actual altitude, and new target
        # setpoint.  We'll compute target based on a smooth up-down between
        # the current position and the goal, instead of the original position and the
        # goal, so we can move the goal
        
        target			= updown( y0, goal, begin, finish, now )

        r			= rows - rows * y0     / ceiling
        x			= rows - rows * goal   / ceiling
        c			= rows - rows * target / ceiling

        message( win, "  goal:% 7.2f, target:% 7.2f, row:% 7.2f" % ( goal, target, r ),
                 row = 6 )

        if x >= 0:
            win.addstr( int( x )     , cols / 2, 'x' ) # goal
	if c >= 0:
            win.addstr( int( c )     , cols / 2, '.' ) # carrot
	if r >= 2:
	    win.addstr( int( r ) - 2 , cols / 2, '^' ) # rocket
	    win.addstr( int( r ) - 1 , cols / 2, '|' )
	    win.addstr( int( r )     , cols / 2, ";'`^!.()"[ int( time.time() * 100 ) % 8 ] )

        autopilot.setpoint	= target
        thrust			= autopilot.loop( y0, now )


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

