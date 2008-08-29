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


def near( a, b, significance = 1.0e-4 ):

    """ Returns True iff the difference between the values is within the factor 'significance' of
    one of the original values.  Default is to within 4 decimal places. """

    return abs( a - b ) <= significance * ( a and a or b )

def test_controller():
    control		= pid.controller( 20.0, 0.5, 100, -100, 0.0, 0 )

    assert near( control.loop( 5.0, 5.0 ),   0.0 )
    assert near( control.loop( 5.0, 0.0 ),  20.0 )
    
    for x in range( 1, 10 ):
        pass
