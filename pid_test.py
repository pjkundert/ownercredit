
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


    
