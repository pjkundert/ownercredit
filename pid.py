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
                  set		= 0.0,		# Target setpoint
                  inp		= 0.0,		# Estimated initial value (to avoid huge initial acceleration term!)
                  Kpid 		= ( 0.1, 0.1, 0.1 ),
                  Li		= ( 0.0, 0.0 ),
                  Lout		= ( 0.0, 0.0 ),
                  now		= time.time() ):

	self.set		= float( set )

        self.Kpid		= Kpid
        self.Li			= Li		# Integral anti-wind-up (eg. output saturated, doesn't reduce error term)
        self.Lout		= Lout		# Output limiting (eg. output saturated)

        self.last		= float( now )	# Last time computed
        self.err		= 0.		#   with this error term
	self.I			= 0.		#   and integral of error over time
        self.D			= set - inp	# Remember for dt == 0. case...


    def loop( self, inp, now = time.time() ):
        dt			= float( now ) - self.last
        err			= self.set - inp

        if dt > 0:
            # New error term only contributes to integral if time has elapsed!
            # Avoid integral wind-up
            self.I		= clamp( self.I + err * dt, self.Li )
            self.D		= ( err - self.err ) / dt
            self.err		= err
            self.last		= now
        
        return clamp(      err * self.Kpid[0]
                      + self.I * self.Kpid[1]
                      + self.D * self.Kpid[2], self.Lout )


if __name__ == "__main__":
    # Run a little rocket up to 10m, and then station-keep

    g				= -9.8					# m/s^2
    goal			= 10.					# m

    Kpid			= ( .1, .1, .1 )			# PID loop tuning
    Lout			= ( 0.0, 3.0 )				# 3 kg m/s^2 of thrust available
    Li				= ( 0.0, 0.0 )				# error integral limits
    Ly				= ( 0.1, 0.0 )				# Lauch pad height
    

    m0				= 1.					# kg
    a0				= 0.0
    v0				= 0.0
    y0				= Ly[0]
    thrust			= 0.0

    autopilot			= controller( goal, y0, Kpid, Lout, Li )
    start			= autopilot.last

    while 1:
        now			= time.time()
        dt			= now - autopilot.last			# last computed

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
        v_act			= ( v_ave_act - v ) * 2.
        a_act			= ( v_act - v0 ) / dt

        print( "T + %8.4f: (P: % 7.2f I: % 7.2f/% 7.2f D: %7.2f/% 7.2f) Thrust: % 7.2f: a: % 7.2f m/s^2 -> v: % 7.2f m/s -> Y: % 7.2fm |%sx%s\n"
                       % ( now - start,
                           autopilot.Kpid[0],
                           autopilot.Kpid[1],
                           autopilot.I,
                           autopilot.Kpid[2],
                           autopilot.D,
                           thrust, a_act, v_act, y_act, '', '' ), )

        a0			= a_act
        v0			= v_act
        y0			= y_act

        # Compute new thrust based on current actual altitude
        thrust			= autopilot.loop( y0, now )
        time.sleep( 0.10 )
