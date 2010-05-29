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

# 
# pid.pid	-- Basic test, no filtering.
# 
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


# 
# pid.controller -- Same test
# 
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

# 
# pid.controller -- Steady state
# 
def test_pid_controller_steady():
    control		= pid.controller(
        			Kpid 	= ( 2.0, 1.0, 2.0 ),
                                setpoint=  1.0,
                                process	=  2.0,
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
    assert near( control.loop( 1.0, 1.05,now = 7. ),   5.9720 )
    assert near( control.loop( 1.0, 1.01,now = 8. ),   6.1220 )
    assert near( control.loop( 1.0, 1.0, now = 9. ),   6.0820 )
    assert near( control.loop( 1.0, 1.0, now =10. ),   6.0620 )
    assert near( control.loop( 1.0, 1.0, now =11. ),   6.0620 )
    assert near( control.loop( 1.0, 1.0, now =12. ),   6.0620 )
    assert near( control.loop( 1.0, 1.0, now =13. ),   6.0620 )
    assert near( control.loop( 1.0, 1.0, now =14. ),   6.0620 )


# 
# pid.controller -- Initial integral computation
# 
def test_pid_controller_integral():
    control		= pid.controller(
        			Kpid 	= ( 2.0, 1.0, 2.0 ),
                                setpoint=  1.0,
                                process	=  1.0,
                                output	= 10.0,
                                now	=  0. )

    assert near( control.Kp, 2.000 )
    assert near( control.Ki, 1.000 )
    assert near( control.Kd, 2.000 )
    assert near( control.P,  0.000 )
    assert near( control.I, 10.000 )

    control		= pid.controller(
        			Kpid 	= ( 2.0, 3.0, 1.0 ),
                                setpoint=  1.0,
                                process	=  1.0,
                                output	= 10.0,
                                now	=  0. )

    assert near( control.Kp, 2.000 )
    assert near( control.Ki, 3.000 )
    assert near( control.Kd, 1.000 )
    assert near( control.P,  0.000 )
    assert near( control.I,  3.333 )

    assert near( control.loop( 1.0, 1.00, now = 1.0),  10.000 )
    assert near( control.loop( 1.0, 1.00, now = 2.0),  10.000 )
    assert near( control.loop( 1.0, 1.20, now = 2.1),   7.540 )
    assert near( control.loop( 1.0, 1.10, now = 2.2),  10.710 )
    assert near( control.loop( 1.0, 0.99, now = 2.3),  11.033 )
    assert near( control.loop( 1.0, 1.00, now = 2.4),   9.813 )
    assert near( control.loop( 1.0, 1.00, now = 2.5),   9.913 )
    assert near( control.loop( 1.0, 1.00, now = 2.6),   9.913 )

# 
# pid.controller -- Output limiting and Integral wind-up avoidance
# 
#     When we hit the max output, the PID Integral should cease to be in/decreased.  If the PID loop
# doesn't do this, it will "stick" to min/max output long after the setpoint/process error has been
# decreased.  Once the Integral has maxed out, the only things that can continue to increase the
# output is the Proportional and Derivative, but these are temporary; in fact, as the Derivative
# (rate-of-change of error) goes in the opposite direction after the PID loop had previously hit the
# output limit, then it will "over compensate" in the output term for the first loop.  If this turns
# out to be a significant issue, then we'll have to limit both I and D terms when output is clamped
# to limits.
# 
def test_pid_controller_integral():
    control		= pid.controller(
        			Kpid 	= ( 2.0, 3.0, 1.0 ),
                                setpoint=  1.0,
                                process	=  1.0,
                                output	= 10.0,
                                now	=  0. )

    assert near( control.Kp, 2.000 )
    assert near( control.Ki, 3.000 )
    assert near( control.Kd, 1.000 )
    assert near( control.P,  0.000 )
    assert near( control.I,  3.333 )

    assert near( control.P,  0.000 ); assert near( control.I,  3.3333 )
    assert near( control.loop( 1.0, 1.00, now = 1.0, Lout=(0.0, 100.0)),  10.000 )
    assert near( control.P,  0.000 ); assert near( control.I,  3.3333 )
    assert near( control.loop( 1.0, 1.00, now = 2.0, Lout=(0.0, 100.0)),  10.000 )
    assert near( control.P,  0.000 ); assert near( control.I,  3.3333 )
    assert near( control.loop( 1.0, 1.20, now = 2.1, Lout=(0.0, 100.0)),   7.540 )
    assert near( control.P, -0.200 ); assert near( control.I,  3.3133 )
    assert near( control.loop( 1.0, 2.00, now = 3.0, Lout=(0.0, 100.0)),   4.351 )
    assert near( control.P, -1.000 ); assert near( control.I,  2.4133 )
    assert near( control.loop( 1.0, 1.90, now = 4.0, Lout=(0.0, 100.0)),   2.840 )
    assert near( control.P, -0.900 ); assert near( control.I,  1.5133 )
    assert near( control.loop( 1.0, 1.75, now = 5.0, Lout=(0.0, 100.0)),   0.940 )
    assert near( control.P, -0.750 ); assert near( control.I,  0.7633 )
    assert near( control.loop( 1.0, 1.50, now = 6.0, Lout=(0.0, 100.0)),   0.040 )
    assert near( control.P, -0.500 ); assert near( control.I,  0.26333 )
    assert near( control.loop( 1.0, 1.25, now = 7.0, Lout=(0.0, 100.0)),   0.000 ) # Clamped!
    assert near( control.P, -0.250 ); assert near( control.I,  0.26333 )
    assert near( control.loop( 1.0, 1.20, now = 7.2, Lout=(0.0, 100.0)),   0.520 )
    assert near( control.P, -0.200 ); assert near( control.I,  0.22333 )
    assert near( control.loop( 1.0, 1.20, now = 7.4, Lout=(0.0, 100.0)),   0.150 )
    assert near( control.P, -0.200 ); assert near( control.I,  0.18333 )
    assert near( control.loop( 1.0, 1.20, now = 7.6, Lout=(0.0, 100.0)),   0.030 )
    assert near( control.P, -0.200 ); assert near( control.I,  0.14333 )
    assert near( control.loop( 1.0, 1.20, now = 7.8, Lout=(0.0, 100.0)),   0.000 ) # Clamped!
    assert near( control.P, -0.200 ); assert near( control.I,  0.14333 )
    # Even increasing error doesn't change things (except P, of course)!
    assert near( control.loop( 1.0, 1.25, now = 8.0, Lout=(0.0, 100.0)),   0.000 ) # Clamped!
    assert near( control.P, -0.250 ); assert near( control.I,  0.14333 )
    # ...but the changed P will result in a larger Derivative when error reduced...
    assert near( control.loop( 1.0, 1.20, now = 8.2, Lout=(0.0, 100.0)),   0.160 )
    assert near( control.P, -0.200 ); assert near( control.I,  0.10333 )
    # Here's an example
    assert near( control.loop( 1.0, 1.20, now = 8.4, Lout=(0.0, 100.0)),   0.000 ) # Clamped!
    assert near( control.P, -0.200 ); assert near( control.I,  0.10333 )
    assert near( control.loop( 1.0, 1.30, now = 8.6, Lout=(0.0, 100.0)),   0.000 ) # Clamped!
    assert near( control.P, -0.300 ); assert near( control.I,  0.10333 )
    # ...so the changed P resulted in a larger Derivative when error reduced...
    assert near( control.loop( 1.0, 1.20, now = 8.8, Lout=(0.0, 100.0)),   0.290 ) # Clamped!
    assert near( control.P, -0.200 ); assert near( control.I,  0.06333 )

