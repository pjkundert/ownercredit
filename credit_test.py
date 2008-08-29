#!/usr/bin/env python

"""
Implements tests for the credit module.
"""

__author__ 				= "Perry Kundert (perry@kundert.ca)"
__version__ 				= "$Revision: 1.2 $"
__date__ 				= "$Date: 2006/05/10 16:51:11 $"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "GNU General Public License, Version 3 (or later)"

# local modules
import credit
from misc import near

def test_near():
    assert     near( 0.5, 0.500001 )
    assert     near( 0.5, 0.50001 )
    assert not near( 0.5, 0.5001 )

    assert     near( 100.5, 100.51 )
    assert not near( 100.5, 100.51, 1.0e-5 )
    assert     near( 100.5, 100.501, 1.0e-5 )


def test_money_create_1():
    commodities				= {
        # Commodity	Units	 -of-	Quality	  -at-	Market
        "beer":		( "355ml",	"Pilsener",	"7-11"	    ),
        "bullets":	( "9mm",	"Springfield",	"Walmart"   ),
        "gas":		( "1l", 	"Unleaded"	"Esso"	    ),
        }

    basket				= {
        # Commodity	Price	
        "gas":		  1.00 /   1,	# BUX1.00
        "beer":		  6.00 /  12,	# BUX0.50
        "bullets":	 25.00 / 100,	# BUX0.25
        }

    # BUX, or &, are computed based on a the given commodities back,
    # over a rolling average over 5 units of time, beginning at 0.
    
    buck				= credit.currency( '&', 'BUX', commodities, basket, 0.5, 2.0, 5, 0 )

    assert buck.window == 5
    assert near( buck.reference['beer'], 0.5 )
    assert buck.now()			== 0
    assert near( buck.val(),		1.00 )
    assert near( buck.avg(),		1.00 )
    assert near( buck.K(), 		0.5 )

    
    # If beer falls in price, and gas rises by the same percentage...
    # Since beer has 1/2 the weighting in BUX as gas, net inflation
    # has occured.
    buck.update( {
        'gas': 		1.10 /  1,
        'beer':		5.40 / 12,
        }, 3 )

    assert near( buck.price['gas'],	1.10 )
    assert near( buck.price['beer'],	0.45 )

    # The & has inflated -- the price of the commodities backing it have gone up.  

    assert buck.now()		== 3
    assert near( buck.val(),		0.9722 )
    assert near( buck.avg(),		0.9833 )
    assert near( buck.K(), 		0.4778 )    

    # Same prices next time unit!   Inflation staying...
    ela = float( 4 ) - buck.now()
    assert near( ela, 			1 )
    rpl = ela / buck.window
    assert near( rpl, 			1.0/5.0 )
    avg = max( 0.0, 1.0 - rpl ) * buck.val()
    assert near( avg,			0.9722 * 4.0 / 5.0 )
    val = sum( buck.reference.values() ) / sum( buck.price.values() )
    assert near( val,			0.9722 )
    avg += min( 1.0, rpl ) * val
    assert near( avg, 0.9722 )
    buck.update( { }, 4 )
    assert buck.now()		== 4
    assert near( buck.val(),		0.9722 )
    assert near( buck.avg(),		0.9811 )
    assert near( buck.K(), 		0.4600 )    

    # Things go back to normal!  K should stay fixed, because it apparently
    # set things right...
    buck.update( {
        'gas': 		0.99 /  1,
        'beer':		6.12 / 12,
        }, 5 )

    assert near( buck.val(), 		1.00 )
    assert near( buck.avg(), 		0.9849 )
    assert near( buck.K(), 		0.4902 )    
