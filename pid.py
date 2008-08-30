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
                  Li		= ( 0.0, 0.0 ),
                  Lout		= ( 0.0, 0.0 ),
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

if __name__ == "__main__":
    # Run a little rocket up to 100km, and then station-keep

    g				= -9.81					# m/s^2
    mass			= 1.					# kg
    goal			= 25.					# m
    countdown			= 1.					# s to launch
    deadline			= 10.					# s to goal
    platform			= 0.1					# m, height of launch pad

    Kpid			= ( 1.0, 0.5, 0.1 )			# PID loop tuning
    Lout			= ( 0.0, 0.0 )				# 3 kg m/s^2 of thrust available
    Li				= ( 0.0, 0.0 )				# error integral limits
    Ly				= ( platform, 0.0 )			# Lauch pad height


    m0				= mass
    a0				= 0.0
    v0				= 0.0
    y0				= Ly[0]
    thrust			= 0.0					# N (kg.m/s^s)

    target			= platform
    autopilot			= controller( target, Kpid, Lout, Li )
    start			= autopilot.now

    liftoff			= start + countdown
    while 1:
        time.sleep( 0.10 )
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

        print( "T + %5.2f: (P: % 7.2f I: % 7.2f/% 7.2f D: %7.2f/% 7.2f) Thrust: % 7.2fkg.m/s^s: a: % 7.2f (raw:% 7.2f)m/s^2 -> v: % 7.2f (raw:% 7.2f, ave:% 7.2f))m/s -> Y: % 7.2fm (err: % 7.2f, tar:% 7.2f) |%s\n"
                       % ( now - start,
                           autopilot.Kpid[0],
                           autopilot.Kpid[1],
                           autopilot.I,
                           autopilot.Kpid[2],
                           autopilot.D,
                           thrust,
                           a_act, a,
                           v_act, v, v_ave_act,
                           y_act, autopilot.err, target,
                           '.' * int( y_act * 10 / goal ) + '>' + '.' * max( 0, int( ( goal - y_act ) * 10 / goal ))), )

        a0			= a_act
        v0			= v_act
        y0			= y_act

        # Compute new thrust based on current actual altitude, and new target setpoint
        if now > liftoff:
            target		= updown( platform, goal, deadline, now - liftoff )

        autopilot.setpoint	= target
        thrust			= autopilot.loop( y0, now )
