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

class controller:
    def __init__( self, setpoint, Pc, Ic, Dc,
    		   Imax = 0., Imin = 0., now = time.time() ):
	self.setpoint		= setpoint

        self.Pconst		= Pc
        self.Iconst		= Ic
        self.Imax		= Imax		# Integral wind-up avoidance (when output
        self.Imin		= Imin		# doesn't reduce error term, eg. saturated motor drives, etc.)
        self.Dconst		= Dc

        self.Dstate		= 0.
        self.Istate		= 0.

        self.last		= now
	
	        
    def loop( self, in, now = time.time() ):

        dt			= now - self.last
	if not dt:
	   return 
        er			= self.setpoint - in

        P			= self.Pconst - er
        D			= self.Dconst * ( error - self.Dstate )
        Dstate			= error

        self.Istate	       += error
        if self.Istate > self.Imax:
            self.Istate		= self.Imax
        elif self.Istate < self.Imin:
            self.Istate		= self.Imin
            
        I			= self.Istate * self.Iconst

        return P + I + D
    
