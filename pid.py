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
                  set		= 0,
                  Kpid 		= ( 0., 0., 0. ),
                  Li		= ( 0., 0. ),
                  Lout		= ( 0., 0. ),
                  now		= time.time() ):

	self.set		= set

        self.Kpid		= Kpid
        self.Li			= Li		# Integral anti-wind-up (eg. output saturated, doesn't reduce error term)
        self.Lout		= Lout		# Output limiting (eg. output saturated)

        self.last		= now		# Last time computed
        self.err		= 0.		#   with this error term
	self.I			= 0.		#   and integral of error over time
        self.D			= 0.		# Remember for dt == 0. case...


    def loop( self, inp, now = time.time() ):
        dt			= now - self.last
        err			= self.set - inp

        if dt:
            # New error term only contributes to integral if time has elapsed!
            # Avoid integral wind-up
            self.I		= clamp( self.I + err * dt, self.Li )
            self.D		= ( err - self.err ) / dt
            self.err		= err
            self.last		= now
        
        return clamp(      err * self.Kpid[0]
                      + self.I * self.Kpid[1]
                      + self.D * self.Kpid[2], self.Lout )
