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

class controller:
    def __init__( self, Pc, Ic, Imax, Imin, Dc, now = time.time() ):
        self. last		= now
        self.error_avg		= 0
        self.Pconst		= Pc
        self.Iconst		= Ic
        self.Imax		= Imax
        self.Imin		= Imin
        self.Dconst		= Dc
    
    def loop( self, target, current, now = time.time() ):
        error			= target - current

        P			= self.Pconst - error
        D			= self.Dconst * ( error - Dstate )
        Dstate			= error

        Istate		       += error
        if Istate > Imax:
            Istate		= Imax
        elif Istate < Imin:
            Istate		= Imin
            
        I			= Istate * Iconst

        return P + I + D
    
