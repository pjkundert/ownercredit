
 #!/usr/bin/env python

"""
Implements tests for the pid module.
"""

__author__ 				= "Perry Kundert (perry@kundert.ca)"
__version__ 				= "$Revision: 1.2 $"
__date__ 				= "$Date: 2006/05/10 16:51:11 $"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "GNU General Public License, Version 3 (or later)"

# local modules
import pid
from misc import *

# pid.pid	-- Basic test, no filtering.
def test_pid_pid():
    control		= pid.pid( Kpid = ( 2.0, 1.0, 2.0 ), now = 0. )

    assert near( control.loop( 1.0, 1.0, now = 1. ),   0.0000 )
    assert near( control.loop( 1.0, 1.0, now = 2. ),   0.0000 )
    assert near( control.loop( 1.0, 1.1, now = 3. ),  -0.5000 )
    assert near( control.loop( 1.0, 1.1, now = 4. ),  -0.4000 )
    assert near( control.loop( 1.0, 1.1, now = 5. ),  -0.5000 )
    assert near( control.loop( 1.0, 1.05,now = 6. ),  -0.3500 )
    assert near( control.loop( 1.0, 1.05,now = 7. ),  -0.5000 )
    assert near( control.loop( 1.0, 1.01,now = 8. ),  -0.3500 )
    assert near( control.loop( 1.0, 1.0, now = 9. ),  -0.3900 )
    assert near( control.loop( 1.0, 1.0, now =10. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =11. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =12. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =13. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =14. ),  -0.4100 )

# pid.controller -- Same test
def test_pid_controller():
    control		= pid.controller( Kpid = ( 2.0, 1.0, 2.0 ), now = 0. )

    assert near( control.loop( 1.0, 1.0, now = 1. ),   0.0000 )
    assert near( control.loop( 1.0, 1.0, now = 2. ),   0.0000 )
    assert near( control.loop( 1.0, 1.1, now = 3. ),  -0.5000 )
    assert near( control.loop( 1.0, 1.1, now = 4. ),  -0.4000 )
    assert near( control.loop( 1.0, 1.1, now = 5. ),  -0.5000 )
    assert near( control.loop( 1.0, 1.05,now = 6. ),  -0.3500 )
    assert near( control.loop( 1.0, 1.05,now = 7. ),  -0.5000 )
    assert near( control.loop( 1.0, 1.01,now = 8. ),  -0.3500 )
    assert near( control.loop( 1.0, 1.0, now = 9. ),  -0.3900 )
    assert near( control.loop( 1.0, 1.0, now =10. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =11. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =12. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =13. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =14. ),  -0.4100 )


# pid.controller -- Steady state
def test_pid_controller_steady():
    control		= pid.controller(
        			Kpid 	= ( 2.0, 1.0, 2.0 ),
                                setpoint=  1.0,
                                value	=  2.0,
                                output	=  5.0,
                                now	=  0. )

    assert near( control.Kp, 2.000 )
    assert near( control.Ki, 1.000 )
    assert near( control.Kd, 2.000 )
    assert near( control.P, -1.000 )
    assert near( control.I,  7.000 )

    assert near( control.loop( 1.0, 2.0, now = 0.1),   4.9000 )
    assert near( control.P, -1.000 ); assert near( control.I,  6.900 )
    assert near( control.loop( 1.0, 1.9, now = 0.2),   7.0100 )
    assert near( control.P, -0.900 ); assert near( control.I,  6.810 )
    assert near( control.loop( 1.0, 1.8, now = 0.3),   7.1300 )
    assert near( control.P, -0.800 ); assert near( control.I,  6.730 )
    assert near( control.loop( 1.0, 1.7, now = 0.4),   7.2600 )
    assert near( control.P, -0.700 ); assert near( control.I,  6.660 )
    assert near( control.loop( 1.0, 1.6, now = 0.5),   7.4000 )
    assert near( control.P, -0.600 ); assert near( control.I,  6.600 )
    assert near( control.loop( 1.0, 1.4, now = 0.6),   9.7600 )
    assert near( control.P, -0.400 ); assert near( control.I,  6.560 )
    assert near( control.loop( 1.0, 1.5, now = 0.7),   3.5100 )
    assert near( control.P, -0.500 ); assert near( control.I,  6.510 )
    assert near( control.loop( 1.0, 1.3, now = 0.8),   9.8800 )
    assert near( control.P, -0.300 ); assert near( control.I,  6.480 )
    assert near( control.loop( 1.0, 1.1, now = 0.9),  10.2700 )
    assert near( control.loop( 1.0, 0.9, now = 0.95), 14.6750 )
    assert near( control.loop( 1.0, 1.1, now = 0.98), -7.0613 )
    assert near( control.loop( 1.0, 1.0, now = 1. ),  16.4720 )
    assert near( control.loop( 1.0, 1.0, now = 2. ),   6.4720 )
    assert near( control.loop( 1.0, 1.1, now = 3. ),   5.9720 )
    assert near( control.loop( 1.0, 1.1, now = 4. ),   6.0720 )
    assert near( control.loop( 1.0, 1.1, now = 5. ),   5.9720 )
    assert near( control.loop( 1.0, 1.05,now = 6. ),   6.1220 )
    assert near( control.loop( 1.0, 1.05,now = 7. ),   4.5000 )
    assert near( control.loop( 1.0, 1.01,now = 8. ),  -0.3500 )
    assert near( control.loop( 1.0, 1.0, now = 9. ),  -0.3900 )
    assert near( control.loop( 1.0, 1.0, now =10. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =11. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =12. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =13. ),  -0.4100 )
    assert near( control.loop( 1.0, 1.0, now =14. ),  -0.4100 )
