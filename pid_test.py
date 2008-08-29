
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

def test_controller():
    control		= pid.controller( 1.0, 1,0, ( 0.1, 0.1, 0.1 ), now = 0 )

    assert near( control.loop( 1.0,  1 ),   0.0000 )
    assert near( control.loop( 1.0,  2 ),   0.0000 )
    assert near( control.loop( 1.1,  3 ),  -0.0300 )
    assert near( control.loop( 1.1,  4 ),  -0.0300 )
    assert near( control.loop( 1.1,  5 ),  -0.0400 )
    assert near( control.loop( 1.05, 6 ),  -0.0350 )
    assert near( control.loop( 1.05, 7 ),  -0.0450 )
    assert near( control.loop( 1.01, 8 ),  -0.0380 )
    assert near( control.loop( 1.0,  9 ),  -0.0400 )
    assert near( control.loop( 1.0, 10 ),  -0.0410 )
    assert near( control.loop( 1.0, 11 ),  -0.0410 )
    assert near( control.loop( 1.0, 12 ),  -0.0410 )
    assert near( control.loop( 1.0, 13 ),  -0.0410 )
    assert near( control.loop( 1.0, 14 ),  -0.0410 )


    
